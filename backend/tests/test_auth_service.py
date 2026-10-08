"""账号切片 · 业务编排测试（SQLite 内存库 + FakeRedis，不碰真实 PG/Redis）。

验收语义在这里锁定：
- 注册必须先过短信验证码（真链路假网关，requirements「不做什么」）
- 登录连续失败 N 次 → 拒绝（Redis 计数）；成功一次即清零
- 改密 / 登出 → token_version +1 → 旧 token 立即失效
"""

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.db.session import Base
from app.modules.auth.models import User
from app.modules.auth import service
from app.modules.auth.service import AuthError

SECRET = "test-secret"
EXPIRE = 10
MAX_ATTEMPTS = 5


class FakeRedis:
    """字典版 Redis：只实现 service 用到的原语，语义对齐（TTL 到期即无）。"""

    def __init__(self):
        self.store: dict = {}
        self.ttls: dict = {}

    def setex(self, key, seconds, value):
        self.store[key] = str(value)
        self.ttls[key] = seconds

    def set(self, key, value, nx=False, ex=None):
        if nx and key in self.store:
            return False
        self.store[key] = str(value)
        if ex:
            self.ttls[key] = ex
        return True

    def get(self, key):
        return self.store.get(key)

    def incr(self, key):
        self.store[key] = str(int(self.store.get(key, "0")) + 1)
        return int(self.store[key])

    def expire(self, key, seconds):
        if key in self.store:
            self.ttls[key] = seconds

    def delete(self, key):
        self.store.pop(key, None)
        self.ttls.pop(key, None)


@pytest.fixture()
def redis():
    return FakeRedis()


@pytest.fixture()
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, future=True)
    session = factory()
    yield session
    session.close()


def _register_user(db, redis, username="farmer01", password="s3cret-pw", phone="13800000001") -> User:
    send_code_ok(redis, phone)
    return register_ok(db, redis, username, password, phone)


def send_code_ok(redis, phone):
    """从 FakeRedis 里取出刚发送的验证码（模拟用户收到短信）。"""
    service.send_sms_code(redis, phone)
    return redis.get(f"sms:code:{phone}")


def register_ok(db, redis, username, password, phone):
    code = redis.get(f"sms:code:{phone}")
    return service.register(db, redis, username, password, phone, code,
                            secret=SECRET, expire_minutes=EXPIRE)


# ---- 注册 ----

def test_register_creates_user_and_returns_token(db, redis):
    user, token = _register_user(db, redis)
    assert user.id is not None
    assert user.role == "user"
    assert not user.password_hash.startswith("s3cret")
    claims = service.decode_or_raise(token, SECRET)
    assert claims["sub"] == str(user.id)


def test_register_rejects_duplicate_username(db, redis):
    _register_user(db, redis, username="dup")
    with pytest.raises(AuthError):
        _register_user(db, redis, username="dup", phone="13800000002")


def test_register_rejects_wrong_sms_code(db, redis):
    service.send_sms_code(redis, "13800000003")
    with pytest.raises(AuthError):
        service.register(db, redis, "u3", "s3cret-pw", "13800000003", "000000",
                         secret=SECRET, expire_minutes=EXPIRE)


def test_sms_send_is_rate_limited_per_phone(redis):
    service.send_sms_code(redis, "13800000004")
    with pytest.raises(AuthError):
        service.send_sms_code(redis, "13800000004")


# ---- 登录 ----

def test_login_success_returns_token(db, redis):
    _register_user(db, redis)
    user, token = service.login(db, redis, "farmer01", "s3cret-pw",
                                secret=SECRET, expire_minutes=EXPIRE, max_attempts=MAX_ATTEMPTS)
    assert user.username == "farmer01"
    assert service.decode_or_raise(token, SECRET)["sub"] == str(user.id)


def test_login_wrong_password_counts_and_locks(db, redis):
    _register_user(db, redis)
    for _ in range(MAX_ATTEMPTS):
        with pytest.raises(AuthError):
            service.login(db, redis, "farmer01", "wrong", secret=SECRET,
                          expire_minutes=EXPIRE, max_attempts=MAX_ATTEMPTS)
    # 第 N+1 次：即使密码正确也拒绝 —— 连续失败 N 次后拒绝（验收标准）
    with pytest.raises(AuthError):
        service.login(db, redis, "farmer01", "s3cret-pw", secret=SECRET,
                      expire_minutes=EXPIRE, max_attempts=MAX_ATTEMPTS)


def test_login_success_resets_failure_counter(db, redis):
    _register_user(db, redis)
    for _ in range(MAX_ATTEMPTS - 1):
        with pytest.raises(AuthError):
            service.login(db, redis, "farmer01", "wrong", secret=SECRET,
                          expire_minutes=EXPIRE, max_attempts=MAX_ATTEMPTS)
    service.login(db, redis, "farmer01", "s3cret-pw", secret=SECRET,
                  expire_minutes=EXPIRE, max_attempts=MAX_ATTEMPTS)
    # 计数已清零：之后还能再错 N 次
    for _ in range(MAX_ATTEMPTS):
        with pytest.raises(AuthError):
            service.login(db, redis, "farmer01", "wrong", secret=SECRET,
                          expire_minutes=EXPIRE, max_attempts=MAX_ATTEMPTS)


def test_login_unknown_user_same_error_as_wrong_password(db, redis):
    """不泄露用户是否存在 —— 同一错误信息（枚举防护）。"""
    with pytest.raises(AuthError) as e1:
        service.login(db, redis, "nobody", "x", secret=SECRET,
                      expire_minutes=EXPIRE, max_attempts=MAX_ATTEMPTS)
    _register_user(db, redis)
    with pytest.raises(AuthError) as e2:
        service.login(db, redis, "farmer01", "wrong-pw", secret=SECRET,
                      expire_minutes=EXPIRE, max_attempts=MAX_ATTEMPTS)
    assert str(e1.value) == str(e2.value)


# ---- 改密 / 登出（token_version 撤销语义）----

def test_change_password_bumps_version_and_invalidates_old_token(db, redis):
    user, old_token = _register_user(db, redis)
    change_password_ok(db, redis, user, "s3cret-pw", "new-password-9")
    with pytest.raises(AuthError):
        service.decode_and_check_version(old_token, SECRET, db)
    user2, new_token = service.login(db, redis, "farmer01", "new-password-9", secret=SECRET,
                                     expire_minutes=EXPIRE, max_attempts=MAX_ATTEMPTS)
    assert user2.id == user.id
    service.decode_and_check_version(new_token, SECRET, db)  # 新 token 有效


def test_change_password_requires_old_password(db, redis):
    user, _ = _register_user(db, redis)
    with pytest.raises(AuthError):
        service.change_password(db, user, "wrong-old", "whatever-1")


def test_logout_bumps_version_and_invalidates_token(db, redis):
    user, token = _register_user(db, redis)
    service.logout(db, user)
    with pytest.raises(AuthError):
        service.decode_and_check_version(token, SECRET, db)


# ---- 辅助 ----

def change_password_ok(db, redis, user, old, new):
    service.change_password(db, user, old, new)


def test_password_stored_as_bcrypt_hash(db, redis):
    user, _ = _register_user(db, redis)
    assert user.password_hash.startswith("$2")
