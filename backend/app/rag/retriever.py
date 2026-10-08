"""向量检索（入口②第一步）：症状描述 → top-k 相关语料块。

排序用 pgvector 的余弦距离 `<=>`。入库时向量已归一（embedding.py），
余弦距离等价于欧氏距离的平方差，但直接用 `<=>` 语义最直白；
score = 1 - distance，落在 [0, 1]，直接对接 D10 的阈值三档。

SQL 的真实行为（排序、维度）由真库冒烟验证；这里只锁编排。
"""

from dataclasses import dataclass

from sqlalchemy import text

from app.rag.pgvector import vector_literal

DEFAULT_TOP_K = 3  # 需求写死 top-3（requirements.md 验收表）

SEARCH_SQL = text("""
SELECT pest_name, chinese_name, chunk_type, content,
       1 - (embedding <=> CAST(:vec AS vector)) AS score
FROM corpus_chunks
ORDER BY embedding <=> CAST(:vec AS vector)
LIMIT :k
""")


@dataclass
class Retrieved:
    pest_name: str
    chinese_name: str
    chunk_type: int
    content: str
    score: float


def retrieve(session, encoder, query: str, top_k: int = DEFAULT_TOP_K) -> list[Retrieved]:
    """session 是 SQLAlchemy Session；单次编码 + 单条 SQL，检索 P99 达标的前提。"""
    vec = encoder.encode([query])[0]
    result = session.execute(SEARCH_SQL, {"vec": vector_literal(vec), "k": top_k})
    return [Retrieved(*row) for row in result.fetchall()]
