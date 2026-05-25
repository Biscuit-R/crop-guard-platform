import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from app.config import settings
from app.database import engine, Base
from app.api.detection import router as detection_router
from app.api.auth import router as auth_router
from app.api.history import router as history_router
from app.api.dashboard import router as dashboard_router
from app.api.dataset import router as dataset_router
from app.api.admin import router as admin_router
from app.api.forum import router as forum_router
from app.utils.paths import Paths

import app.models.db_models  # noqa: F401

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def _run_migrations():
    """自动迁移：为已有表添加缺失的列"""
    with engine.connect() as conn:
        # users 表迁移
        for col, ddl in [
            ("token_version", "ALTER TABLE users ADD COLUMN token_version INTEGER NOT NULL DEFAULT 0"),
            ("role", "ALTER TABLE users ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'user'"),
            ("is_active", "ALTER TABLE users ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT true"),
        ]:
            result = conn.execute(text(
                "SELECT column_name FROM information_schema.columns "
                f"WHERE table_name='users' AND column_name='{col}'"
            ))
            if not result.fetchone():
                logger.info("[迁移] 添加 users.%s 列", col)
                conn.execute(text(ddl))
                conn.commit()

        # 首个用户自动升级为 admin
        result = conn.execute(text(
            "SELECT id, role FROM users ORDER BY id LIMIT 1"
        ))
        first = result.fetchone()
        if first and first[1] != "admin":
            logger.info("[迁移] 首个用户 id=%s 升级为 admin", first[0])
            conn.execute(text(f"UPDATE users SET role='admin' WHERE id={first[0]}"))
            conn.commit()

        # detection_history 表迁移（视频检测字段）
        for col, ddl in [
            ("media_type", "ALTER TABLE detection_history ADD COLUMN media_type VARCHAR(10) NOT NULL DEFAULT 'image'"),
            ("video_url", "ALTER TABLE detection_history ADD COLUMN video_url VARCHAR(500)"),
            ("result_video_url", "ALTER TABLE detection_history ADD COLUMN result_video_url VARCHAR(500)"),
            ("frame_count", "ALTER TABLE detection_history ADD COLUMN frame_count INTEGER"),
            ("fps", "ALTER TABLE detection_history ADD COLUMN fps DOUBLE PRECISION"),
            ("duration", "ALTER TABLE detection_history ADD COLUMN duration DOUBLE PRECISION"),
        ]:
            result = conn.execute(text(
                "SELECT column_name FROM information_schema.columns "
                f"WHERE table_name='detection_history' AND column_name='{col}'"
            ))
            if not result.fetchone():
                logger.info("[迁移] 添加 detection_history.%s 列", col)
                conn.execute(text(ddl))
                conn.commit()

        # forum_posts 表迁移（精选置顶字段）
        result = conn.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='forum_posts' AND column_name='is_pinned'"
        ))
        if not result.fetchone():
            logger.info("[迁移] 添加 forum_posts.is_pinned 列")
            conn.execute(text("ALTER TABLE forum_posts ADD COLUMN is_pinned BOOLEAN NOT NULL DEFAULT false"))
            conn.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Paths.init_all_dirs()
    Base.metadata.create_all(bind=engine)
    _run_migrations()

    from app.services.detection_service import detection_service
    status = detection_service.get_status()
    logger.info("[启动] 模型路径: %s", status['model_path'])
    logger.info("[启动] 模型版本: %s", status['model_version'])
    logger.info("[启动] 类别数量: %d", status['class_count'])
    logger.info("[启动] 加载状态: %s", '成功' if status['is_loaded'] else '失败')

    yield
    # Shutdown (if needed)


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="农作物病虫害检测平台后端API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=settings.STATIC_DIR), name="static")

app.include_router(detection_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(history_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(dataset_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(forum_router, prefix="/api")


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
