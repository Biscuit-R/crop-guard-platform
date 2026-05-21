from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
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
    query = db.query(DetectionHistory).filter(DetectionHistory.user_id == current_user.id)

    total_detections = query.count()

    total_objects_result = db.query(
        func.coalesce(func.sum(DetectionHistory.total_objects), 0)
    ).filter(DetectionHistory.user_id == current_user.id).scalar()

    completed_count = query.filter(DetectionHistory.status == "completed").count()
    success_rate = round((completed_count / total_detections * 100), 1) if total_detections > 0 else 0.0

    active_days = db.query(
        func.count(func.distinct(func.date(DetectionHistory.created_at)))
    ).filter(DetectionHistory.user_id == current_user.id).scalar()

    return DashboardStats(
        total_detections=total_detections,
        total_objects=int(total_objects_result),
        success_rate=success_rate,
        active_days=active_days or 0,
    )
