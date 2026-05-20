import os
import uuid
import aiofiles
from fastapi import UploadFile
from app.config import settings


def ensure_directories():
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.RESULT_DIR, exist_ok=True)
    os.makedirs(settings.STATIC_DIR, exist_ok=True)


async def save_upload_file(file: UploadFile, directory: str) -> str:
    ext = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
    filename = f"temp_{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(directory, filename)

    async with aiofiles.open(file_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    return filename


def get_file_url(filename: str, directory: str) -> str:
    return f"http://localhost:{settings.PORT}/{directory}/{filename}"
