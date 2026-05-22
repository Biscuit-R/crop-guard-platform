from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.db_models import User
from app.models.schemas import AdminUserUpdate, TokenResponse
from app.utils.auth_utils import get_current_admin

router = APIRouter(prefix="/admin", tags=["用户管理"])


@router.get("/users", response_model=TokenResponse)
async def list_users(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    users = db.query(User).order_by(User.id).all()
    return TokenResponse(
        success=True,
        message="获取成功",
        data={
            "users": [
                {
                    "id": u.id,
                    "username": u.username,
                    "email": u.email,
                    "role": u.role,
                    "is_active": u.is_active,
                    "created_at": u.created_at.isoformat(),
                }
                for u in users
            ]
        },
    )


@router.put("/users/{user_id}/role", response_model=TokenResponse)
async def update_user_role(
    user_id: int,
    body: AdminUserUpdate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能修改自己的角色")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    if body.role and body.role in ("admin", "user"):
        user.role = body.role
    db.commit()

    return TokenResponse(success=True, message="角色已更新")


@router.put("/users/{user_id}/status", response_model=TokenResponse)
async def update_user_status(
    user_id: int,
    body: AdminUserUpdate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能禁用自己的账户")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    if body.is_active is not None:
        user.is_active = body.is_active
        if not body.is_active:
            user.token_version = (user.token_version or 0) + 1
    db.commit()

    status_text = "启用" if user.is_active else "禁用"
    return TokenResponse(success=True, message=f"用户已{status_text}")


@router.delete("/users/{user_id}", response_model=TokenResponse)
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能删除自己的账户")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    db.delete(user)
    db.commit()

    return TokenResponse(success=True, message="用户已删除")
