import logging
from pathlib import Path
from pydantic_settings import BaseSettings
from app.utils.paths import Paths

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    APP_NAME: str = "Crop Guard Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    HOST: str = "0.0.0.0"
    PORT: int = 8081

    STATIC_DIR: str = str(Paths.static())
    UPLOAD_DIR: str = str(Paths.uploads())
    RESULT_DIR: str = str(Paths.results())
    VIDEO_DIR: str = str(Paths.videos())
    RESULT_VIDEO_DIR: str = str(Paths.result_videos())
    VIDEO_MAX_SIZE: int = 200 * 1024 * 1024  # 200MB

    YOLO_MODEL_PATH: str = str(Paths.yolo_model())
    MODEL_DIR: str = str(Paths.models_dir())
    CONFIDENCE_THRESHOLD: float = 0.5
    IOU_THRESHOLD: float = 0.45

    # 数据库配置
    DB_HOST: str = "localhost"
    DB_PORT: int = 5433
    DB_USER: str = "crop_user"
    DB_PASSWORD: str = "crop_password"
    DB_NAME: str = "crop_guard_db"

    # JWT配置
    JWT_SECRET_KEY: str = "crop-guard-secret-key-change-in-production"
    JWT_EXPIRE_MINUTES: int = 1440  # 24小时

    CORS_ORIGINS: list = ["http://localhost:5174", "http://localhost:3000"]

    # MinIO 配置
    MINIO_ENDPOINT: str = "localhost:9002"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "crop-guard-bucket"
    MINIO_SECURE: bool = False

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


# 安全凭据默认值列表（用于启动时检测）
_INSECURE_DEFAULTS = {
    "JWT_SECRET_KEY": "crop-guard-secret-key-change-in-production",
    "DB_PASSWORD": "crop_password",
    "MINIO_ACCESS_KEY": "minioadmin",
    "MINIO_SECRET_KEY": "minioadmin",
}


def _check_insecure_defaults(settings: Settings):
    """检测不安全的默认凭据并发出警告"""
    for field, default_val in _INSECURE_DEFAULTS.items():
        if getattr(settings, field) == default_val:
            logger.warning(
                "[安全警告] %s 使用了默认值，生产环境请通过 .env 文件覆盖", field
            )


settings = Settings()
_check_insecure_defaults(settings)
