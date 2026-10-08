"""本地 embedding（D7）：BGE-small-zh，CPU 足够，断网可重建索引。

维度 512 与 rebuild_index.DDL 的 vector(512) 绑定 —— 换模型必须同步改表。

HF_ENDPOINT 必须在**导入 sentence_transformers 之前**写入 os.environ：
huggingface_hub 在 import 时就固化了常量，之后设置无效。
配置链路：.env → pydantic Settings（hf_endpoint）→ 这里 → HF 库。
"""

import os

from app.core.config import get_settings

if get_settings().hf_endpoint:
    os.environ.setdefault("HF_ENDPOINT", get_settings().hf_endpoint)

from sentence_transformers import SentenceTransformer

MODEL_NAME = "BAAI/bge-small-zh-v1.5"


class BGEEncoder:
    dim = 512

    def __init__(self, model_name: str = MODEL_NAME):
        self._model = SentenceTransformer(model_name)

    def encode(self, texts: list[str]) -> list[list[float]]:
        # normalize=True：向量归一到单位球面，余弦相似度退化为内积，阈值才有稳定语义
        vectors = self._model.encode(
            texts, normalize_embeddings=True, show_progress_bar=False
        )
        return [v.tolist() for v in vectors]
