from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.db_models import User, DetectionHistory
from app.models.schemas import HistoryListResponse, HistoryDetailItem, TokenResponse
from app.utils.auth_utils import get_current_user

router = APIRouter(prefix="/history", tags=["检测历史"])


@router.get("/list", response_model=HistoryListResponse)
async def get_history_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keyword: str = Query(None),
    status: str = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(DetectionHistory).filter(DetectionHistory.user_id == current_user.id)
    if keyword:
        query = query.filter(DetectionHistory.filename.ilike(f"%{keyword}%"))
    if status:
        query = query.filter(DetectionHistory.status == status)
    total = query.count()
    records = (
        query.order_by(DetectionHistory.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return HistoryListResponse(
        success=True,
        message="获取成功",
        data=[HistoryDetailItem.model_validate(r) for r in records],
        total=total,
    )


@router.get("/{history_id}", response_model=HistoryDetailItem)
async def get_history_detail(
    history_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = (
        db.query(DetectionHistory)
        .filter(DetectionHistory.id == history_id, DetectionHistory.user_id == current_user.id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="记录不存在")
    return HistoryDetailItem.model_validate(record)


@router.delete("/{history_id}", response_model=TokenResponse)
async def delete_history(
    history_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = (
        db.query(DetectionHistory)
        .filter(DetectionHistory.id == history_id, DetectionHistory.user_id == current_user.id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="记录不存在")

    db.delete(record)
    db.commit()
    return TokenResponse(success=True, message="删除成功")


class BatchDeleteRequest(BaseModel):
    ids: List[int]


@router.post("/batch-delete", response_model=TokenResponse)
async def batch_delete_history(
    body: BatchDeleteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not body.ids:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="请提供要删除的记录ID")

    deleted = (
        db.query(DetectionHistory)
        .filter(DetectionHistory.id.in_(body.ids), DetectionHistory.user_id == current_user.id)
        .delete(synchronize_session=False)
    )
    db.commit()
    return TokenResponse(success=True, message=f"已删除 {deleted} 条记录")
