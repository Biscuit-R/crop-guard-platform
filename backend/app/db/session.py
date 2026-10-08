"""数据库引擎与会话（同步栈，见 docs/decisions.md D3）。

注意：模块导入时就会建引擎，但**不会真的连库** —— SQLAlchemy 的引擎是惰性的。
所以单元测试不需要数据库也能跑（见 tests/test_health.py）。
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # 连接被中间件掐断后自动重连，避免拿到死连接
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    """所有 ORM 模型的基类。Alembic 从这里自动发现表结构。"""


def get_db() -> Generator[Session, None, None]:
    """FastAPI 依赖：每个请求一个会话，请求结束必定关闭。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
