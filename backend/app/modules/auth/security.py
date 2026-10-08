"""安全原语（D6）：PyJWT 签发/校验 + 直接 bcrypt（无 passlib 层）。"""

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

_TOKEN_ALGO = "HS256"


class TokenError(Exception):
    """token 无效（过期 / 篡改 / 密钥不符 / 格式坏）。"""


def hash_password(plain: str) -> str:
    # bcrypt 只取前 72 字节；直接用库，无 passlib 的版本钉子问题（D6）
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def create_token(user_id: int, role: str, token_version: int, secret: str, expire_minutes: int) -> str:
    payload = {
        "sub": str(user_id),
        "role": role,
        "ver": token_version,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=expire_minutes),
    }
    return jwt.encode(payload, secret, algorithm=_TOKEN_ALGO)


def decode_token(token: str, secret: str) -> dict:
    try:
        return jwt.decode(token, secret, algorithms=[_TOKEN_ALGO])
    except jwt.PyJWTError as e:
        raise TokenError(f"token 无效：{e}") from e
