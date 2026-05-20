"""
筛选数据集：只保留精选 30 类害虫对应的图片和标注，
并重新映射 class_id（原 ID → 新 ID 0-29）。
运行后生成 filtered_dataset/ 目录。
"""
import os
import shutil
from pathlib import Path

# 原始类别 ID → 新类别 ID 的映射
SELECTED_CLASSES = {
    0: 0,    # rice_leaf_roller
    1: 1,    # rice_leaf_caterpillar
    2: 2,    # paddy_stem_maggot
    3: 3,    # asiatic_rice_borer
    4: 4,    # yellow_rice_borer
    5: 5,    # rice_gall_midge
    6: 6,    # Rice_Stemfly
    7: 7,    # brown_plant_hopper
    8: 8,    # white_backed_plant_hopper
    9: 9,    # small_brown_plant_hopper
    10: 10,  # rice_water_weevil
    11: 11,  # rice_leafhopper
    22: 12,  # corn_borer
    23: 13,  # army_worm
    24: 14,  # aphids
    27: 15,  # english_grain_aphid
    18: 16,  # black_cutworm
    19: 17,  # large_cutworm
    20: 18,  # yellow_cutworm
    21: 19,  # red_spider
    15: 20,  # mole_cricket
    14: 21,  # grub
    16: 22,  # wireworm
    86: 23,  # Prodenia_litura
    39: 24,  # beet_army_worm
    38: 25,  # cabbage_army_worm
    37: 26,  # flea_beetle
    48: 27,  # Locustoidea
    51: 28,  # blister_beetle
    34: 29,  # wheat_sawfly
}

SRC_DIR = Path(__file__).parent
DST_DIR = SRC_DIR / "filtered_dataset"


def process_split(split: str):
    src_img_dir = SRC_DIR / "images" / split
    src_lbl_dir = SRC_DIR / "labels" / split
    dst_img_dir = DST_DIR / "images" / split
    dst_lbl_dir = DST_DIR / "labels" / split

    dst_img_dir.mkdir(parents=True, exist_ok=True)
    dst_lbl_dir.mkdir(parents=True, exist_ok=True)

    copied = 0
    skipped = 0

    for lbl_file in src_lbl_dir.glob("*.txt"):
        with open(lbl_file) as f:
            lines = f.readlines()

        new_lines = []
        for line in lines:
            parts = line.strip().split()
            if not parts:
                continue
            old_id = int(parts[0])
            if old_id in SELECTED_CLASSES:
                new_id = SELECTED_CLASSES[old_id]
                new_lines.append(f"{new_id} {' '.join(parts[1:])}")

        if new_lines:
            img_name = lbl_file.stem + ".jpg"
            src_img = src_img_dir / img_name
            if src_img.exists():
                shutil.copy2(src_img, dst_img_dir / img_name)
                with open(dst_lbl_dir / lbl_file.name, "w") as f:
                    f.write("\n".join(new_lines) + "\n")
                copied += 1
            else:
                skipped += 1
        else:
            skipped += 1

    print(f"[{split}] 保留 {copied} 张，跳过 {skipped} 张")


if __name__ == "__main__":
    print("开始筛选数据集...")
    print(f"源目录: {SRC_DIR}")
    print(f"目标目录: {DST_DIR}")
    print(f"精选类别: {len(SELECTED_CLASSES)} 类")
    print()

    process_split("train")
    process_split("val")

    print(f"\n筛选完成！数据集保存在: {DST_DIR}")
