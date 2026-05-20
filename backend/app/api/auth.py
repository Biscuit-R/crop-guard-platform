from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.db_models import User
from app.models.schemas import UserCreate, UserLogin, TokenResponse
from app.utils.auth_utils import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在",
        )

    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册",
        )

    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token({"sub": str(new_user.id)})

    return TokenResponse(
        success=True,
        message="注册成功",
        data={
            "token": token,
            "user": {
                "id": new_user.id,
                "username": new_user.username,
                "email": new_user.email,
            },
        },
    )


@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == user_data.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    if not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    token = create_access_token({"sub": str(user.id)})

    return TokenResponse(
        success=True,
        message="登录成功",
        data={
            "token": token,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
            },
        },
    )


@router.get("/me", response_model=TokenResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return TokenResponse(
        success=True,
        message="获取成功",
        data={
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "created_at": current_user.created_at.isoformat(),
        },
    )
