"""账号切片 · 安全原语测试（哈希与 JWT，纯逻辑不碰 DB/Redis）。

凭据语义（D6）：PyJWT + 直接 bcrypt。token_version 是服务端撤销的机制——
改密 / 登出时 +1，携带旧 version 的 token 立即失效（验收：改密后所有端立即失效）。
"""

import pytest

from app.modules.auth.security import (
    TokenError,
    create_token,
    decode_token,
    hash_password,
    verify_password,
)

SECRET = "test-secret"


def test_password_hash_roundtrip():
    h = hash_password("s3cret-password")
    assert h != "s3cret-password"
    assert verify_password("s3cret-password", h)
    assert not verify_password("wrong-password", h)


def test_password_hash_is_salted():
    assert hash_password("same") != hash_password("same")


def test_token_roundtrip_carries_claims():
    token = create_token(user_id=42, role="user", token_version=3, secret=SECRET, expire_minutes=10)
    claims = decode_token(token, secret=SECRET)
    assert claims["sub"] == "42"
    assert claims["role"] == "user"
    assert claims["ver"] == 3


def test_expired_token_rejected():
    token = create_token(user_id=1, role="user", token_version=1, secret=SECRET, expire_minutes=-1)
    with pytest.raises(TokenError):
        decode_token(token, secret=SECRET)


def test_tampered_token_rejected():
    token = create_token(user_id=1, role="user", token_version=1, secret=SECRET, expire_minutes=10)
    with pytest.raises(TokenError):
        decode_token(token[:-4] + "aaaa", secret=SECRET)


def test_wrong_secret_rejected():
    token = create_token(user_id=1, role="user", token_version=1, secret=SECRET, expire_minutes=10)
    with pytest.raises(TokenError):
        decode_token(token, secret="other-secret")
