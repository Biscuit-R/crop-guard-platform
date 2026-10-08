"""query 改写测试：改写只喂检索器、fail-open 回退、输出清洗、prompt 红线。

红线（rewrite.py 模块注释）：不得引入对话未提及的虫名/新事实 —— 这条写进
prompt，这里断言 prompt 确实带了红线措辞，防日后改 prompt 时悄悄丢掉。
"""

from app.rag.qa import answer
from app.rag.rewrite import LLMError, REWRITE_SYSTEM, _clean_output, make_rewriter
from app.rag.retriever import Retrieved

HIGH, LOW = 0.85, 0.65


class FakeChatRaw:
    """可编程的 chat_raw 假件：记录 messages，按脚本返回或抛错。"""

    def __init__(self, reply="稻纵卷叶螟 防治方法", error=None):
        self.reply = reply
        self.error = error
        self.messages = []

    def __call__(self, messages):
        self.messages.append(messages)
        if self.error:
            raise self.error
        return self.reply


def _hit(score, name="稻纵卷叶螟", content="【稻纵卷叶螟·症状】幼虫吐丝纵卷叶片"):
    return Retrieved("rice_leaf_roller", name, 2, content, score)


class FakeRetriever:
    def __init__(self, hits):
        self.hits = hits
        self.queries = []

    def __call__(self, query, top_k):
        self.queries.append(query)
        return self.hits


class FakeLLM:
    def __init__(self):
        self.calls = []

    def __call__(self, query, hits, history=None):
        self.calls.append((query, hits))
        return "答案"


# ---- 改写器本体 ----

def test_rewrite_passes_history_and_question_in_prompt():
    chat = FakeChatRaw("稻纵卷叶螟防治")
    rewriter = make_rewriter(chat)
    history = [{"q": "水稻叶片卷起来了", "mode": "clarify", "a": "请补充更多信息"}]
    rewriter("怎么防治", history)
    user_msg = chat.messages[0][1]["content"]
    assert "水稻叶片卷起来了" in user_msg, "历史问题必须进 prompt"
    assert "怎么防治" in user_msg
    assert "稻纵卷叶螟防治" not in user_msg, "历史答案只截断参考，不直接注入查询"
    # 系统提示带红线措辞
    system_msg = chat.messages[0][0]["content"]
    assert "严禁引入" in system_msg and "未提及" in system_msg


def test_clean_output_strips_quotes_fences_and_takes_first_line():
    assert _clean_output('```稻纵卷叶螟 防治方法\n第二行') == "稻纵卷叶螟 防治方法"
    assert _clean_output('"稻纵卷叶螟"') == "稻纵卷叶螟"
    assert _clean_output("  \n\n稻纵卷叶螟\n") == "稻纵卷叶螟"
    assert _clean_output("") == ""
    assert _clean_output(None) == ""


def test_rewriter_empty_output_falls_back_to_query():
    rewriter = make_rewriter(FakeChatRaw(""))
    assert rewriter("原问题", []) == "原问题"


def test_rewriter_propagates_llm_error():
    """改写失败由调用方（qa.answer）fail-open，这里锁异常透传语义。"""
    rewriter = make_rewriter(FakeChatRaw(error=LLMError("api down")))
    try:
        rewriter("q", None)
        raise AssertionError("应当抛 LLMError")
    except LLMError:
        pass


# ---- answer 集成：改写只影响检索端 ----

def test_answer_feeds_rewritten_query_to_retriever():
    retr = FakeRetriever([_hit(0.9)])
    result = answer(
        "怎么防治", retr, FakeLLM(), HIGH, LOW,
        rewriter=make_rewriter(FakeChatRaw("稻纵卷叶螟 防治方法")),
    )
    assert retr.queries == ["稻纵卷叶螟 防治方法"], "检索器必须收到改写后的查询"
    assert result.search_query == "稻纵卷叶螟 防治方法"
    assert result.mode == "confident"


def test_answer_generating_still_uses_original_query():
    """红线落点：作答 LLM 看到的是原问题，不是改写结果。"""
    llm = FakeLLM()
    answer("怎么防治", FakeRetriever([_hit(0.9)]), llm, HIGH, LOW,
           rewriter=make_rewriter(FakeChatRaw("稻纵卷叶螟 防治方法")))
    assert llm.calls[0][0] == "怎么防治"


def test_answer_rewriter_error_falls_open_to_original_query():
    """改写失败 fail-open：用原问题检索，业务不中断。"""
    retr = FakeRetriever([_hit(0.9)])
    result = answer(
        "怎么防治", retr, FakeLLM(), HIGH, LOW,
        rewriter=make_rewriter(FakeChatRaw(error=LLMError("down"))),
    )
    assert retr.queries == ["怎么防治"]
    assert result.search_query == "怎么防治"
    assert result.mode == "confident"


def test_answer_without_rewriter_unchanged():
    """不传 rewriter 行为与改写切片之前完全一致（回归保护）。"""
    retr = FakeRetriever([_hit(0.7)])
    result = answer("怎么防治", retr, FakeLLM(), HIGH, LOW)
    assert retr.queries == ["怎么防治"]
    assert result.search_query == "怎么防治"
    assert result.mode == "caution"


def test_rewrite_system_contains_all_four_rules():
    """四条规则的措辞锚点：指代补全 / 口语规范化 / 引入红线 / 只输出查询。"""
    assert "指代" in REWRITE_SYSTEM
    assert "规范化" in REWRITE_SYSTEM
    assert "严禁引入" in REWRITE_SYSTEM
    assert "只输出" in REWRITE_SYSTEM
