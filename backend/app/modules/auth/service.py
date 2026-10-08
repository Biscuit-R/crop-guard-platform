"""账号业务编排。Redis 依赖按原语注入（FakeRedis 可替）—— 这是本模块可测的关键。"""

import secrets

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.auth.models import User
from app.modules.auth.security import (
    TokenError,
    create_token,
    decode_token,
    hash_password,
    verify_password,
)

_CODE_TTL_SECONDS = 300
_SEND_INTERVAL_SECONDS = 60
_LOGIN_LOCK_SECONDS = 900  # 锁定窗口 15 分钟

_GENERIC_LOGIN_ERROR = "用户名或密码错误"


class AuthError(Exception):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status


def decode_or_raise(token: str, secret: str) -> dict:
    try:
        return decode_token(token, secret)
    except TokenError as e:
        raise AuthError(str(e), status=401) from e


def decode_and_check_version(token: str, secret: str, db: Session) -> User:
    """验签 + 落库比对 token_version —— 服务端撤销语义的收口点。"""
    claims = decode_or_raise(token, secret)
    user = db.get(User, int(claims["sub"]))
    if user is None or user.token_version != claims["ver"]:
        raise AuthError("凭据已失效", status=401)
    return user


# ---- 短信验证码（真链路假网关：随机数生成 + Redis 管过期限次）----
# 演示模式（settings.sms_demo）下返回 code 给路由层随响应下发；真实网关接入后
# 这里改成调网关 API，code 只进 Redis 不出返回值。

def send_sms_code(redis, phone: str) -> str:
    interval_key = f"sms:interval:{phone}"
    if not redis.set(interval_key, "1", nx=True, ex=_SEND_INTERVAL_SECONDS):
        raise AuthError("发送太频繁，请稍后再试", status=429)
    code = f"{secrets.randbelow(1_000_000):06d}"
    redis.setex(f"sms:code:{phone}", _CODE_TTL_SECONDS, code)
    return code


def _consume_sms_code(redis, phone: str, code: str) -> None:
    stored = redis.get(f"sms:code:{phone}")
    if not stored or not secrets.compare_digest(str(code), str(stored)):
        raise AuthError("验证码错误或已过期")
    redis.delete(f"sms:code:{phone}")  # 一次性


# ---- 注册 / 登录 / 登出 / 改密 ----

def register(db: Session, redis, username: str, password: str, phone: str, code: str,
             secret: str, expire_minutes: int) -> tuple[User, str]:
    _consume_sms_code(redis, phone, code)
    exists = db.scalar(select(User).where(User.username == username))
    if exists is not None:
        raise AuthError("用户名已被占用", status=409)
    user = User(
        username=username,
        phone=phone,
        password_hash=hash_password(password),
        role="user",
    )
    db.add(user)
    db.commit()
    return user, create_token(user.id, user.role, user.token_version, secret, expire_minutes)


def login(db: Session, redis, username: str, password: str,
          secret: str, expire_minutes: int, max_attempts: int) -> tuple[User, str]:
    fail_key = f"login:fail:{username}"
    if int(redis.get(fail_key) or 0) >= max_attempts:
        raise AuthError("失败次数过多，账户已临时锁定", status=429)

    user = db.scalar(select(User).where(User.username == username))
    if user is None or not verify_password(password, user.password_hash):
        redis.incr(fail_key)
        redis.expire(fail_key, _LOGIN_LOCK_SECONDS)
        # 用户不存在与密码错误同一报错 —— 不给枚举用户名的口子
        raise AuthError(_GENERIC_LOGIN_ERROR, status=401)

    redis.delete(fail_key)  # 成功一次即清零
    return user, create_token(user.id, user.role, user.token_version, secret, expire_minutes)


def logout(db: Session, user: User) -> None:
    user.token_version += 1
    db.commit()


def change_password(db: Session, user: User, old_password: str, new_password: str) -> None:
    if not verify_password(old_password, user.password_hash):
        raise AuthError("原密码错误", status=401)
    user.password_hash = hash_password(new_password)
    user.token_version += 1  # 所有端立即失效
    db.commit()
