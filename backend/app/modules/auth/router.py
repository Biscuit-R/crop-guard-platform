"""账号路由：短信 / 注册 / 登录 / 登出 / 改密 / 我的信息。

端点薄，业务在 service。HTTPException 映射是这里唯一的逻辑。
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.modules.auth import service
from app.modules.auth.deps import get_current_user, get_redis
from app.modules.auth.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


class PhoneIn(BaseModel):
    phone: str = Field(pattern=r"^1\d{10}$")


class RegisterIn(BaseModel):
    username: str = Field(min_length=3, max_length=32, pattern=r"^\w+$")
    password: str = Field(min_length=8, max_length=64)
    phone: str = Field(pattern=r"^1\d{10}$")
    code: str = Field(min_length=6, max_length=6)


class LoginIn(BaseModel):
    username: str
    password: str


class PasswordIn(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8, max_length=64)


def _raise(e: service.AuthError) -> None:
    raise HTTPException(e.status, str(e)) from e


def _user_out(user: User) -> dict:
    return {"id": user.id, "username": user.username, "role": user.role}


@router.post("/sms/send")
def send_sms(payload: PhoneIn, redis=Depends(get_redis)) -> dict:
    s = get_settings()
    try:
        code = service.send_sms_code(redis, payload.phone)
    except service.AuthError as e:
        _raise(e)
    # 演示模式：验证码随响应返回（前端弹窗展示）；生产关闭后 code 只在 Redis
    # 5 分钟过期，走真实短信网关下发
    return {"ok": True, **({"code": code} if s.sms_demo else {})}


@router.post("/register", status_code=201)
def register(payload: RegisterIn, db: Session = Depends(get_db), redis=Depends(get_redis)) -> dict:
    s = get_settings()
    try:
        user, token = service.register(db, redis, payload.username, payload.password,
                                       payload.phone, payload.code,
                                       secret=s.jwt_secret, expire_minutes=s.jwt_expire_minutes)
    except service.AuthError as e:
        _raise(e)
    return {"token": token, "user": _user_out(user)}


@router.post("/login")
def login(payload: LoginIn, db: Session = Depends(get_db), redis=Depends(get_redis)) -> dict:
    s = get_settings()
    try:
        user, token = service.login(db, redis, payload.username, payload.password,
                                    secret=s.jwt_secret, expire_minutes=s.jwt_expire_minutes,
                                    max_attempts=s.login_max_attempts)
    except service.AuthError as e:
        _raise(e)
    return {"token": token, "user": _user_out(user)}


@router.post("/logout")
def logout(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    service.logout(db, user)
    return {"ok": True}


@router.post("/password")
def change_password(payload: PasswordIn, user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)) -> dict:
    try:
        service.change_password(db, user, payload.old_password, payload.new_password)
    except service.AuthError as e:
        _raise(e)
    return {"ok": True}


@router.get("/me")
def me(user: User = Depends(get_current_user)) -> dict:
    return _user_out(user)
