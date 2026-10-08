"""问答编排（D10 三档语义 + 会话追问）。

分数三档：
  score >= high        → confident：正常作答 + 溯源
  low <= score < high  → caution ：作答 + 「仅供参考」标注
  score <  low         → 不直接作答。花一次轻量 LLM 调用判断意图：
                            与虫害诊断无关          → off_topic：指引用户
                            相关但信息不足          → clarify ：出选择题/判断题追问
                          已追问过一轮仍低分        → refused ：零调用拒答（防无限澄清循环）

低分档的语义演进（2026-10-08，用户拍板）：旧版「低分直接拒答」对相关但笼统的
问题体验差（用户只知道被拒，不知道怎么补信息）。澄清调用是轻量的意图分类 +
追问生成，不是检索增强作答 —— 省 token 的初衷保留：作答永远必须有检索分数背书。

降级只看 LLM 死活，不看分数档：作答路径 LLM 抛 LLMError → fail-open 返回检索原文
（原文可信，宁可不精美也不能有错误信息）；澄清路径 LLM 不可用 → fail-closed 拒答
（分不清意图时宁可拒答也不能猜）。
"""

import json
import re
from dataclasses import dataclass, field

from app.rag.llm import LLMError
from app.rag.retriever import Retrieved

REFUSAL = (
    "抱歉，图鉴语料中没有足够可信的内容回答这个问题。"
    "您可以换个说法补充症状细节（如虫体颜色、大小、为害部位），"
    "或前往「图鉴」页按名称 / 寄主植物查找，或在「检测」页上传照片识别。"
)

CAUTION_LABEL = "⚠️ 以下回答置信度有限，仅供参考：\n\n"

# 低分分支的意图分类 + 追问生成。只要求结构化 JSON，不给它任何图鉴资料 ——
# 追问的是诊断常识维度（作物/部位/颜色），不是答案本身。
CLARIFY_SYSTEM = (
    "你是作物虫害防治助手。用户的提问信息不足以在图鉴语料中定位虫害。"
    "请判断用户意图并只输出一个 JSON 对象，不要输出其他内容：\n"
    '1. 与作物虫害诊断无关（闲聊、天气、其他领域）→ {"kind":"off_topic","text":"<一句指引用语，'
    '建议用户提问虫害症状或使用检测/图鉴功能>"}\n'
    '2. 与虫害相关但信息不足 → {"kind":"clarify","text":"<一句承接语，表示需要补充信息>",'
    '"options":[{"q":"<追问问题>","choices":["<选项A>","<选项B>","<选项C>"]}]}，'
    "共 2 个追问，每个 3~4 个选项，其中一个追问用判断题形式（choices 为 [\"是\",\"否\"]）。"
    "只根据对话上下文设计追问，不要假设答案。"
)


@dataclass
class QAResult:
    mode: str  # confident | caution | refused | fallback | clarify | off_topic
    answer: str
    sources: list[Retrieved] = field(default_factory=list)
    # clarify 档的选择题：[{"q": "这是什么作物？", "choices": ["水稻", "小麦", ...]}]
    options: list[dict] = field(default_factory=list)
    # 实际用于检索的查询（经改写；与原问题不同时前端展示，调试/演示可见）
    search_query: str | None = None


def _parse_clarify_payload(text: str) -> tuple[str, str, list[dict]] | None:
    """从 LLM 输出里抠 JSON（容忍 ```json 围栏）。解析失败返回 None。"""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        payload = json.loads(match.group())
    except ValueError:
        return None
    kind = payload.get("kind")
    text_out = payload.get("text") or ""
    if kind not in ("off_topic", "clarify"):
        return None
    options = []
    if kind == "clarify":
        for item in payload.get("options") or []:
            if isinstance(item, dict) and item.get("q") and item.get("choices"):
                # LLM 自由生成的选项不限长，截断兜底防前端按钮被撑爆
                options.append(
                    {
                        "q": str(item["q"])[:50],
                        "choices": [str(c)[:20] for c in item["choices"] if str(c).strip()],
                    }
                )
        options = [o for o in options if o["choices"]]
        if not options:
            return None
    return kind, text_out, options


def _fallback_clarify() -> tuple[str, str, list[dict]]:
    """LLM 输出不合规范时的兜底：固定诊断维度选择题（比直接拒答体验好）。"""
    return "clarify", "为了帮您定位虫害，请补充几个信息：", [
        {"q": "受害的是什么作物？", "choices": ["水稻", "小麦", "玉米", "蔬菜", "果树", "其他"]},
        {"q": "叶片上是否能看到虫体或虫粪？", "choices": ["是", "否"]},
    ]


def answer(
    query: str,
    retrieve,
    llm,
    high: float,
    low: float,
    top_k: int = 3,
    history: list[dict] | None = None,
    prev_mode: str | None = None,
    rewriter=None,
) -> QAResult:
    """retrieve: (query, top_k) -> list[Retrieved]；llm: (query, hits, history=) -> str，
    且需提供 chat_raw(messages)（低分分支的意图分类用）；
    rewriter: (query, history) -> str（可选，检索查询改写，见 rewrite.py）。"""
    # 改写只喂检索器；作答仍用原问题（见 rewrite.py 模块注释）。
    # 改写失败 fail-open 回退原问题。
    search_query = query
    if rewriter is not None:
        try:
            search_query = rewriter(query, history) or query
        except LLMError:
            search_query = query

    hits = retrieve(search_query, top_k)
    top = hits[0].score if hits else 0.0

    if top >= low:
        try:
            text = llm(query, hits, history=history)
        except LLMError:
            raw = "\n\n".join(h.content for h in hits)
            return QAResult(mode="fallback", answer=raw, sources=hits, search_query=search_query)

        if top >= high:
            return QAResult(mode="confident", answer=text, sources=hits, search_query=search_query)
        return QAResult(mode="caution", answer=CAUTION_LABEL + text, sources=hits,
                        search_query=search_query)

    # ---- 低分分支：澄清一轮后仍低分 → 零调用拒答 ----
    if prev_mode == "clarify":
        return QAResult(mode="refused", answer=REFUSAL, sources=[], search_query=search_query)

    chat_raw = getattr(llm, "chat_raw", None)
    if chat_raw is None:
        # 假件/旧签名没有分类能力 → fail-closed 拒答（测试双件也走这里）
        return QAResult(mode="refused", answer=REFUSAL, sources=[], search_query=search_query)

    context_lines = [f"用户：{t['q']}\n助手：{t['a'][:200]}" for t in (history or [])]
    prompt = "最近对话：\n" + "\n".join(context_lines) + f"\n\n用户最新提问：{query}"
    try:
        raw = chat_raw(
            [
                {"role": "system", "content": CLARIFY_SYSTEM},
                {"role": "user", "content": prompt},
            ]
        )
    except LLMError:
        # 分不清意图时宁可拒答，也不能猜 —— 澄清路径 fail-closed
        return QAResult(mode="refused", answer=REFUSAL, sources=[], search_query=search_query)

    parsed = _parse_clarify_payload(raw) if raw else None
    if parsed is None:
        kind, text, options = _fallback_clarify()
    else:
        kind, text, options = parsed

    if kind == "off_topic":
        return QAResult(mode="off_topic", answer=text, sources=[], search_query=search_query)
    return QAResult(mode="clarify", answer=text, sources=hits, options=options,
                    search_query=search_query)
