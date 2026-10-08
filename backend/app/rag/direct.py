"""RAG 入口①（D12）：检测结果的 class_name → 查表直出。

与入口②（症状描述 → 向量检索 → LLM）相对：入口①的键是模型输出的英文名，
查询是精确 SQL，**不过 LLM** —— 知识卡的确定内容不该有生成的随机性。
"""

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.data.pest_database import PEST_DATABASE

_LOOKUP = {e["name"]: e for e in PEST_DATABASE}

_SECTIONS_SQL = text(
    "SELECT chinese_name, chunk_type, content FROM corpus_chunks "
    "WHERE pest_name = :name ORDER BY id"
)


def pest_profile(db: Session, class_name: str) -> dict | None:
    entry = _LOOKUP.get(class_name)
    rows = db.execute(_SECTIONS_SQL, {"name": class_name}).fetchall()
    if entry is None and not rows:
        return None
    return {
        "name": class_name,
        "chinese_name": entry["chinese_name"] if entry else rows[0].chinese_name,
        "meta": entry,  # 无条目但有语料时为 None，前端只渲染 sections
        "sections": [{"chunk_type": r.chunk_type, "content": r.content} for r in rows],
    }
