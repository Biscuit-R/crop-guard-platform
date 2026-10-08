"""检测切片 · 路由接线测试（真实依赖：SQLite；storage/detector 换假件）。

锁定语义：
- 未登录 401；multipart 上传 → 201 + status
- 内容非图片 → 415（不是扩展名校验）
- 超过大小上限 → 413，且**先于**嗅探/落库（不读内容）
- 推理失败 → 照常返回，body 里 status=failed（失败也落库的对外表现）
"""

import io

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.db.session import Base, get_db
from app.main import app
from app.modules.auth.deps import get_redis
from app.modules.detection.inference import get_detector
from app.modules.detection.storage import get_storage
from tests.test_detection import FakeDetector, FakeStorage, JPEG_MAGIC, _det
from tests.test_auth_service import FakeRedis

JPEG_FILE = {"image": ("pest.jpg", io.BytesIO(JPEG_MAGIC), "image/jpeg")}
TEXT_FILE = {"image": ("x.jpg", io.BytesIO(b"plain text, not an image"), "image/jpeg")}


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
    storage, detector = FakeStorage(), FakeDetector(detections=[_det()])
    app.dependency_overrides[get_storage] = lambda: storage
    app.dependency_overrides[get_detector] = lambda: detector

    # 大小上限测试要动 settings；lru_cache 返回同一对象，测完还原
    s = get_settings()
    original_max = s.max_upload_mb

    with TestClient(app) as c:
        yield c, store, storage, detector, s
    s.max_upload_mb = original_max
    app.dependency_overrides.clear()


def _register(c, store, username="farmerdet"):
    c.post("/auth/sms/send", json={"phone": "13800000021"})
    code = store.get("sms:code:13800000021")
    resp = c.post("/auth/register", json={
        "username": username, "password": "s3cret-pw",
        "phone": "13800000021", "code": code,
    })
    assert resp.status_code == 201, resp.text
    return {"Authorization": f"Bearer {resp.json()['token']}"}


def test_upload_requires_auth(env):
    c, *_ = env
    assert c.post("/detections", files=JPEG_FILE).status_code in (401, 403)


def test_upload_success_returns_done_record(env):
    c, store, storage, _, _ = env
    headers = _register(c, store)
    resp = c.post("/detections", files=JPEG_FILE, headers=headers)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["status"] == "done"
    assert body["detections"][0]["chinese_name"] == "稻纵卷叶螟"
    assert body["error"] is None
    # 原图与标注图都进了存储
    assert len(storage.objects) == 2


def test_non_image_is_415_and_writes_nothing(env):
    c, store, storage, detector, _ = env
    headers = _register(c, store)
    resp = c.post("/detections", files=TEXT_FILE, headers=headers)
    assert resp.status_code == 415
    assert storage.objects == {}
    assert detector.called_with == []


def test_oversize_rejected_before_processing(env):
    c, store, storage, detector, s = env
    s.max_upload_mb = 0  # 任何带 size 的上传都超限
    headers = _register(c, store)
    resp = c.post("/detections", files=JPEG_FILE, headers=headers)
    assert resp.status_code == 413
    assert storage.objects == {}
    assert detector.called_with == []


def test_inference_failure_returns_failed_record(env):
    c, store, storage, detector, _ = env
    detector.error = RuntimeError("model exploded")
    headers = _register(c, store)
    resp = c.post("/detections", files=JPEG_FILE, headers=headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "failed"
    assert "model exploded" in body["error"]
    assert body["detections"] is None
    # 失败清理半成品：存储里只剩标注图没有、原图也删了
    assert storage.objects == {}
