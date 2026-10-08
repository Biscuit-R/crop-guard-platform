"""切片 1 · 标准 2：切分函数的验收测试（D11 三块字段组 + 虫名·类型前缀）。

不碰数据库、不碰 embedding —— 切分是纯函数：输入语料 dict 列表，输出块列表。
字段装错块、前缀错、空块，任何一处失败都要在这里红，而不是等评测失分才被发现。
"""

import sys

from app.rag.chunking import build_chunks

# 语料里的一条达标条目（001 稻纵卷叶螟），字段值截取自真实语料
SAMPLE_ENTRY = {
    "name": "rice_leaf_roller",
    "chinese_name": "稻纵卷叶螟",
    "description": "水稻迁飞性重要害虫，幼虫纵卷叶片取食叶肉，严重影响光合作用",
    "host_plants": "水稻、稗草、马唐、游草等禾本科植物",
    "morphology": "成虫体长约10mm，翅展约20mm，淡黄褐色",
    "damage_symptoms": "幼虫吐丝纵卷叶片成圆筒状虫苞，形成白色条斑",
    "occurrence_period": "长江流域5-9月发生4-5代，6-7月为害最重",
    "control_methods": "①农业防治：合理施肥避免氮肥过多；②生物防治：释放赤眼蜂；③化学防治：卵孵化盛期喷施氯虫苯甲酰胺",
}


def test_builds_three_chunks_per_entry():
    chunks = build_chunks([SAMPLE_ENTRY])
    assert len(chunks) == 3
    assert sorted(c.chunk_type for c in chunks) == [1, 2, 3]


def test_prefix_is_name_and_type_label():
    chunks = build_chunks([SAMPLE_ENTRY])
    by_type = {c.chunk_type: c for c in chunks}
    assert by_type[1].content.startswith("【稻纵卷叶螟·认知】")
    assert by_type[2].content.startswith("【稻纵卷叶螟·症状】")
    assert by_type[3].content.startswith("【稻纵卷叶螟·防治】")


def test_field_groups_mapped_to_right_chunks():
    chunks = build_chunks([SAMPLE_ENTRY])
    by_type = {c.chunk_type: c for c in chunks}
    # 认知块：description + morphology + host_plants
    assert "水稻迁飞性重要害虫" in by_type[1].content
    assert "成虫体长约10mm" in by_type[1].content
    assert "禾本科植物" in by_type[1].content
    # 症状块：damage_symptoms + occurrence_period，且不含形态描述
    assert "圆筒状虫苞" in by_type[2].content
    assert "4-5代" in by_type[2].content
    assert "成虫体长约10mm" not in by_type[2].content
    # 防治块：control_methods
    assert "氯虫苯甲酰胺" in by_type[3].content
    assert "圆筒状虫苞" not in by_type[3].content


def test_metadata_carries_name_and_chinese_name():
    chunks = build_chunks([SAMPLE_ENTRY])
    assert all(c.pest_name == "rice_leaf_roller" for c in chunks)
    assert all(c.chinese_name == "稻纵卷叶螟" for c in chunks)


def test_no_empty_chunk_body():
    chunks = build_chunks([SAMPLE_ENTRY])
    for c in chunks:
        body = c.content.split("】", 1)[1]
        assert body.strip(), f"chunk_type={c.chunk_type} 正文为空"


def test_empty_required_field_raises():
    broken = dict(SAMPLE_ENTRY, damage_symptoms="")
    try:
        build_chunks([broken])
    except ValueError:
        pass
    else:
        raise AssertionError("必填字段为空时应显式报错，而不是产出空块")


def test_full_corpus_yields_306_chunks():
    from app.data.pest_database import PEST_DATABASE

    chunks = build_chunks(PEST_DATABASE)
    assert len(chunks) == len(PEST_DATABASE) * 3


def test_deterministic_output():
    from app.data.pest_database import PEST_DATABASE

    assert build_chunks(PEST_DATABASE) == build_chunks(PEST_DATABASE)
