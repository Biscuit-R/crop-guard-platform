"""FastAPI 依赖：Redis 客户端与当前用户。"""

from functools import lru_cache

import redis as redis_lib
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.modules.auth.models import User
from app.modules.auth.service import AuthError, decode_and_check_version

_bearer = HTTPBearer(auto_error=False)


@lru_cache
def get_redis() -> redis_lib.Redis:
    settings = get_settings()
    return redis_lib.Redis(
        host=settings.redis_host, port=settings.redis_port, db=settings.redis_db,
        decode_responses=True, socket_timeout=2,
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "缺少凭据")
    try:
        return decode_and_check_version(credentials.credentials, get_settings().jwt_secret, db)
    except AuthError as e:
        raise HTTPException(e.status, str(e)) from e
