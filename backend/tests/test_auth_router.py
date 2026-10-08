"""账号切片 · 路由接线测试（真实依赖：SQLite + FakeRedis，换掉 PG/Redis）。"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base, get_db
from app.main import app
from app.modules.auth.deps import get_redis

SECRET = "test-secret"


@pytest.fixture()
def client():
    # StaticPool：内存 SQLite 的所有连接共享同一库（否则应用线程拿到空库）
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, future=True)

    def override_db():
        db = factory()
        try:
            yield db
        finally:
            db.close()

    from tests.test_auth_service import FakeRedis

    store = FakeRedis()

    def override_redis():
        return store

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_redis] = override_redis
    with TestClient(app) as c:
        yield c, store
    app.dependency_overrides.clear()


def _send_sms(client, phone="13800000009"):
    resp = client.post("/auth/sms/send", json={"phone": phone})
    assert resp.status_code == 200
    return resp


def test_full_flow_register_login_me_logout(client):
    c, store = client
    _send_sms(c)
    code = store.get("sms:code:13800000009")

    resp = c.post("/auth/register", json={
        "username": "farmer09", "password": "s3cret-pw", "phone": "13800000009", "code": code
    })
    assert resp.status_code == 201, resp.text
    token = resp.json()["token"]

    resp = c.post("/auth/login", json={"username": "farmer09", "password": "s3cret-pw"})
    assert resp.status_code == 200
    token2 = resp.json()["token"]

    resp = c.get("/auth/me", headers={"Authorization": f"Bearer {token2}"})
    assert resp.status_code == 200
    assert resp.json()["username"] == "farmer09"

    resp = c.post("/auth/logout", headers={"Authorization": f"Bearer {token2}"})
    assert resp.status_code == 200

    # 登出后旧 token 立即失效（服务端撤销语义）
    resp = c.get("/auth/me", headers={"Authorization": f"Bearer {token2}"})
    assert resp.status_code == 401


def test_me_rejects_missing_or_bad_token(client):
    c, _ = client
    assert c.get("/auth/me").status_code in (401, 403)
    assert c.get("/auth/me", headers={"Authorization": "Bearer garbage"}).status_code == 401


def test_register_with_bad_code_is_400(client):
    c, _ = client
    _send_sms(c, "13800000010")
    resp = c.post("/auth/register", json={
        "username": "farmer10", "password": "s3cret-pw", "phone": "13800000010", "code": "000000"
    })
    assert resp.status_code == 400


def test_change_password_invalidates_all_sessions(client):
    c, store = client
    _send_sms(c, "13800000011")
    code = store.get("sms:code:13800000011")
    token = c.post("/auth/register", json={
        "username": "farmer11", "password": "s3cret-pw", "phone": "13800000011", "code": code
    }).json()["token"]
    # 再登录一个「另一端」
    token_b = c.post("/auth/login", json={"username": "farmer11", "password": "s3cret-pw"}).json()["token"]

    resp = c.post("/auth/password", headers={"Authorization": f"Bearer {token}"},
                  json={"old_password": "s3cret-pw", "new_password": "brand-new-77"})
    assert resp.status_code == 200

    # 验收标准：改密后所有端立即失效
    assert c.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401
    assert c.get("/auth/me", headers={"Authorization": f"Bearer {token_b}"}).status_code == 401
