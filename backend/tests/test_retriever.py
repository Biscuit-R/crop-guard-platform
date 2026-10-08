"""切片 2 · 检索层测试。

检索的编排（单次编码、余弦距离 SQL、行映射、top_k 传递）在这里用假件锁；
SQL 与 pgvector 的真实排序行为由真库冒烟验证（标准 2），不在这里 mock 数据库方言。
"""

from app.rag.retriever import DEFAULT_TOP_K, Retrieved, retrieve


class FakeEncoder:
    dim = 4

    def __init__(self):
        self.calls = 0
        self.texts = []

    def encode(self, texts):
        self.calls += 1
        self.texts.extend(texts)
        return [[0.1, 0.2, 0.3, 0.4] for _ in texts]


class FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


class FakeSession:
    def __init__(self, rows):
        self.executed = []
        self._rows = rows

    def execute(self, sql, params=None):
        self.executed.append((str(sql), params))
        return FakeResult(self._rows)


ROW = (
    "rice_leaf_roller",
    "稻纵卷叶螟",
    2,
    "【稻纵卷叶螟·症状】幼虫吐丝纵卷叶片成虫苞",
    0.87,
)


def test_retrieve_encodes_query_once():
    session = FakeSession([ROW])
    encoder = FakeEncoder()
    retrieve(session, encoder, "叶子被卷起来了")
    assert encoder.calls == 1
    assert encoder.texts == ["叶子被卷起来了"]


def test_retrieve_uses_cosine_distance_sql():
    session = FakeSession([ROW])
    retrieve(session, FakeEncoder(), "q")
    sql = session.executed[0][0]
    assert "<=>" in sql, "必须用余弦距离算子 <=>"
    assert "ORDER BY" in sql and "LIMIT" in sql


def test_retrieve_maps_rows_to_retrieved():
    session = FakeSession([ROW])
    hits = retrieve(session, FakeEncoder(), "q")
    assert hits == [
        Retrieved(
            pest_name="rice_leaf_roller",
            chinese_name="稻纵卷叶螟",
            chunk_type=2,
            content="【稻纵卷叶螟·症状】幼虫吐丝纵卷叶片成虫苞",
            score=0.87,
        )
    ]


def test_retrieve_default_top_k_is_three():
    session = FakeSession([ROW])
    retrieve(session, FakeEncoder(), "q")
    assert session.executed[0][1]["k"] == DEFAULT_TOP_K == 3


def test_retrieve_passes_vector_literal():
    session = FakeSession([ROW])
    retrieve(session, FakeEncoder(), "q")
    vec = session.executed[0][1]["vec"]
    assert vec.startswith("[") and vec.endswith("]")
    assert "0.1" in vec and "0.4" in vec
