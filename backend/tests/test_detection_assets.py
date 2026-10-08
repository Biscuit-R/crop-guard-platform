"""老版 UI 迁移配套端点：图片回源 / 图鉴列表 / 个人统计。

- GET /detections/{id}/image?variant=original|result —— MinIO 回源，鉴权 + 越权 404
- GET /rag/pests —— 102 条图鉴全量（前端图鉴页/浮窗数据源）
- GET /detections/stats/summary —— 我的页统计卡（总数/检出数/成功率/活跃天数）
"""

import io

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base, get_db
from app.main import app
from app.modules.auth.deps import get_redis
from app.modules.detection.inference import get_detector
from app.modules.detection.storage import get_storage
from tests.test_auth_service import FakeRedis
from tests.test_detection import FakeDetector, FakeStorage, JPEG_MAGIC, _det

PNG_MAGIC = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


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
    storage = FakeStorage()
    app.dependency_overrides[get_storage] = lambda: storage
    app.dependency_overrides[get_detector] = lambda: FakeDetector(detections=[_det()])

    with TestClient(app) as c:
        yield c, storage
    app.dependency_overrides.clear()


def _register(c, username="assetuser", phone="13800000051"):
    c.post("/auth/sms/send", json={"phone": phone})
    code = c.app.dependency_overrides[get_redis]().get(f"sms:code:{phone}")
    resp = c.post("/auth/register", json={
        "username": username, "password": "s3cret-pw",
        "phone": phone, "code": code,
    })
    assert resp.status_code == 201, resp.text
    return {"Authorization": f"Bearer {resp.json()['token']}"}


def _upload(c, headers, data=JPEG_MAGIC, mime="image/jpeg"):
    resp = c.post("/detections", files={"image": (f"a.{'jpg' if 'jpeg' in mime else 'png'}",
                                                  io.BytesIO(data), mime)}, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_original_and_result_image_roundtrip(env):
    c, storage = env
    headers = _register(c)
    record = _upload(c, headers)

    r = c.get(f"/detections/{record['id']}/image?variant=original", headers=headers)
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("image/jpeg")
    assert r.content == JPEG_MAGIC

    r = c.get(f"/detections/{record['id']}/image?variant=result", headers=headers)
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("image/jpeg")
    assert r.content == b"annotated-bytes"


def test_png_original_gets_png_content_type(env):
    c, _ = env
    headers = _register(c, "assetuser2")
    record = _upload(c, headers, data=PNG_MAGIC, mime="image/png")
    r = c.get(f"/detections/{record['id']}/image?variant=original", headers=headers)
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("image/png")


def test_image_requires_auth_and_404s(env):
    c, _ = env
    headers = _register(c, "assetuser3")
    record = _upload(c, headers)

    other = _register(c, "assetuser4", phone="13800000052")
    assert c.get(f"/detections/{record['id']}/image", headers=other).status_code == 404
    assert c.get("/detections/99999/image", headers=headers).status_code == 404
    assert c.get(f"/detections/{record['id']}/image").status_code in (401, 403)


def test_failed_record_has_no_result_image(env):
    c, _ = env
    headers = _register(c, "assetuser5")
    c.app.dependency_overrides[get_detector] = lambda: FakeDetector(error=RuntimeError("boom"))
    record = _upload(c, headers)
    assert record["status"] == "failed"

    assert c.get(f"/detections/{record['id']}/image?variant=result",
                 headers=headers).status_code == 404


def test_pest_list_returns_full_database(env):
    c, _ = env
    resp = c.get("/rag/pests")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 102
    first = data[0]
    for field in ("name", "chinese_name", "scientific_name", "description",
                  "host_plants", "damage_symptoms", "control_methods"):
        assert field in first, f"图鉴页需要的字段 {field} 缺失"


def test_stats_aggregates_own_records(env):
    c, _ = env
    headers = _register(c, "assetuser6")
    _upload(c, headers)  # done，1 个检出
    r = c.get("/detections/stats/summary", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["total_detections"] == 1
    assert body["total_objects"] == 1
    assert body["success_rate"] == 100
    assert body["active_days"] >= 1

    # 失败记录也计入总数（失败也落库），但拉低成功率
    c.app.dependency_overrides[get_detector] = lambda: FakeDetector(error=RuntimeError("x"))
    _upload(c, headers)
    body = c.get("/detections/stats/summary", headers=headers).json()
    assert body["total_detections"] == 2
    assert body["total_objects"] == 1
    assert body["success_rate"] == 50

    assert c.get("/detections/stats/summary").status_code in (401, 403)
