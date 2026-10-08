"""MinIO 对象存储适配器。put 走流式 —— 200MB 上传不进内存（RSS 验收）。"""

from functools import lru_cache

import minio

from app.core.config import get_settings


class MinIOStorage:
    def __init__(self, endpoint: str, access_key: str, secret_key: str,
                 bucket: str, secure: bool = False):
        self._bucket = bucket
        self._client = minio.Minio(endpoint, access_key=access_key,
                                   secret_key=secret_key, secure=secure)
        if not self._client.bucket_exists(bucket):
            self._client.make_bucket(bucket)

    def put(self, key: str, stream, length: int) -> None:
        self._client.put_object(self._bucket, key, stream, length)

    def get(self, key: str) -> bytes:
        resp = self._client.get_object(self._bucket, key)
        try:
            return resp.read()
        finally:
            resp.close()
            resp.release_conn()

    def delete(self, key: str) -> None:
        self._client.remove_object(self._bucket, key)


def get_storage() -> MinIOStorage:
    """lru_cache 单例放 deps 会循环导入，这里就近提供。"""
    s = get_settings()
    return _cached_storage(s.minio_endpoint, s.minio_access_key, s.minio_secret_key,
                           s.minio_bucket, s.minio_secure)


@lru_cache
def _cached_storage(endpoint, access_key, secret_key, bucket, secure) -> MinIOStorage:
    return MinIOStorage(endpoint, access_key, secret_key, bucket, secure)
