import logging
import os
import uuid
import aiofiles
from fastapi import UploadFile, HTTPException
from app.config import settings

logger = logging.getLogger(__name__)

MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB


def ensure_directories():
    """保留兼容性，实际由 Paths.init_all_dirs() 处理"""
    from app.utils.paths import Paths
    Paths.init_all_dirs()


async def save_upload_file(file: UploadFile, directory: str) -> str:
    ext = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
    filename = f"temp_{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(directory, filename)

    size = 0
    async with aiofiles.open(file_path, "wb") as f:
        while chunk := await file.read(8192):
            size += len(chunk)
            if size > MAX_UPLOAD_SIZE:
                await f.close()
                os.remove(file_path)
                raise HTTPException(status_code=413, detail="文件大小超过限制 (最大 50MB)")
            await f.write(chunk)

    return filename


def get_file_url(filename: str, directory: str) -> str:
    """生成文件的可访问 URL 路径（相对于 /static 挂载点）"""
    # 从绝对路径中提取 static 之后的相对部分
    # 例如 E:\...\backend\static\uploads → /static/uploads
    static_dir = settings.STATIC_DIR.replace("\\", "/")
    dir_normalized = directory.replace("\\", "/")

    if dir_normalized.startswith(static_dir):
        relative = dir_normalized[len(static_dir):].lstrip("/")
        return f"/static/{relative}/{filename}"

    # 回退：直接用目录名
    dir_name = os.path.basename(directory)
    return f"/static/{dir_name}/{filename}"
