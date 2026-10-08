"""检索查询改写（Conversational Query Condense）。

改写只服务检索端：BGE 只看当前这句话的向量，历史与口语都不进它的视野。
改写器把「最近几轮对话 + 原问题」交给 LLM，换回一句独立、规范、可检索的查询。

两条红线（写进 prompt，由评测/测试把关）：
- 不得引入对话中未提及的具体虫名或新事实 —— 否则等于让改写模型用参数知识
  替检索押题，押错整条链路被带偏；改写只做表达层规范化与指代消解；
- 改写结果不进作答 —— 作答喂的是原问题 + 历史 + 检索语料，改写偏差最多
  影响「找得准不准」，不污染最终回答。

改写失败 fail-open：用原问题检索，宁可用没那么准的查询也不能不检索。
"""

from app.rag.llm import LLMError  # noqa: F401  （调用方捕获；在此导出便于组装方 import）

REWRITE_SYSTEM = (
    "你是检索查询改写器。把用户最新问题改写成一条独立、完整、贴近作物虫害图鉴"
    "语料用词的可检索查询：\n"
    "1. 补全对话中的指代与省略（历史里提到的作物、部位、害虫可以直接引用）；\n"
    "2. 将口语化症状描述规范化为专业表达；\n"
    "3. 严禁引入对话中未提及的具体虫名或任何新事实；\n"
    "4. 只输出改写后的查询本身，不要任何解释、引号或前缀。"
)


def _clean_output(raw: str) -> str:
    """LLM 输出清洗：取第一行非空文本，剥掉引号/反引号/围栏/中文引号残留。"""
    for line in (raw or "").splitlines():
        line = line.strip().strip('"').strip("`").strip("'")
        line = line.strip("「」『』《》").strip()
        if line:
            return line
    return ""


def make_rewriter(chat_raw):
    """组装改写器。chat_raw: (messages) -> str（DeepSeekClient.chat_raw 或测试假件）。"""

    def rewrite(query: str, history: list[dict] | None) -> str:
        lines = [f"用户：{t['q']}\n助手：{t['a'][:200]}" for t in (history or [])]
        prompt = "最近对话：\n" + "\n".join(lines) if lines else "（本轮为对话第一句）"
        prompt += f"\n\n用户最新问题：{query}\n\n请输出改写后的检索查询："
        raw = chat_raw(
            [
                {"role": "system", "content": REWRITE_SYSTEM},
                {"role": "user", "content": prompt},
            ]
        )
        return _clean_output(raw) or query  # 空输出视为改写失败，回退原问题

    return rewrite
