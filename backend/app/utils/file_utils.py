import logging
import os
import uuid
import aiofiles
from fastapi import UploadFile, HTTPException
from app.config import settings

logger = logging.getLogger(__name__)

MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB


def ensure_directories():
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.RESULT_DIR, exist_ok=True)
    os.makedirs(settings.STATIC_DIR, exist_ok=True)


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
    host = os.environ.get("API_HOST", f"localhost:{settings.PORT}")
    return f"http://{host}/{directory}/{filename}"
