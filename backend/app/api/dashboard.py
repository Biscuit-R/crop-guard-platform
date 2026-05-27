from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date, distinct
from app.database import get_db
from app.models.db_models import User, DetectionHistory
from app.models.schemas import DashboardStats
from app.utils.auth_utils import get_current_user

router = APIRouter(prefix="/dashboard", tags=["数据看板"])


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    today = datetime.now(timezone.utc).date()

    # 全平台今日统计
    today_detections = db.query(DetectionHistory).filter(
        cast(DetectionHistory.created_at, Date) == today
    ).count()

    today_objects = db.query(
        func.coalesce(func.sum(DetectionHistory.total_objects), 0)
    ).filter(
        cast(DetectionHistory.created_at, Date) == today
    ).scalar()

    today_users = db.query(
        func.count(func.distinct(DetectionHistory.user_id))
    ).filter(
        cast(DetectionHistory.created_at, Date) == today
    ).scalar()

    total_users = db.query(User).count()

    # 当前用户个人统计
    user_records = db.query(DetectionHistory).filter(
        DetectionHistory.user_id == current_user.id
    )

    total_detections = user_records.count()

    total_objects = db.query(
        func.coalesce(func.sum(DetectionHistory.total_objects), 0)
    ).filter(
        DetectionHistory.user_id == current_user.id
    ).scalar()

    completed = user_records.filter(
        DetectionHistory.status == "completed"
    ).count()
    success_rate = round(completed / total_detections * 100, 1) if total_detections > 0 else 0

    active_days = db.query(
        func.count(func.distinct(cast(DetectionHistory.created_at, Date)))
    ).filter(
        DetectionHistory.user_id == current_user.id
    ).scalar()

    return DashboardStats(
        today_detections=today_detections,
        today_objects=int(today_objects),
        today_users=today_users or 0,
        total_users=total_users,
        total_detections=total_detections,
        total_objects=int(total_objects),
        success_rate=success_rate,
        active_days=active_days or 0,
    )
