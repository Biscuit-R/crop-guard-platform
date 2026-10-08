"""切片 2 · LLM 客户端测试。

值得测的是纯逻辑（prompt 组装）与错误映射（任何异常 → LLMError）；
openai SDK 本身不测 —— 那是别人的代码。
"""

import pytest

from app.rag.llm import LLMError, DeepSeekClient, build_messages
from app.rag.retriever import Retrieved


def _hit(content, chinese="稻纵卷叶螟"):
    return Retrieved("rice_leaf_roller", chinese, 2, content, 0.9)


def test_build_messages_includes_query_and_numbered_sources():
    hits = [_hit("【稻纵卷叶螟·症状】卷叶"), _hit("【二化螟·防治】诱捕", "二化螟")]
    messages = build_messages("叶子卷了怎么办", hits)
    system, user = messages[0], messages[1]
    assert system["role"] == "system"
    assert user["role"] == "user"
    assert "叶子卷了怎么办" in user["content"]
    assert "【资料1】" in user["content"] and "【资料2】" in user["content"]
    assert "【稻纵卷叶螟·症状】卷叶" in user["content"]


def test_build_messages_system_forbids_outside_knowledge():
    messages = build_messages("q", [_hit("资料")])
    system = messages[0]["content"]
    assert "只能依据" in system, "系统提示必须约束模型只用资料作答"
    assert "来源" in system, "系统提示必须要求溯源标注"


class _FakeOpenAI:
    """替身：替换 DeepSeekClient 内部的 SDK 客户端。"""

    def __init__(self, content="生成文本", error=None):
        self._content = content
        self._error = error
        self.kwargs = None

        class _Completions:
            def create(inner_self, **kwargs):
                if self._error:
                    raise self._error
                self.kwargs = kwargs
                return type("R", (), {"choices": [type("C", (), {"message": type("M", (), {"content": self._content})()})]})()

        self.chat = type("Chat", (), {"completions": _Completions()})()


def test_client_returns_generated_text():
    fake = _FakeOpenAI(content="生成的答案")
    client = DeepSeekClient(api_key="k", base_url="https://api.deepseek.com", model="deepseek-chat")
    client._client = fake
    hits = [_hit("资料内容")]
    assert client.generate("问题", hits) == "生成的答案"
    assert fake.kwargs["model"] == "deepseek-chat"
    assert fake.kwargs["messages"] == build_messages("问题", hits)


def test_client_wraps_any_error_into_llm_error():
    client = DeepSeekClient(api_key="k", base_url="https://api.deepseek.com")
    client._client = _FakeOpenAI(error=RuntimeError("connection refused"))
    with pytest.raises(LLMError):
        client.generate("q", [_hit("资料")])


def test_client_sets_explicit_timeout(monkeypatch):
    """SDK 默认 600s 会拖死请求 —— 必须显式传 timeout，让挂住转成 LLMError 走 fail-open。"""
    captured = {}

    class _FakeOpenAIClass:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr("app.rag.llm.OpenAI", _FakeOpenAIClass)
    DeepSeekClient(api_key="k", base_url="https://api.deepseek.com", timeout=30.0)
    assert captured["timeout"] == 30.0
