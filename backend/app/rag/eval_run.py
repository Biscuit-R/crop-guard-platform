"""评测跑测（切片 2 标准 3）：跑 rag-eval-set.md 的 40 题，产出测量数据。

C 类参数（top-k、两阈值）由本脚本的输出**测量**得出，不拍脑袋（handoff.md 第 4 节）。
产出三组数字：
  1. top-k 曲线（k=1..5 的命中率）→ 定 top-k
  2. 症状题 vs B1 无关题的 max(similarity) 分布 → 定两阈值
  3. B1 拒答率（在示意阈值下）→ 验收「B1 拒答率 = 100%」

评测集已于 2026-10-08 口语化改写定稿（docs/rag-eval-set.md）；
本脚本产出的数字是「真实农户口吻」下的测量，与草稿集的乐观上界不可直接对比。

用法：uv run python -m app.rag.eval_run
"""

from app.core.config import get_settings
from app.data.pest_database import PEST_DATABASE
from app.db.session import SessionLocal
from app.rag.embedding import BGEEncoder
from app.rag.retriever import retrieve

# ---- 评测集（docs/rag-eval-set.md；2026-10-08 用户口语化改写后的定稿文本）----
# A · 30 条症状题（s01-s30）
EVAL_A = [
    ("s01", "水稻叶子被虫子卷成圆筒一样的虫苞，里面的叶肉被啃掉，只剩一层皮，变成白色条斑，严重时整片叶子发白枯掉", ["001"]),
    ("s02", "玉米心叶和雄穗被虫子吃掉，茎秆被蛀后容易折秆，穗柄也会断，雌穗被蛀后发霉腐烂", ["023"]),
    ("s03", "葡萄根部鼓起菱形的小瘤子，根系烂掉坏死，树越来越弱，最后死掉", ["060"]),
    ("s04", "柑橘果皮上有像针扎一样的小圆孔，孔周围有一圈晕，果子还没熟就先发黄掉落，果肉也烂了", ["084"]),
    ("s05", "小麦穗上的幼虫钻进颖壳里吸浆液，麦粒变得干瘪，严重时整穗都是空壳", ["031"]),
    ("s06", "桑树枝干被虫子蛀进木质部，隧道里全是虫粪，被害枝条上部枯死", ["066"]),
    ("s07", "芒果叶片被虫子沿着叶缘切掉，还卷成筒状，很多叶子变得缺一块少一块", ["097"]),
    ("s08", "水稻心叶展不开，变成葱管一样的虫瘿，受害的稻株抽不出穗", ["006"]),
    ("s09", "稻子根茎那里发黑烂掉，整株枯死倒伏，田里东一片西一片地枯", ["008"]),
    ("s10", "叶子正面密密麻麻全是白点，翻过来背面能看到红色小虫和蛛丝，叶子慢慢发红枯掉", ["022"]),
    ("s11", "棉花嫩叶卷起来、长歪了，叶子上黏糊糊的，还起黑色的霉", ["025"]),
    ("s12", "菜叶上全是密密麻麻的小孔，像筛子眼一样", ["038"]),
    ("s13", "玉米穗上有蛀孔，孔外边堆着一大堆虫粪，籽粒也霉烂了", ["030"]),
    ("s14", "柑橘果面的油胞破了，往外流油，氧化以后变成褐色", ["076"]),
    ("s15", "温室番茄叶子背面一群小白虫，一碰就飞起来", ["072"]),
    ("s16", "苹果树叶被吃得只剩主脉和叶柄，虫子身上有刺，碰到很疼", ["059"]),
    ("s17", "苜蓿种子被蛀空，只剩一层种皮", ["056"]),
    ("s18", "亚麻蒴果里有虫，种子被吃掉了", ["046"]),
    ("s19", "玉米穗顶端的籽粒被啃掉，向日葵花盘上也爬满了虫子", ["029"]),
    ("s20", "柑橘嫩叶里有银白色弯曲的隧道，叶子卷缩硬化，嫩梢也受害", ["089"]),
    ("s21", "稻叶上有一条条白纹，叶肉像被虫子刮掉一层，严重的整片叶子都发白了", ["001", "014"]),
    ("s22", "水稻先是叶鞘那里枯了，后来茎秆也被蛀，出现枯心和白穗", ["004", "005"]),
    ("s23", "水稻基部有一群小虫在吸汁，茎上还有褐色斑点", ["008", "009", "010"]),
    ("s24", "小麦抽穗的时候，穗上和旗叶上爬满蚜虫，麦粒都瘪了", ["026", "027", "028"]),
    ("s25", "苜蓿叶片上有破孔，还皱皱缩缩的，农民管这个叫「破叶疯」", ["047", "048", "058", "071"]),
    ("s26", "柑橘的枝叶和果子上密密麻麻全是小突起，树越来越弱", ["077", "078", "079", "080", "081", "082"]),
    ("s27", "柑橘叶子正面有很多灰白色失绿小点，密密麻麻的，严重时落叶落果", ["075", "076"]),
    ("s28", "白菜叶子被吃得只剩叶脉和叶柄，叶球里还有虫粪", ["039", "057"]),
    ("s29", "柑橘成熟果子上有针刺一样的小孔，然后烂掉脱落，但果皮下没有产卵孔那圈晕", ["088"]),
    ("s30", "幼苗茎基部被咬断，苗倒了，白天扒开土能看到虫子", ["018", "019", "020", "021"]),
]

# B1 · 6 条明显无关题（n01-n06）
EVAL_B1 = [
    ("n01", "今天北京的天气怎么样？"),
    ("n02", "帮我写一个 Python 的快速排序"),
    ("n03", "苹果手机怎么截屏？"),
    ("n04", "推荐几本科幻小说"),
    ("n05", "解释一下什么是相对论"),
    ("n06", "Excel 怎么做数据透视表？"),
]

# B2 · 4 条农业相关但语料没有（n07-n10，按拍板允许落中间档）
EVAL_B2 = [
    ("n07", "我家地里的土壤板结了怎么办？"),
    ("n08", "化肥施多了烧苗怎么办？"),
    ("n09", "水稻田里稗草很多，用什么除草剂？"),
    ("n10", "蔬菜大棚冬天怎么保温？"),
]

MAX_K = 5  # top-k 曲线上限；需求写死 top-3，曲线只用于确认 3 是否合理


def main():
    id_to_entry = {f"{i + 1:03d}": e for i, e in enumerate(PEST_DATABASE)}
    encoder = BGEEncoder()
    session = SessionLocal()
    try:
        # ---- 1. top-k 曲线（A 组，一次取 MAX_K，逐级累计判命中）----
        print(f"== top-k 曲线（A 组 {len(EVAL_A)} 题，期望命中进 top-k 即算）==")
        curve = {k: 0 for k in range(1, MAX_K + 1)}
        a_rows = []
        for qid, q, expected in EVAL_A:
            want = {id_to_entry[i]["chinese_name"] for i in expected}
            hits = retrieve(session, encoder, q, MAX_K)
            names = [h.chinese_name for h in hits]
            a_rows.append((qid, want, hits))
            for k in range(1, MAX_K + 1):
                if want & set(names[:k]):
                    curve[k] += 1
        for k in sorted(curve):
            print(f"  k={k}: 命中 {curve[k]}/{len(EVAL_A)} = {curve[k] / len(EVAL_A):.0%}")
        n3 = curve[3] / len(EVAL_A)
        print(f"  → top-3 命中率 = {n3:.0%}（验收线 ≥ 80%：{'达标' if n3 >= 0.8 else '未达标'}）")

        # ---- 2. 分数分布（定两阈值的依据）----
        print("\n== max(similarity) 分布 ==")
        a_scores = []
        for qid, want, hits in a_rows:
            top = hits[0]
            mark = "✓" if want & {h.chinese_name for h in hits[:3]} else "✗"
            a_scores.append(top.score)
            print(f"  {qid} {mark} top1={top.score:.4f} {top.chinese_name}")
        b1_scores = []
        for qid, q in EVAL_B1:
            top = retrieve(session, encoder, q, 1)[0]
            b1_scores.append(top.score)
            print(f"  {qid} 拒? top1={top.score:.4f} {top.chinese_name}")
        a_sorted = sorted(a_scores, reverse=True)
        print(f"\n  A 组最高 {a_sorted[0]:.4f}，最低 {a_sorted[-1]:.4f}")
        print(f"  B1 组最高 {max(b1_scores):.4f}，最低 {min(b1_scores):.4f}")
        overlap = max(b1_scores) >= min(a_scores)
        print(f"  分布重叠：{'是 ⚠️（阈值无法两全，按 rag-eval-set.md C 节处理）' if overlap else '否 → 阈值取两组分界'}")

        # ---- 3. B1 拒答率（低阈值取自配置：2026-10-05 实测定值）----
        low = get_settings().retrieval_low
        refused = sum(1 for s in b1_scores if s < low)
        print(f"\n== B1 拒答率（示意低阈值 {low}）== {refused}/{len(EVAL_B1)} = {refused / len(EVAL_B1):.0%}（验收线 = 100%）")
        print("== B2 落点（拍板：允许中间档作答+标注）==")
        for qid, q in EVAL_B2:
            top = retrieve(session, encoder, q, 1)[0]
            band = "拒答" if top.score < low else "中间档/作答"
            print(f"  {qid} top1={top.score:.4f} → {band}（{top.chinese_name}）")
    finally:
        session.close()


if __name__ == "__main__":
    main()
