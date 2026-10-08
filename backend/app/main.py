"""应用装配。

保持这个文件**极薄**：只做装配，不写业务。
业务逻辑属于 `modules/<切片>/`，路由汇总属于 `api.py`。
"""

from fastapi import FastAPI

from app.api import api_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title=settings.app_name, debug=settings.debug)
app.include_router(api_router)
