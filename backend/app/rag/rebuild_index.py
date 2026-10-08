"""重建向量索引（标准 1）：语料 → 切分 → 编码 → 清库重建。

编排逻辑（配对、清库先于插入、单批编码、提交）由 tests/test_rebuild_index.py
用假件锁定；SQL 由 live PG 集成验证。
"""

from app.rag.chunking import build_chunks
from app.rag.pgvector import vector_literal

DDL = """
CREATE TABLE IF NOT EXISTS corpus_chunks (
    id           SERIAL PRIMARY KEY,
    pest_name    VARCHAR(64)  NOT NULL,
    chinese_name VARCHAR(32)  NOT NULL,
    chunk_type   SMALLINT     NOT NULL,
    content      TEXT         NOT NULL,
    embedding    vector(512)  NOT NULL
)
"""

HNSW = """
CREATE INDEX IF NOT EXISTS corpus_chunks_embedding_hnsw
    ON corpus_chunks USING hnsw (embedding vector_cosine_ops)
"""

INSERT = """
INSERT INTO corpus_chunks (pest_name, chinese_name, chunk_type, content, embedding)
VALUES (%s, %s, %s, %s, %s::vector)
"""


def build_rows(chunks, embeddings):
    if len(chunks) != len(embeddings):
        raise ValueError(f"块数 {len(chunks)} 与向量数 {len(embeddings)} 不一致")
    return [
        (c.pest_name, c.chinese_name, c.chunk_type, c.content, emb)
        for c, emb in zip(chunks, embeddings)
    ]


def rebuild(conn, encoder, entries):
    chunks = build_chunks(entries)
    embeddings = encoder.encode([c.content for c in chunks])
    rows = build_rows(chunks, embeddings)

    cur = conn.cursor()
    cur.execute(DDL)
    cur.execute(HNSW)
    cur.execute("DELETE FROM corpus_chunks")
    for row in rows:
        cur.execute(INSERT, (*row[:4], vector_literal(row[4])))
    conn.commit()
    return len(rows)


def main():
    """标准 1 的那条命令：uv run python -m app.rag.rebuild_index"""
    from app.data.pest_database import PEST_DATABASE
    from app.db.session import engine

    from .embedding import BGEEncoder

    conn = engine.raw_connection()
    try:
        count = rebuild(conn, BGEEncoder(), PEST_DATABASE)
    finally:
        conn.close()
    print(f"重建完成：{count} 块已入 corpus_chunks")


if __name__ == "__main__":
    main()
