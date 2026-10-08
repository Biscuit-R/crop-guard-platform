"""路由汇总。

每个垂直切片在自己的 `modules/<name>/router.py` 里定义路由，
在这里挂上去。`main.py` 只认这一个 `api_router`。
"""

from fastapi import APIRouter

from app.modules.auth.router import router as auth_router
from app.modules.detection.router import router as detection_router
from app.modules.health.router import router as health_router
from app.modules.rag.router import router as rag_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(detection_router)
api_router.include_router(rag_router)
