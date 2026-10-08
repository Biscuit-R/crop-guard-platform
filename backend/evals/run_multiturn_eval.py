"""多轮评测（query 改写切片验收）：对比 turn-2 检索「改写 on/off」的 top-3 命中率。

背景（切片 2 实测发现）：指代续问（「它怎么防治？」）检索打不中 —— BGE 只看
当前这句话的向量，历史不进视野；口语描述（「绿黑色的虫子」）专业词缺失。
query 改写救的就是检索端：改写 = 口语规范化 + 历史指代消解，一次 LLM 调用。

评测口径（与 app/rag/eval_run.py 一致）：
  命中 = 期望害虫中文名出现在 top-3；指标 = turn-2 top-3 命中率，改写 on vs off。
  score 是闸门不是测评标准 —— 测评标准始终是标注期望 + 命中率。

每对是一个两轮对话：turn1 症状/描述 + 助手答复（canned，模拟真实会话），
turn2 是带指代或口语的续问。改写器的输入与线上完全一致（最近轮次 + 原问题）。

红线检查：改写结果若引入「对话文本 + 图鉴虫名表」之外的虫名 → 标 ⚠️（改写模型
用参数知识押题）。这是定性检查，不算进命中率。

前置：Postgres(pgvector) 已起、语料已入库（见 app/rag/rebuild_index.py）、
.env 已配 DEEPSEEK_API_KEY。启动即校验期望中文名全部存在于语料，防止评测对
写错虫名导致假阴性。

用法：uv run python -m evals.run_multiturn_eval
"""

import sys

# Windows GBK 终端：✓/✗ 等符号编不出来会直接抛异常，用 replace 容错
sys.stdout.reconfigure(errors="replace")

from app.core.config import get_settings
from app.data.pest_database import PEST_DATABASE
from app.db.session import SessionLocal
from app.rag.embedding import BGEEncoder
from app.rag.llm import DeepSeekClient
from app.rag.retriever import retrieve
from app.rag.rewrite import LLMError, make_rewriter

TOP_K = 3

# ---- 评测对（8 对）----
# (id, turn1_user, turn1_assistant_canned, turn2_raw, 期望虫害 id 列表)
# turn1_assistant_canned 模拟真实会话答复：confident 答复会点名虫，
# clarify 追问不点名 —— 这决定改写器「能不能」引用虫名（红线边界）。
EVAL_PAIRS = [
    # 指代消解：虫名出现在前轮答复里，改写应当引用
    ("p01", "水稻叶子被卷成白色的虫苞，怎么办？",
     "这符合稻纵卷叶螟的为害特征：幼虫吐丝纵卷单叶或几张叶结成白色虫苞，在苞内啃食叶肉。",
     "它主要在什么时期为害最严重？", ["001"]),
    ("p02", "玉米心叶被咬出一排排小孔，里面还有虫粪",
     "这符合玉米螟的为害特征：幼虫蛀茎为害，心叶被蛀后展开呈排孔状。",
     "用什么药能治住它？", ["023"]),
    ("p03", "棉花嫩叶卷起来了，叶子上黏糊糊的还发霉",
     "这符合棉蚜的为害特征：成蚜若蚜群集嫩头吸汁，分泌蜜露诱发煤污病。",
     "它的天敌有哪些？", ["025"]),
    ("p04", "稻子上一种虫把茎秆蛀空了，出现枯心和白穗",
     "二化螟和稻褐边螟都会造成枯心与白穗：幼虫钻蛀稻茎，破坏生长点与输导组织。",
     "它们俩要怎么区分？", ["004", "005"]),
    # 口语规范化 + 补全省略：前轮答复不点名，改写不得引入虫名
    ("p05", "苹果树上好多虫，叶子被吃得只剩叶脉了",
     "为了帮您定位虫害，请补充：能看到虫体吗？虫子身上有没有刺毛？",
     "就是那种浑身是刺碰了会痒的大虫子", ["059"]),
    ("p06", "玉米苗被虫子从茎基部咬断了",
     "为了帮您定位虫害，请补充：虫子是什么颜色？大小如何？",
     "白天扒开根部土能抓到，灰黑色的小虫", ["018", "019", "020", "021"]),
    ("p07", "小麦穗上爬满了虫",
     "为了帮您定位虫害，请补充：虫子是什么颜色？麦粒有没有变瘪？",
     "绿黑色的，麦粒都瘪了", ["026", "027", "028"]),
    ("p08", "柑橘叶子上密密麻麻的小白虫，一碰就飞起来",
     "这符合温室白粉虱的为害特征：成虫若虫群集叶背吸汁，分泌蜜露诱发煤污病。",
     "这玩意儿冬天能在棚里过冬吗？", ["072"]),
]


def _validate_expected(id_to_entry: dict) -> None:
    """期望中文名必须真实存在于语料 —— 评测对写错虫名是假阴性，宁可启动失败。"""
    for pid, _, _, _, expected in EVAL_PAIRS:
        for eid in expected:
            entry = id_to_entry.get(eid)
            if entry is None:
                raise SystemExit(f"评测对 {pid} 期望 id {eid} 不存在于语料库")
            name = entry["chinese_name"]
            if not name:
                raise SystemExit(f"评测对 {pid} 期望 id {eid} 无 chinese_name")


def _mentioned_pests(text: str, all_names: set[str]) -> set[str]:
    """从对话文本中提取出现过的虫名（红线检查的「白名单」）。"""
    return {n for n in all_names if n in text}


def main():
    id_to_entry = {f"{i + 1:03d}": e for i, e in enumerate(PEST_DATABASE)}
    _validate_expected(id_to_entry)
    all_names = {e["chinese_name"] for e in PEST_DATABASE}

    settings = get_settings()
    if not settings.deepseek_api_key:
        raise SystemExit("DEEPSEEK_API_KEY 未配置：改写评测需要真实 LLM")
    llm = DeepSeekClient(
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        model=settings.deepseek_model,
        timeout=settings.deepseek_timeout,
    )
    rewriter = make_rewriter(llm.chat_raw)
    encoder = BGEEncoder()
    session = SessionLocal()

    raw_hits = 0
    rewr_hits = 0
    fail_open = 0
    redline_warns = 0
    print(f"== 多轮评测：{len(EVAL_PAIRS)} 对，指标 = turn-2 top-{TOP_K} 命中率 ==\n")
    try:
        for pid, t1, a1, t2_raw, expected in EVAL_PAIRS:
            want = {id_to_entry[i]["chinese_name"] for i in expected}
            history = [{"q": t1, "mode": "confident" if "符合" in a1 else "clarify", "a": a1}]
            conversation_text = f"{t1}\n{a1}\n{t2_raw}"

            # off：原问题直接检索
            raw_names = [h.chinese_name for h in retrieve(session, encoder, t2_raw, TOP_K)]
            raw_ok = bool(want & set(raw_names))

            # on：改写后检索；失败 fail-open（与线上 qa.answer 同语义）
            try:
                t2_rewritten = rewriter(t2_raw, history) or t2_raw
            except LLMError:
                t2_rewritten = t2_raw
                fail_open += 1
            rewr_names = [h.chinese_name for h in retrieve(session, encoder, t2_rewritten, TOP_K)]
            rewr_ok = bool(want & set(rewr_names))

            # 红线定性检查：改写引入了对话中没出现过的虫名 → 押题，标警。
            # 白名单做双向包含：对话里出现过「玉米螟」时，改写扩写出的
            # 「亚洲玉米螟」不算引入（同一名实体的短名/全名互认）。
            conv_names = _mentioned_pests(conversation_text, all_names)
            leaked = {
                n for n in _mentioned_pests(t2_rewritten, all_names)
                if n not in conversation_text
                and not any(w in n or n in w for w in conv_names)
            }
            redline_warns += bool(leaked)

            raw_hits += raw_ok
            rewr_hits += rewr_ok
            mark_raw = "✓" if raw_ok else "✗"
            mark_rewr = "✓" if rewr_ok else "✗"
            warn = f"  ⚠️红线:改写引入{leaked}" if leaked else ""
            print(f"{pid} 期望{sorted(want)}")
            print(f"  off {mark_raw} 「{t2_raw}」→ {raw_names}")
            print(f"  on  {mark_rewr} 「{t2_rewritten}」→ {rewr_names}{warn}")
    finally:
        session.close()

    n = len(EVAL_PAIRS)
    print(f"\n== 汇总 ==")
    print(f"  改写 off：{raw_hits}/{n} = {raw_hits / n:.0%}")
    print(f"  改写 on ：{rewr_hits}/{n} = {rewr_hits / n:.0%}")
    if fail_open:
        print(f"  改写 fail-open 次数：{fail_open}（这些对退化为 off 口径）")
    if redline_warns:
        print(f"  ⚠️ 红线警告：{redline_warns} 对的改写引入了对话未提及的虫名（见上）")
    print(f"  结论：改写收益 = on − off = {rewr_hits - raw_hits:+d} 对")


if __name__ == "__main__":
    main()
