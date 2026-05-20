from pydantic import BaseModel
import os


class Settings(BaseModel):
    APP_NAME: str = "Crop Guard Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    HOST: str = "0.0.0.0"
    PORT: int = 8081

    STATIC_DIR: str = "static"
    UPLOAD_DIR: str = "static/uploads"
    RESULT_DIR: str = "static/results"

    YOLO_MODEL_PATH: str = "models/yolo11n.pt"
    MODEL_DIR: str = "models"
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


def get_settings() -> Settings:
    settings = Settings()

    env_file = ".env"
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    if hasattr(settings, key):
                        try:
                            setattr(settings, key, type(getattr(settings, key))(value))
                        except ValueError:
                            pass

    return settings


settings = get_settings()
