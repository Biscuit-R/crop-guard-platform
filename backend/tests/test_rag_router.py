"""切片 2 · RAG 路由接线测试。

端点本身要薄：组装真实链路的 get_qa 用 dependency_overrides 换掉，
锁的是「请求校验 → 调链路 → 返回 QAResult 字段」这一段接线。
"""

from fastapi.testclient import TestClient

from app.main import app
from app.modules.auth.deps import get_redis
from app.modules.rag.router import get_qa
from app.rag.qa import QAResult
from app.rag.retriever import Retrieved
from tests.test_auth_service import FakeRedis

client = TestClient(app)

_HIT = Retrieved("rice_leaf_roller", "稻纵卷叶螟", 2, "【稻纵卷叶螟·症状】卷叶", 0.9)


def test_ask_returns_qa_result_fields():
    # 会话记忆走 get_redis 依赖：必须换假件，否则测试隐式依赖本机 6380 的真 Redis
    #（Windows 本机有容器映射所以一直碰巧通过，CI 无 Redis 才暴露）
    app.dependency_overrides[get_redis] = lambda: FakeRedis()
    app.dependency_overrides[get_qa] = lambda: lambda q, **kw: QAResult(
        mode="confident", answer="测试答案", sources=[_HIT]
    )
    try:
        resp = client.post("/rag/ask", json={"question": "叶子卷了怎么办"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["mode"] == "confident"
        assert body["answer"] == "测试答案"
        assert body["sources"][0]["chinese_name"] == "稻纵卷叶螟"
        assert "session_id" in body, "响应必须带回会话 id，前端续问靠它"
    finally:
        app.dependency_overrides.clear()


def test_ask_rejects_too_short_question():
    app.dependency_overrides[get_qa] = lambda: lambda q, **kw: QAResult(mode="confident", answer="x", sources=[])
    try:
        resp = client.post("/rag/ask", json={"question": "卷"})
        assert resp.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_ask_without_key_fails_closed(monkeypatch):
    """key 未配置 = 配置层 fail-closed：组装链路时直接拒绝，不带病上线。"""
    from app.modules.rag import router as rag_router

    monkeypatch.setenv("DEEPSEEK_API_KEY", "")
    rag_router.get_settings.cache_clear()
    no_raise = TestClient(app, raise_server_exceptions=False)
    try:
        resp = no_raise.post("/rag/ask", json={"question": "叶子卷了怎么办"})
        assert resp.status_code == 500  # 配置缺失是部署错误，显式炸出来
    finally:
        rag_router.get_settings.cache_clear()
