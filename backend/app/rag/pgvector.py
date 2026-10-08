"""pgvector 字面量工具：Python 列表 → pgvector 的 '[1,2,...]' 文本格式。

rebuild_index（入库）与 retriever（查询向量）共用 —— 格式错一处两边就 dim 不匹配。
"""

from collections.abc import Sequence


def vector_literal(embedding: Sequence[float]) -> str:
    return "[" + ",".join(repr(float(x)) for x in embedding) + "]"
