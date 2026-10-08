"""检测切片 · 编排测试（假件：FakeStorage / FakeDetector，不碰 MinIO/模型）。

验收语义在这里锁定：
- 类型按**内容嗅探**校验（不是扩展名）
- 推理成功 → 落库 done + 结果图入库
- 推理失败 → **也落库**（status=failed）+ **清理半成品**（原图删除，不留孤儿）
- 类别名走**名字映射**（handoff 3.1：索引映射会静默错 5 条）
"""

import io

import pytest

from app.modules.detection.service import (
    Detection,
    NotAnImage,
    submit_detection,
    sniff_image_type,
)

JPEG_MAGIC = b"\xff\xd8\xff" + b"\x00" * 32
PNG_MAGIC = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


class FakeStorage:
    def __init__(self):
        self.objects: dict[str, bytes] = {}
        self.deleted: list[str] = []

    def put(self, key: str, stream, length: int) -> None:
        self.objects[key] = stream.read()

    def get(self, key: str) -> bytes:
        return self.objects[key]

    def delete(self, key: str) -> None:
        self.objects.pop(key, None)
        self.deleted.append(key)


class FakeDetector:
    def __init__(self, detections=None, annotated=b"annotated-bytes", error=None):
        self.detections = detections or []
        self.annotated = annotated
        self.error = error
        self.called_with: list[bytes] = []

    def detect(self, image: bytes):
        self.called_with.append(image)
        if self.error:
            raise self.error
        return self.detections, self.annotated


@pytest.fixture()
def db(sqlite_db):
    return sqlite_db


@pytest.fixture()
def sqlite_db():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    from app.db.session import Base
    import app.modules.auth.models  # noqa: F401 —— user_id 外键目标
    import app.modules.detection.models  # noqa: F401 —— 确保 metadata 里有表

    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, future=True)()
    yield session
    session.close()


# ---- 内容嗅探 ----

def test_sniff_jpeg():
    assert sniff_image_type(io.BytesIO(JPEG_MAGIC)) == "jpeg"


def test_sniff_png():
    assert sniff_image_type(io.BytesIO(PNG_MAGIC)) == "png"


def test_sniff_rejects_text_and_garbage():
    assert sniff_image_type(io.BytesIO(b"hello world, not an image at all")) is None


def test_sniff_accepts_stream_of_any_size():
    """200MB 上传的 RSS 验收靠流式 —— 嗅探只读头部，不把流读进内存。"""
    big = io.BytesIO(PNG_MAGIC + b"\x00" * (50 * 1024 * 1024))
    assert sniff_image_type(big) == "png"


# ---- 提交检测 ----

def _det(name="rice_leaf_roller", conf=0.91):
    return Detection(class_name=name, confidence=conf, bbox=[10.0, 20.0, 110.0, 220.0])


def test_submit_success_creates_done_record(db):
    storage, detector = FakeStorage(), FakeDetector(detections=[_det()])
    record = submit_detection(db, storage, detector, user_id=7,
                              image=io.BytesIO(JPEG_MAGIC), length=len(JPEG_MAGIC))
    assert record.status == "done"
    assert record.user_id == 7
    assert record.image_key in storage.objects
    assert record.result_key in storage.objects
    assert storage.objects[record.result_key] == b"annotated-bytes"
    assert record.detections == [
        {"class_name": "rice_leaf_roller", "chinese_name": "稻纵卷叶螟",
         "confidence": 0.91, "bbox": [10.0, 20.0, 110.0, 220.0]}
    ]


def test_detector_receives_uploaded_bytes(db):
    storage, detector = FakeStorage(), FakeDetector(detections=[_det()])
    submit_detection(db, storage, detector, user_id=1,
                     image=io.BytesIO(JPEG_MAGIC), length=len(JPEG_MAGIC))
    assert detector.called_with == [JPEG_MAGIC]


def test_submit_failure_records_and_cleans(db):
    storage = FakeStorage()
    detector = FakeDetector(error=RuntimeError("CUDA out of memory"))
    record = submit_detection(db, storage, detector, user_id=7,
                              image=io.BytesIO(JPEG_MAGIC), length=len(JPEG_MAGIC))
    assert record.status == "failed"
    assert "CUDA out of memory" in record.error
    assert record.result_key is None
    assert record.detections is None
    assert record.image_key in storage.deleted, "失败必须清理半成品（原图）"
    assert record.image_key not in storage.objects


def test_non_image_rejected_before_any_writes(db):
    storage, detector = FakeStorage(), FakeDetector(detections=[_det()])
    with pytest.raises(NotAnImage):
        submit_detection(db, storage, detector, user_id=1,
                         image=io.BytesIO(b"plain text"), length=10)
    assert storage.objects == {}, "非图片不得写进存储"
    assert detector.called_with == [], "非图片不得送进推理"
