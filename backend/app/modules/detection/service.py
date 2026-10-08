"""检测业务编排：嗅探 → 存储 → 推理 → 落库。

- 类型按**内容嗅探**校验，只读头部字节（200MB 上传的 RSS 验收靠这个 + 上限检查）。
- 类别名走**名字映射**：模型输出的英文名 → 图鉴中文名（handoff 3.1：
  data.yaml 的 names 与语料索引错位，按索引映射会静默错 5 条）。
- 失败也落库（status=failed）+ 清理半成品（删原图，不留孤儿对象）。
"""

import uuid
from dataclasses import dataclass, asdict
from functools import lru_cache
from io import BytesIO

from sqlalchemy.orm import Session

from app.data.pest_database import PEST_DATABASE
from app.modules.detection.models import DetectionRecord

_MAGIC = {
    b"\xff\xd8\xff": "jpeg",
    b"\x89PNG\r\n\x1a\n": "png",
}


class NotAnImage(Exception):
    pass


@dataclass
class Detection:
    class_name: str
    confidence: float
    bbox: list[float]


def sniff_image_type(stream) -> str | None:
    """只读头部并 seek 回去 —— 不把流读进内存。"""
    head = stream.read(12)
    stream.seek(0)
    for magic, ftype in _MAGIC.items():
        if head.startswith(magic):
            return ftype
    return None


@lru_cache
def _chinese_names() -> dict[str, str]:
    return {e["name"]: e["chinese_name"] for e in PEST_DATABASE}


def submit_detection(db: Session, storage, detector, user_id: int,
                     image, length: int) -> DetectionRecord:
    ftype = sniff_image_type(image)
    if ftype is None:
        raise NotAnImage("文件内容不是 JPEG/PNG 图片")
    image_key = f"detections/{user_id}/{uuid.uuid4().hex}.{ftype}"

    record = DetectionRecord(user_id=user_id, status="pending", image_key=image_key)
    db.add(record)
    db.commit()

    storage.put(image_key, image, length)
    try:
        detections, annotated = detector.detect(storage.get(image_key))
    except Exception as e:
        record.status = "failed"
        record.error = str(e)[:512]
        db.commit()
        storage.delete(image_key)  # 清理半成品
        return record

    result_key = f"detections/{user_id}/{uuid.uuid4().hex}_result.jpg"
    storage.put(result_key, BytesIO(annotated), len(annotated))

    names = _chinese_names()
    record.status = "done"
    record.result_key = result_key
    record.detections = [
        {**asdict(d), "chinese_name": names.get(d.class_name, d.class_name)}
        for d in detections
    ]
    db.commit()
    return record


MAX_PAGE_SIZE = 100


def list_records(db: Session, user_id: int, page: int, page_size: int
                 ) -> tuple[list[DetectionRecord], int]:
    """固定两条 SQL（count + 一页），page_size 再大也不逐条查（无 N+1）。"""
    page_size = min(page_size, MAX_PAGE_SIZE)
    query = db.query(DetectionRecord).filter(
        DetectionRecord.user_id == user_id).order_by(DetectionRecord.id.desc())
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return items, total


def get_record(db: Session, user_id: int, record_id: int) -> DetectionRecord | None:
    """user_id 进 WHERE —— 别人的记录与不存在的记录同样返回 None → 404，不泄露存在性。"""
    return db.query(DetectionRecord).filter(
        DetectionRecord.id == record_id,
        DetectionRecord.user_id == user_id,
    ).first()


def delete_record(db: Session, storage, user_id: int, record_id: int) -> bool:
    record = get_record(db, user_id, record_id)
    if record is None:
        return False
    for key in (record.image_key, record.result_key):
        if key:
            storage.delete(key)
    db.delete(record)
    db.commit()
    return True
