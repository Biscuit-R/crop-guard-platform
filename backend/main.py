from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.database import engine, Base
from app.api.detection import router as detection_router
from app.api.auth import router as auth_router
from app.api.history import router as history_router
from app.api.dashboard import router as dashboard_router
from app.api.dataset import router as dataset_router
from app.utils.file_utils import ensure_directories

import app.models.db_models  # noqa: F401

Base.metadata.create_all(bind=engine)

ensure_directories()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="农作物病虫害检测平台后端API"
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


@app.on_event("startup")
async def startup_event():
    from app.services.detection_service import detection_service
    status = detection_service.get_status()
    print(f"[启动] 模型路径: {status['model_path']}")
    print(f"[启动] 模型版本: {status['model_version']}")
    print(f"[启动] 类别数量: {status['class_count']}")
    print(f"[启动] 加载状态: {'成功' if status['is_loaded'] else '失败'}")


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
