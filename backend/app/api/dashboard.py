from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date
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

    # 今日检测次数（全平台）
    today_detections = db.query(DetectionHistory).filter(
        cast(DetectionHistory.created_at, Date) == today
    ).count()

    # 今日检测目标数
    today_objects = db.query(
        func.coalesce(func.sum(DetectionHistory.total_objects), 0)
    ).filter(
        cast(DetectionHistory.created_at, Date) == today
    ).scalar()

    # 今日活跃用户数
    today_users = db.query(
        func.count(func.distinct(DetectionHistory.user_id))
    ).filter(
        cast(DetectionHistory.created_at, Date) == today
    ).scalar()

    # 平台总用户数
    total_users = db.query(User).count()

    return DashboardStats(
        today_detections=today_detections,
        today_objects=int(today_objects),
        today_users=today_users or 0,
        total_users=total_users,
    )
