"""切片 1 · 标准 1/3 的编排层测试。

rebuild 的纯编排逻辑在这里用假件测：行与向量按序配对、清库先于插入、
批量编码、提交后返回行数。SQL 方言与 pgvector 的真实行为由 live PG 集成验证
（标准 3 的 512 维/行数/非零断言在真库上跑），不在这里 mock SQL 字符串本身。
"""

from app.rag.chunking import build_chunks
from app.rag.rebuild_index import build_rows, rebuild

SAMPLE_ENTRY = {
    "name": "rice_leaf_roller",
    "chinese_name": "稻纵卷叶螟",
    "description": "水稻迁飞性重要害虫",
    "host_plants": "水稻、稗草",
    "morphology": "成虫体长约10mm",
    "damage_symptoms": "幼虫吐丝纵卷叶片成虫苞",
    "occurrence_period": "长江流域5-9月",
    "control_methods": "①农业防治：合理施肥",
}


class FakeEncoder:
    """确定性假编码器：向量由文本长度派生，可断言配对关系。"""

    dim = 4

    def encode(self, texts):
        self.calls = getattr(self, "calls", 0) + 1
        self.last_batch_size = len(texts)
        return [[float(len(t)), 1.0, 2.0, 3.0] for t in texts]


class RecordingConn:
    def __init__(self):
        self.sql_log = []
        self.committed = False

    def cursor(self):
        conn = self

        class _Cur:
            def execute(_self, sql, params=None):
                conn.sql_log.append((sql.strip(), params))

        return _Cur()

    def commit(self):
        self.committed = True


def _entries(n=2):
    return [dict(SAMPLE_ENTRY, name=f"pest_{i}", chinese_name=f"虫{i}") for i in range(n)]


def test_build_rows_pairs_chunks_with_embeddings_in_order():
    chunks = build_chunks(_entries(2))  # 2 条 × 3 块 = 6 块
    encoder = FakeEncoder()
    embeddings = encoder.encode([c.content for c in chunks])
    rows = build_rows(chunks, embeddings)
    assert len(rows) == 6
    for row, chunk, emb in zip(rows, chunks, embeddings):
        assert row[:4] == (chunk.pest_name, chunk.chinese_name, chunk.chunk_type, chunk.content)
        assert row[4] == emb


def test_build_rows_rejects_mismatched_lengths():
    chunks = build_chunks(_entries(2))
    try:
        build_rows(chunks, [[0.0] * 4] * (len(chunks) - 1))
    except ValueError:
        pass
    else:
        raise AssertionError("块数与向量数不一致时必须报错")


def test_rebuild_clears_before_insert():
    conn = RecordingConn()
    rebuild(conn, FakeEncoder(), _entries(2))
    inserts = [i for i, (sql, _) in enumerate(conn.sql_log) if sql.upper().startswith("INSERT")]
    deletes = [i for i, (sql, _) in enumerate(conn.sql_log) if "DELETE FROM corpus_chunks" in sql]
    assert deletes and inserts, "缺少清库或插入"
    assert deletes[0] < inserts[0], "清库必须发生在插入之前"


def test_rebuild_encodes_in_one_batch():
    conn = RecordingConn()
    encoder = FakeEncoder()
    rebuild(conn, encoder, _entries(2))
    assert encoder.calls == 1
    assert encoder.last_batch_size == 6


def test_rebuild_returns_count_and_commits():
    conn = RecordingConn()
    count = rebuild(conn, FakeEncoder(), _entries(2))
    assert count == 6
    assert conn.committed
