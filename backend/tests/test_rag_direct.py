"""RAG 入口①（D12）：检测 class_name → SQL 查表直出，不过 LLM、不做向量检索。

验收语义：
- 图鉴元数据 + 图鉴语料分节一次返回（检测页知识卡一次拉全）
- 未收录 → None → 路由 404
- 语料无块但图鉴有条目 → 仍返回元数据（sections 为空）
"""

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.rag.direct import pest_profile

TEST_DDL = """
CREATE TABLE corpus_chunks (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    pest_name    VARCHAR(64) NOT NULL,
    chinese_name VARCHAR(32) NOT NULL,
    chunk_type   SMALLINT    NOT NULL,
    content      TEXT        NOT NULL
)
"""


@pytest.fixture()
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    conn = engine.connect()
    conn.execute(text(TEST_DDL))
    conn.execute(text(
        "INSERT INTO corpus_chunks (pest_name, chinese_name, chunk_type, content) VALUES "
        "('rice_leaf_roller', '稻纵卷叶螟', 1, '成虫前翅有两条横线'),"
        "('rice_leaf_roller', '稻纵卷叶螟', 2, '药剂防治：甲维盐')"
    ))
    conn.commit()
    session = sessionmaker(bind=engine, future=True)()
    yield session
    session.close()
    conn.close()


def test_profile_returns_meta_and_sections(db):
    profile = pest_profile(db, "rice_leaf_roller")
    assert profile is not None
    assert profile["chinese_name"] == "稻纵卷叶螟"
    assert profile["meta"]["scientific_name"]
    assert [s["chunk_type"] for s in profile["sections"]] == [1, 2]
    assert "甲维盐" in profile["sections"][1]["content"]


def test_unlisted_pest_returns_none(db):
    assert pest_profile(db, "no_such_pest") is None


def test_meta_only_when_corpus_missing(db):
    """语料缺块不炸：图鉴条目兜底。"""
    profile = pest_profile(db, "rice_leaf_caterpillar")
    assert profile is not None
    assert profile["chinese_name"] == "稻螟蛉"
    assert profile["sections"] == []


def test_corpus_only_pest_uses_corpus_chinese_name(db):
    """验收发现的兜底分支：图鉴缺条目但语料有行 —— 中文名取自语料，不得炸。"""
    db.execute(text(
        "INSERT INTO corpus_chunks (pest_name, chinese_name, chunk_type, content) "
        "VALUES ('ghost_pest', '幽灵虫', 1, '只在语料里出现')"
    ))
    db.commit()
    profile = pest_profile(db, "ghost_pest")
    assert profile is not None
    assert profile["chinese_name"] == "幽灵虫"
    assert profile["meta"] is None
    assert len(profile["sections"]) == 1
