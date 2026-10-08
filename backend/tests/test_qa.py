"""切片 2 · 问答编排层测试（D10 三档语义 + fail-open 降级）。

分支行为全部用假件锁：假检索器控制分数落点，假 LLM 记录调用。
拒答时绝不调 LLM —— 这是省 token 也是防幻觉的硬语义。
"""

import pytest

from app.rag.qa import LLMError, QAResult, answer
from app.rag.retriever import Retrieved

HIGH, LOW = 0.85, 0.65


def _hit(score, name="稻纵卷叶螟", content="【稻纵卷叶螟·症状】幼虫吐丝纵卷叶片"):
    return Retrieved("rice_leaf_roller", name, 2, content, score)


class FakeLLM:
    def __init__(self, text="幼虫吐丝纵卷叶片，可用药剂防治。", error=None):
        self.text = text
        self.error = error
        self.calls = []
        self.histories = []

    def __call__(self, query, hits, history=None):
        self.calls.append((query, hits))
        self.histories.append(history)
        if self.error:
            raise self.error
        return self.text


class FakeRetriever:
    def __init__(self, hits):
        self.hits = hits
        self.queries = []

    def __call__(self, query, top_k):
        self.queries.append(query)
        return self.hits


def test_below_low_threshold_refuses_without_calling_llm():
    llm = FakeLLM()
    result = answer("无关问题", FakeRetriever([_hit(0.4)]), llm, HIGH, LOW)
    assert result.mode == "refused"
    assert llm.calls == [], "低置信度拒答时不得调用 LLM"
    assert result.sources == [], "拒答不得伪造溯源"


def test_empty_hits_refuses():
    result = answer("无关问题", FakeRetriever([]), FakeLLM(), HIGH, LOW)
    assert result.mode == "refused"


def test_at_or_above_high_threshold_answers_confident():
    llm = FakeLLM("标准答案")
    hits = [_hit(0.9)]
    result = answer("怎么防治", FakeRetriever(hits), llm, HIGH, LOW)
    assert result.mode == "confident"
    assert result.answer == "标准答案"
    assert result.sources == hits


def test_between_thresholds_answers_with_caution_label():
    llm = FakeLLM("可能不对的答案")
    result = answer("怎么防治", FakeRetriever([_hit(0.7)]), llm, HIGH, LOW)
    assert result.mode == "caution"
    assert "仅供参考" in result.answer
    assert "可能不对的答案" in result.answer


def test_boundary_low_is_caution_not_refused():
    """拒答语义是 score < low；恰好等于低阈值仍作答（中间档）。"""
    result = answer("q", FakeRetriever([_hit(LOW)]), FakeLLM(), HIGH, LOW)
    assert result.mode == "caution"


def test_boundary_high_is_confident():
    result = answer("q", FakeRetriever([_hit(HIGH)]), FakeLLM(), HIGH, LOW)
    assert result.mode == "confident"


def test_llm_failure_falls_back_to_retrieved_content():
    """fail-open：断 LLM 返回检索原文，绝不静默丢弃或报 500。"""
    llm = FakeLLM(error=LLMError("api down"))
    hits = [_hit(0.9), _hit(0.8, name="稻纵卷叶螟", content="【稻纵卷叶螟·防治】释放赤眼蜂")]
    result = answer("怎么防治", FakeRetriever(hits), llm, HIGH, LOW)
    assert result.mode == "fallback"
    assert "【稻纵卷叶螟·症状】幼虫吐丝纵卷叶片" in result.answer
    assert "【稻纵卷叶螟·防治】释放赤眼蜂" in result.answer
    assert result.sources == hits


def test_fallback_also_works_in_caution_band():
    """中间档断 LLM 同样 fail-open —— 降级只看 LLM 死活，不看分数档。"""
    llm = FakeLLM(error=LLMError("timeout"))
    result = answer("q", FakeRetriever([_hit(0.7)]), llm, HIGH, LOW)
    assert result.mode == "fallback"


def test_result_is_qa_result_with_all_fields():
    result = answer("q", FakeRetriever([_hit(0.9)]), FakeLLM(), HIGH, LOW)
    assert isinstance(result, QAResult)
    assert result.answer and result.sources
