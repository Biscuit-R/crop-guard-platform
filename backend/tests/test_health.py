"""骨架的第一个真实测试。

刻意**不空** —— 归档的问题是「零测试」，一个空的 tests/ 目录修不了它。
这些测试运行时不碰数据库：SQLAlchemy 的引擎是惰性的（建引擎不等于连库），
需要「数据库故障」的场景用依赖覆盖伪造，所以 CI 里不需要起 postgres 就能跑。
"""

import pytest
from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app

client = TestClient(app)


class _BrokenSession:
    """假装数据库挂了：任何查询都抛。"""

    def execute(self, *args, **kwargs):
        raise RuntimeError("database is down")


def _broken_db():
    yield _BrokenSession()


@pytest.fixture
def database_down():
    app.dependency_overrides[get_db] = _broken_db
    yield
    app.dependency_overrides.clear()


def test_health_returns_ok():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_liveness_survives_database_outage(database_down):
    """存活探针必须与数据库解耦 —— 这是分成两个端点**唯一**的理由。

    如果哪天有人把 `db.execute("SELECT 1")` 挪进 `/health`，这条会红。
    """
    assert client.get("/health").status_code == 200


def test_readiness_fails_closed_when_database_is_down(database_down):
    """数据库挂了，就绪探针要返回 503 而不是 500。

    区别是有意义的：503 告诉编排层「别给我派流量」，500 只是「我出错了」。
    """
    resp = client.get("/health/ready")
    assert resp.status_code == 503
    assert resp.json() == {"status": "unavailable", "database": "down"}


def test_routes_are_mounted():
    """防止 api.py 的 include_router 被误删。

    前两条测试在那种情况下仍然会过（`/health` 是定义在 router 里的），
    所以必须直接问 OpenAPI —— 那是框架的公开契约，比翻 `app.routes` 稳。
    """
    schema = client.get("/openapi.json").json()
    assert "/health" in schema["paths"]
    assert "/health/ready" in schema["paths"]
