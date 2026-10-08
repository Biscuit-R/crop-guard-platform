"""检测历史切片测试：列表/详情/删除。

验收语义：
- 越权访问 → **404**（不是 403 —— 不泄露「记录存在但不是你的」）
- 列表 SQL 语句数为常数：page_size 再大也不逐条查（无 N+1，用事件计数器锁死）
- 删除同时清存储对象（原图 + 标注图），不留孤儿
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base, get_db
from app.main import app
from app.modules.auth.deps import get_redis
from app.modules.detection.inference import get_detector
from app.modules.detection.storage import get_storage
from tests.test_auth_service import FakeRedis
from tests.test_detection import FakeDetector, FakeStorage, JPEG_MAGIC

import io


@pytest.fixture()
def env():
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

    store = FakeRedis()
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_redis] = lambda: store
    storage, detector = FakeStorage(), FakeDetector()
    app.dependency_overrides[get_storage] = lambda: storage
    app.dependency_overrides[get_detector] = lambda: detector

    with TestClient(app) as c:
        yield c, store, storage, engine
    app.dependency_overrides.clear()


def _user(c, store, username, phone):
    c.post("/auth/sms/send", json={"phone": phone})
    code = store.get(f"sms:code:{phone}")
    resp = c.post("/auth/register", json={
        "username": username, "password": "s3cret-pw", "phone": phone, "code": code,
    })
    assert resp.status_code == 201, resp.text
    return {"Authorization": f"Bearer {resp.json()['token']}"}


def _upload(c, headers):
    resp = c.post("/detections", files={"image": ("a.jpg", io.BytesIO(JPEG_MAGIC), "image/jpeg")},
                  headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_list_returns_own_records_paginated(env):
    c, store, _, _ = env
    headers = _user(c, store, "hist1", "13800000031")
    for _ in range(3):
        _upload(c, headers)

    resp = c.get("/detections?page=1&page_size=2", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 3
    assert len(body["items"]) == 2
    assert body["page"] == 1

    resp = c.get("/detections?page=2&page_size=2", headers=headers)
    assert len(resp.json()["items"]) == 1


def test_list_is_scoped_to_owner(env):
    c, store, _, _ = env
    h1 = _user(c, store, "histA", "13800000032")
    h2 = _user(c, store, "histB", "13800000033")
    _upload(c, h1)
    _upload(c, h1)

    resp = c.get("/detections", headers=h2)
    assert resp.json()["total"] == 0


def test_detail_and_delete_cross_user_are_404(env):
    c, store, storage, _ = env
    h1 = _user(c, store, "histC", "13800000034")
    h2 = _user(c, store, "histD", "13800000035")
    record = _upload(c, h1)

    assert c.get(f"/detections/{record['id']}", headers=h2).status_code == 404
    assert c.delete(f"/detections/{record['id']}", headers=h2).status_code == 404
    # 越权删除不得真的删掉
    assert c.get(f"/detections/{record['id']}", headers=h1).status_code == 200


def test_delete_removes_storage_objects(env):
    c, store, storage, _ = env
    headers = _user(c, store, "histE", "13800000036")
    record = _upload(c, headers)
    keys_before = set(storage.objects)
    assert keys_before, "上传成功应有存储对象"

    resp = c.delete(f"/detections/{record['id']}", headers=headers)
    assert resp.status_code == 204
    assert set(storage.objects).isdisjoint(keys_before), "删除必须清掉原图与标注图"
    assert c.get(f"/detections/{record['id']}", headers=headers).status_code == 404


def test_detail_includes_detections(env):
    from tests.test_detection import _det
    c, store, _, _ = env
    app.dependency_overrides[get_detector] = lambda: FakeDetector(detections=[_det()])
    headers = _user(c, store, "histF", "13800000037")
    record = _upload(c, headers)

    resp = c.get(f"/detections/{record['id']}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["detections"][0]["chinese_name"] == "稻纵卷叶螟"


def test_list_sql_count_is_constant_regardless_of_page_size(env):
    """page_size 拉满时 SELECT 数不变 —— 无 N+1（事件计数器作证）。"""
    c, store, _, engine = env
    headers = _user(c, store, "histG", "13800000038")
    for _ in range(5):
        _upload(c, headers)

    counter = {"selects": 0}

    def count(conn, cursor, statement, params, context, executemany):
        if statement.lstrip().upper().startswith("SELECT"):
            counter["selects"] += 1

    event.listen(engine, "before_cursor_execute", count)
    try:
        r1 = c.get("/detections?page=1&page_size=1", headers=headers)
        assert r1.status_code == 200, "请求失败则计数无意义"
        small = counter["selects"]
        assert small >= 2, "至少 count + 一页两条 SELECT，计数为 0 说明测试空转"
        counter["selects"] = 0
        r2 = c.get("/detections?page=1&page_size=100", headers=headers)
        assert r2.status_code == 200
        big = counter["selects"]
    finally:
        event.remove(engine, "before_cursor_execute", count)

    assert big == small, f"page_size 变大 SELECT 数变多（{small} → {big}），存在 N+1"
