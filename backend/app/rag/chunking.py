"""语料切分（D11）：一条语料 → 三块字段组，每块前缀【中文名·类型】。"""

from dataclasses import dataclass

TYPE_LABELS = {1: "认知", 2: "症状", 3: "防治"}

# chunk_type -> 组成该块的字段（顺序即拼接顺序）
FIELD_GROUPS = {
    1: ("description", "morphology", "host_plants"),
    2: ("damage_symptoms", "occurrence_period"),
    3: ("control_methods",),
}


@dataclass
class Chunk:
    pest_name: str
    chinese_name: str
    chunk_type: int
    content: str


def build_chunks(entries):
    """每条语料切 3 块；必填字段为空时显式报错，绝不产出空块。"""
    chunks = []
    for entry in entries:
        for ctype in (1, 2, 3):
            parts = []
            for field in FIELD_GROUPS[ctype]:
                value = (entry.get(field) or "").strip()
                if not value:
                    raise ValueError(
                        f"{entry.get('name')}: 字段 {field} 为空，拒绝产出空块"
                    )
                parts.append(value)
            prefix = f"【{entry['chinese_name']}·{TYPE_LABELS[ctype]}】"
            chunks.append(
                Chunk(
                    pest_name=entry["name"],
                    chinese_name=entry["chinese_name"],
                    chunk_type=ctype,
                    content=prefix + "；".join(parts),
                )
            )
    return chunks
