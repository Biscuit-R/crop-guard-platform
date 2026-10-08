"""检测路由：POST /detections（multipart 上传）→ 415 非图片 / 413 超限 / 200 结果。

storage 与 detector 通过依赖注入 —— 测试用 dependency_overrides 换假件，
路由层不依赖 MinIO/模型可测（假件形状差异单测锁不住的教训：接口以 service 签名为准）。
"""

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.modules.auth.deps import get_current_user
from app.modules.auth.models import User
from app.modules.detection.inference import get_detector
from app.modules.detection.models import DetectionRecord
from app.modules.detection.service import (
    NotAnImage,
    delete_record,
    get_record,
    list_records,
    submit_detection,
)
from app.modules.detection.storage import get_storage
from app.db.session import get_db

router = APIRouter(prefix="/detections", tags=["detection"])


@router.post("", status_code=201)
def create_detection(
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    storage=Depends(get_storage),
    detector=Depends(get_detector),
):
    data = image.file
    # 上限检查在嗅探之前：超限直接拒，不读内容
    if image.size is not None and image.size > get_settings().max_upload_mb * 1024 * 1024:
        raise HTTPException(413, "文件超过大小上限")
    try:
        record = submit_detection(db, storage, detector, user.id, data, image.size or 0)
    except NotAnImage as e:
        raise HTTPException(415, str(e)) from e
    return _record_out(record)


def _record_out(record: DetectionRecord) -> dict:
    return {
        "id": record.id,
        "status": record.status,
        "detections": record.detections,
        "error": record.error,
        "created_at": record.created_at.isoformat(),
    }


# ---- 检测历史 ----

@router.get("")
def list_detections(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if page < 1 or page_size < 1:
        raise HTTPException(422, "page / page_size 必须为正整数")
    items, total = list_records(db, user.id, page, page_size)
    return {"items": [_record_out(r) for r in items], "total": total,
            "page": page, "page_size": page_size}


@router.get("/{record_id}")
def get_detection(
    record_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    record = get_record(db, user.id, record_id)
    if record is None:  # 别人的 = 不存在的，统一 404
        raise HTTPException(404, "记录不存在")
    return _record_out(record)


@router.delete("/{record_id}", status_code=204)
def delete_detection(
    record_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    storage=Depends(get_storage),
):
    if not delete_record(db, storage, user.id, record_id):
        raise HTTPException(404, "记录不存在")
    return Response(status_code=204)


_CONTENT_TYPES = {"jpeg": "image/jpeg", "jpg": "image/jpeg", "png": "image/png"}


@router.get("/{record_id}/image")
def get_detection_image(
    record_id: int,
    variant: str = "original",
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    storage=Depends(get_storage),
):
    """MinIO 回源。variant=original 原图（按扩展名定类型）/ result 标注图（jpeg）。"""
    record = get_record(db, user.id, record_id)
    if record is None:
        raise HTTPException(404, "记录不存在")
    key = record.image_key if variant == "original" else record.result_key
    if not key:
        raise HTTPException(404, "该记录没有结果图")
    media_type = _CONTENT_TYPES.get(key.rsplit(".", 1)[-1].lower(),
                                    "application/octet-stream")
    if variant != "original":
        media_type = "image/jpeg"
    try:
        data = storage.get(key)
    except Exception as e:
        raise HTTPException(404, "存储对象不存在") from e
    return Response(content=data, media_type=media_type)


@router.get("/stats/summary")
def detection_stats(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """我的页统计卡。个人数据量级有限，Python 侧聚合（JSON 数组长度跨库函数不一致）。"""
    records = db.query(DetectionRecord).filter(
        DetectionRecord.user_id == user.id).all()
    total = len(records)
    done = [r for r in records if r.status == "done"]
    return {
        "total_detections": total,
        "total_objects": sum(len(r.detections or []) for r in done),
        "success_rate": round(len(done) / total * 100) if total else 0,
        "active_days": len({r.created_at.date() for r in records}),
    }
