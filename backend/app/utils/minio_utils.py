"""
MinIO 对象存储工具
用于上传和管理模型文件、训练结果等
"""
import logging
import os
import json
import threading
from datetime import datetime
from minio import Minio
from minio.error import S3Error
from app.config import settings

logger = logging.getLogger(__name__)


class MinioClient:
    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
        self.bucket = settings.MINIO_BUCKET
        self._ensure_bucket()

    def _ensure_bucket(self):
        """确保 bucket 存在"""
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
                logger.info("[MinIO] 创建 bucket: %s", self.bucket)
        except S3Error as e:
            logger.error("[MinIO] 错误: %s", e)

    def upload_file(self, local_path: str, object_name: str) -> str:
        """
        上传文件到 MinIO

        Args:
            local_path: 本地文件路径
            object_name: MinIO 中的对象名称

        Returns:
            文件的访问 URL
        """
        try:
            self.client.fput_object(
                self.bucket,
                object_name,
                local_path,
            )
            protocol = "https" if settings.MINIO_SECURE else "http"
            url = f"{protocol}://{settings.MINIO_ENDPOINT}/{self.bucket}/{object_name}"
            logger.info("[MinIO] 上传成功: %s", object_name)
            return url
        except S3Error as e:
            logger.error("[MinIO] 上传失败: %s", e)
            raise

    def upload_model(self, model_path: str, model_name: str, metadata: dict = None) -> dict:
        """
        上传模型文件和元数据

        Args:
            model_path: 模型文件路径
            model_name: 模型名称
            metadata: 训练元数据（参数、指标等）

        Returns:
            包含模型 URL 和元数据 URL 的字典
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_path = f"models/{model_name}/{timestamp}"

        # 上传模型文件
        model_object = f"{base_path}/best.pt"
        model_url = self.upload_file(model_path, model_object)

        # 上传元数据
        result = {
            "model_name": model_name,
            "model_url": model_url,
            "model_path": model_object,
            "uploaded_at": datetime.now().isoformat(),
        }

        if metadata:
            metadata["model_url"] = model_url
            metadata["uploaded_at"] = result["uploaded_at"]

            # 保存元数据到本地临时文件
            metadata_path = os.path.join(os.path.dirname(model_path), "metadata.json")
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            # 上传元数据
            metadata_object = f"{base_path}/metadata.json"
            metadata_url = self.upload_file(metadata_path, metadata_object)
            result["metadata_url"] = metadata_url
            result["metadata_path"] = metadata_object

            # 清理临时文件
            os.remove(metadata_path)

        logger.info("[MinIO] 模型上传完成: %s", base_path)
        return result

    def list_models(self, model_name: str = None) -> list:
        """
        列出已上传的模型

        Args:
            model_name: 模型名称（可选，用于过滤）

        Returns:
            模型列表
        """
        prefix = f"models/{model_name}/" if model_name else "models/"
        objects = self.client.list_objects(self.bucket, prefix=prefix, recursive=True)

        models = []
        for obj in objects:
            if obj.object_name.endswith("metadata.json"):
                try:
                    response = self.client.get_object(self.bucket, obj.object_name)
                    try:
                        metadata = json.loads(response.read().decode("utf-8"))
                        models.append(metadata)
                    finally:
                        response.close()
                        response.release_conn()
                except Exception as e:
                    logger.warning("[MinIO] 读取元数据失败: %s", e)

        return models

    def download_model(self, object_name: str, local_path: str) -> str:
        """
        下载模型文件

        Args:
            object_name: MinIO 中的对象名称
            local_path: 本地保存路径

        Returns:
            本地文件路径
        """
        try:
            self.client.fget_object(self.bucket, object_name, local_path)
            logger.info("[MinIO] 下载成功: %s", object_name)
            return local_path
        except S3Error as e:
            logger.error("[MinIO] 下载失败: %s", e)
            raise


# 全局客户端实例（线程安全）
_minio_client = None
_minio_lock = threading.Lock()


def get_minio_client() -> MinioClient:
    """获取 MinIO 客户端实例（线程安全的单例）"""
    global _minio_client
    if _minio_client is None:
        with _minio_lock:
            if _minio_client is None:
                try:
                    _minio_client = MinioClient()
                except Exception as e:
                    logger.error("[MinIO] 初始化失败: %s", e)
                    raise
    return _minio_client
