"""会话问答测试：短期记忆 + 低分澄清分支。

锁定的新语义（2026-10-08 用户拍板）：
- 低分（< low）不再直接拒答：先一次轻量 LLM 意图分类，相关 → 出选择题追问，
  无关 → 指引；已澄清一轮仍低分 → 零调用拒答（防无限循环）。
- 会话记忆存 Redis（FakeRedis 替身），带 session_id 续问时链路能拿到历史。
"""

import json

from fastapi.testclient import TestClient

from app.main import app
from app.modules.auth.deps import get_redis
from app.modules.rag.router import get_qa
from app.rag.qa import LLMError, QAResult, answer
from app.rag.retriever import Retrieved
from tests.test_auth_service import FakeRedis

HIGH, LOW = 0.85, 0.65


def _hit(score, name="稻纵卷叶螟", content="【稻纵卷叶螟·症状】幼虫吐丝纵卷叶片"):
    return Retrieved("rice_leaf_roller", name, 2, content, score)


class FakeRetriever:
    def __init__(self, hits):
        self.hits = hits

    def __call__(self, query, top_k):
        return self.hits


class FakeLLM:
    """带 chat_raw 的假 LLM：generate 记录 history；chat_raw 返回预设 JSON。"""

    def __init__(self, chat_payload="", chat_error=None, text="标准答案"):
        self.chat_payload = chat_payload
        self.chat_error = chat_error
        self.text = text
        self.chat_calls = []
        self.histories = []

    def __call__(self, query, hits, history=None):
        self.histories.append(history)
        return self.text

    def chat_raw(self, messages):
        self.chat_calls.append(messages)
        if self.chat_error:
            raise self.chat_error
        return self.chat_payload


_CLARIFY_JSON = json.dumps(
    {
        "kind": "clarify",
        "text": "为了帮您定位虫害，请补充信息：",
        "options": [
            {"q": "受害的是什么作物？", "choices": ["水稻", "小麦", "玉米"]},
            {"q": "叶片是否被卷成虫苞？", "choices": ["是", "否"]},
        ],
    },
    ensure_ascii=False,
)

_OFF_TOPIC_JSON = json.dumps(
    {"kind": "off_topic", "text": "我是作物虫害助手，请提问虫害相关症状，或在检测页上传照片。"},
    ensure_ascii=False,
)


# ---- 低分澄清分支 ----

def test_low_score_with_relevant_question_returns_clarify_options():
    llm = FakeLLM(chat_payload=_CLARIFY_JSON)
    result = answer("叶子有问题", FakeRetriever([_hit(0.4)]), llm, HIGH, LOW)
    assert result.mode == "clarify"
    assert len(result.options) == 2
    assert result.options[0]["choices"] == ["水稻", "小麦", "玉米"]
    assert llm.chat_calls, "低分相关题应触发一次澄清分类调用"


def test_low_score_off_topic_returns_guidance_without_options():
    llm = FakeLLM(chat_payload=_OFF_TOPIC_JSON)
    result = answer("今天天气怎么样", FakeRetriever([_hit(0.3)]), llm, HIGH, LOW)
    assert result.mode == "off_topic"
    assert result.options == []
    assert "检测" in result.answer


def test_clarify_twice_refuses_without_any_llm_call():
    """澄清过一轮（prev_mode=clarify）仍低分 → 零调用拒答，防无限循环。"""
    llm = FakeLLM(chat_payload=_CLARIFY_JSON)
    result = answer("还是不对", FakeRetriever([_hit(0.4)]), llm, HIGH, LOW, prev_mode="clarify")
    assert result.mode == "refused"
    assert llm.chat_calls == [], "循环守卫生效时不得再调用 LLM"


def test_clarify_llm_down_fails_closed():
    """澄清路径的降级方向与作答路径相反：fail-closed 拒答，不能猜。"""
    llm = FakeLLM(chat_error=LLMError("api down"))
    result = answer("叶子有问题", FakeRetriever([_hit(0.4)]), llm, HIGH, LOW)
    assert result.mode == "refused"


def test_clarify_malformed_json_falls_back_to_template_options():
    llm = FakeLLM(chat_payload="我觉得你说得对！")
    result = answer("叶子有问题", FakeRetriever([_hit(0.4)]), llm, HIGH, LOW)
    assert result.mode == "clarify"
    assert result.options, "JSON 解析失败兜底为固定诊断维度选择题"
    assert all("q" in o and "choices" in o for o in result.options)


def test_clarify_json_inside_code_fence_is_parsed():
    fenced = "```json\n" + _CLARIFY_JSON + "\n```"
    llm = FakeLLM(chat_payload=fenced)
    result = answer("叶子有问题", FakeRetriever([_hit(0.4)]), llm, HIGH, LOW)
    assert result.mode == "clarify"
    assert len(result.options) == 2


# ---- 会话记忆贯穿 ----

def test_history_reaches_the_generation_llm():
    llm = FakeLLM()
    history = [{"q": "叶子卷了", "mode": "clarify", "a": "请问是什么作物？"}]
    answer("是水稻", FakeRetriever([_hit(0.9)]), llm, HIGH, LOW, history=history)
    assert llm.histories[-1] == history, "作答 LLM 必须能拿到会话历史"


def test_router_session_persists_history_between_turns():
    """路由层：同 session_id 续问，第二次调用链路必须收到历史。"""
    store = FakeRedis()
    seen = []

    def fake_qa(query, history=None, prev_mode=None):
        seen.append((history, prev_mode))
        return QAResult(mode="confident", answer="x", sources=[])

    app.dependency_overrides[get_qa] = lambda: fake_qa
    app.dependency_overrides[get_redis] = lambda: store
    try:
        client = TestClient(app)
        r1 = client.post("/rag/ask", json={"question": "叶子卷了怎么办"})
        sid = r1.json()["session_id"]
        assert sid, "首次问答应下发 session_id"

        r2 = client.post("/rag/ask", json={"question": "那用什么药", "session_id": sid})
        assert r2.json()["session_id"] == sid

        first_history, first_prev = seen[0]
        second_history, second_prev = seen[1]
        assert first_history == [] and first_prev is None
        assert second_history, "第二轮必须拿到第一轮的历史"
        assert second_history[0]["q"] == "叶子卷了怎么办"
        assert second_prev == "confident"
    finally:
        app.dependency_overrides.clear()


def test_router_invalid_session_id_starts_fresh():
    """非法 session_id 不报错，按新会话处理。"""
    store = FakeRedis()
    app.dependency_overrides[get_qa] = lambda: lambda q, **kw: QAResult(
        mode="confident", answer="x", sources=[]
    )
    app.dependency_overrides[get_redis] = lambda: store
    try:
        client = TestClient(app)
        resp = client.post("/rag/ask", json={"question": "叶子卷了怎么办", "session_id": "!!bad!!"})
        assert resp.status_code == 200
        assert resp.json()["session_id"] != "!!bad!!"
    finally:
        app.dependency_overrides.clear()
