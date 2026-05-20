"""
通用数据集格式转化工具
支持: VOC(XML) → YOLO(TXT), COCO(JSON) → YOLO(TXT), CSV → YOLO(TXT)

使用方法:
    python convert_dataset.py --input ./data --format voc --output ./yolo_data
    python convert_dataset.py --input ./data --format coco --output ./yolo_data
    python convert_dataset.py --input ./data --format csv --output ./yolo_data
"""
import argparse
import json
import os
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def parse_args():
    parser = argparse.ArgumentParser(description="数据集格式转化工具")
    parser.add_argument("--input", type=str, required=True, help="输入数据集目录")
    parser.add_argument("--format", type=str, required=True, choices=["voc", "coco", "csv"],
                        help="输入数据集格式")
    parser.add_argument("--output", type=str, default="yolo_dataset", help="输出目录")
    parser.add_argument("--classes", type=str, default=None, help="类别文件路径（可选）")
    parser.add_argument("--split", type=str, default="train", help="数据集划分（train/val/test）")
    return parser.parse_args()


def voc_to_yolo(xml_path: str, img_width: int, img_height: int, class_map: Dict[str, int]) -> List[str]:
    """将 VOC XML 标注转化为 YOLO TXT 格式

    Args:
        xml_path: XML 文件路径
        img_width: 图片宽度
        img_height: 图片高度
        class_map: 类别名 → 类别ID 映射

    Returns:
        YOLO 格式的标注行列表
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()

    yolo_lines = []
    for obj in root.findall("object"):
        class_name = obj.find("name").text
        if class_name not in class_map:
            print(f"  警告: 未知类别 '{class_name}'，跳过")
            continue

        class_id = class_map[class_name]
        bbox = obj.find("bndbox")
        xmin = float(bbox.find("xmin").text)
        ymin = float(bbox.find("ymin").text)
        xmax = float(bbox.find("xmax").text)
        ymax = float(bbox.find("ymax").text)

        # 转化为 YOLO 格式 (归一化中心点坐标)
        x_center = ((xmin + xmax) / 2) / img_width
        y_center = ((ymin + ymax) / 2) / img_height
        width = (xmax - xmin) / img_width
        height = (ymax - ymin) / img_height

        # 确保值在 0-1 范围内
        x_center = max(0, min(1, x_center))
        y_center = max(0, min(1, y_center))
        width = max(0, min(1, width))
        height = max(0, min(1, height))

        yolo_lines.append(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}")

    return yolo_lines


def coco_to_yolo(annotation: dict, img_width: int, img_height: int, class_map: Dict[int, int]) -> List[str]:
    """将 COCO 标注转化为 YOLO TXT 格式

    Args:
        annotation: COCO 标注字典
        img_width: 图片宽度
        img_height: 图片高度
        class_map: COCO category_id → YOLO class_id 映射

    Returns:
        YOLO 格式的标注行列表
    """
    yolo_lines = []
    for ann in annotation:
        category_id = ann["category_id"]
        if category_id not in class_map:
            print(f"  警告: 未知类别 ID '{category_id}'，跳过")
            continue

        class_id = class_map[category_id]
        bbox = ann["bbox"]  # [x, y, width, height] (绝对坐标)

        # 转化为 YOLO 格式 (归一化中心点坐标)
        x_center = (bbox[0] + bbox[2] / 2) / img_width
        y_center = (bbox[1] + bbox[3] / 2) / img_height
        width = bbox[2] / img_width
        height = bbox[3] / img_height

        # 确保值在 0-1 范围内
        x_center = max(0, min(1, x_center))
        y_center = max(0, min(1, y_center))
        width = max(0, min(1, width))
        height = max(0, min(1, height))

        yolo_lines.append(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}")

    return yolo_lines


def convert_voc(input_dir: str, output_dir: str, split: str, class_map: Dict[str, int]):
    """转化 VOC 格式数据集

    Expected structure:
        input_dir/
            Annotations/  (XML files)
            JPEGImages/   (image files)
    """
    ann_dir = os.path.join(input_dir, "Annotations")
    img_dir = os.path.join(input_dir, "JPEGImages")

    if not os.path.exists(ann_dir) or not os.path.exists(img_dir):
        print(f"错误: VOC 数据集结构不正确，需要 Annotations/ 和 JPEGImages/ 目录")
        return

    # 创建输出目录
    out_img_dir = os.path.join(output_dir, "images", split)
    out_lbl_dir = os.path.join(output_dir, "labels", split)
    os.makedirs(out_img_dir, exist_ok=True)
    os.makedirs(out_lbl_dir, exist_ok=True)

    # 支持的图片格式
    img_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}

    converted = 0
    skipped = 0

    for xml_file in Path(ann_dir).glob("*.xml"):
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()

            # 获取图片信息
            size = root.find("size")
            img_width = int(size.find("width").text)
            img_height = int(size.find("height").text)

            # 获取图片文件名
            filename = root.find("filename").text
            img_path = None

            # 查找图片文件
            for ext in img_extensions:
                candidate = os.path.join(img_dir, filename)
                if not os.path.splitext(filename)[1]:
                    candidate += ext
                if os.path.exists(candidate):
                    img_path = candidate
                    break

            if img_path is None:
                print(f"  警告: 找不到图片 {filename}，跳过")
                skipped += 1
                continue

            # 转化标注
            yolo_lines = voc_to_yolo(xml_file, img_width, img_height, class_map)

            if not yolo_lines:
                skipped += 1
                continue

            # 复制图片
            img_filename = os.path.basename(img_path)
            shutil.copy2(img_path, os.path.join(out_img_dir, img_filename))

            # 保存 YOLO 标注
            txt_filename = os.path.splitext(img_filename)[0] + ".txt"
            with open(os.path.join(out_lbl_dir, txt_filename), "w") as f:
                f.write("\n".join(yolo_lines) + "\n")

            converted += 1

        except Exception as e:
            print(f"  错误: 处理 {xml_file} 时出错: {e}")
            skipped += 1

    print(f"[VOC → YOLO] 转化完成: {converted} 张，跳过: {skipped} 张")


def convert_coco(input_dir: str, output_dir: str, split: str, class_map: Dict[int, int]):
    """转化 COCO 格式数据集

    Expected structure:
        input_dir/
            annotations.json  (或 instances_train2017.json 等)
            images/           (图片目录)
    """
    # 查找标注文件
    ann_file = None
    for f in os.listdir(input_dir):
        if f.endswith(".json") and ("annotation" in f.lower() or "instance" in f.lower()):
            ann_file = os.path.join(input_dir, f)
            break

    if ann_file is None:
        print(f"错误: 找不到 COCO 标注文件 (annotations.json)")
        return

    img_dir = os.path.join(input_dir, "images")
    if not os.path.exists(img_dir):
        # 尝试使用输入目录本身作为图片目录
        img_dir = input_dir

    # 加载标注
    with open(ann_file) as f:
        coco_data = json.load(f)

    # 创建图片ID → 图片信息映射
    img_map = {img["id"]: img for img in coco_data["images"]}

    # 创建图片ID → 标注列表映射
    ann_map = {}
    for ann in coco_data["annotations"]:
        img_id = ann["image_id"]
        if img_id not in ann_map:
            ann_map[img_id] = []
        ann_map[img_id].append(ann)

    # 创建输出目录
    out_img_dir = os.path.join(output_dir, "images", split)
    out_lbl_dir = os.path.join(output_dir, "labels", split)
    os.makedirs(out_img_dir, exist_ok=True)
    os.makedirs(out_lbl_dir, exist_ok=True)

    converted = 0
    skipped = 0

    for img_id, img_info in img_map.items():
        try:
            img_filename = img_info["file_name"]
            img_path = os.path.join(img_dir, img_filename)

            if not os.path.exists(img_path):
                print(f"  警告: 找不到图片 {img_filename}，跳过")
                skipped += 1
                continue

            img_width = img_info["width"]
            img_height = img_info["height"]

            # 获取该图片的标注
            annotations = ann_map.get(img_id, [])
            if not annotations:
                skipped += 1
                continue

            # 转化标注
            yolo_lines = coco_to_yolo(annotations, img_width, img_height, class_map)

            if not yolo_lines:
                skipped += 1
                continue

            # 复制图片
            shutil.copy2(img_path, os.path.join(out_img_dir, img_filename))

            # 保存 YOLO 标注
            txt_filename = os.path.splitext(img_filename)[0] + ".txt"
            with open(os.path.join(out_lbl_dir, txt_filename), "w") as f:
                f.write("\n".join(yolo_lines) + "\n")

            converted += 1

        except Exception as e:
            print(f"  错误: 处理图片 {img_id} 时出错: {e}")
            skipped += 1

    print(f"[COCO → YOLO] 转化完成: {converted} 张，跳过: {skipped} 张")


def convert_csv(input_dir: str, output_dir: str, split: str, class_map: Dict[str, int]):
    """转化 CSV 格式数据集

    Expected CSV format:
        filename,width,height,class,xmin,ymin,xmax,ymax
    """
    import csv

    # 查找 CSV 文件
    csv_file = None
    for f in os.listdir(input_dir):
        if f.endswith(".csv"):
            csv_file = os.path.join(input_dir, f)
            break

    if csv_file is None:
        print(f"错误: 找不到 CSV 标注文件")
        return

    img_dir = os.path.join(input_dir, "images")
    if not os.path.exists(img_dir):
        img_dir = input_dir

    # 创建输出目录
    out_img_dir = os.path.join(output_dir, "images", split)
    out_lbl_dir = os.path.join(output_dir, "labels", split)
    os.makedirs(out_img_dir, exist_ok=True)
    os.makedirs(out_lbl_dir, exist_ok=True)

    # 按图片分组标注
    img_annotations = {}
    with open(csv_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            filename = row["filename"]
            if filename not in img_annotations:
                img_annotations[filename] = {
                    "width": int(row["width"]),
                    "height": int(row["height"]),
                    "annotations": []
                }
            img_annotations[filename]["annotations"].append(row)

    converted = 0
    skipped = 0

    for filename, data in img_annotations.items():
        try:
            img_path = os.path.join(img_dir, filename)
            if not os.path.exists(img_path):
                print(f"  警告: 找不到图片 {filename}，跳过")
                skipped += 1
                continue

            img_width = data["width"]
            img_height = data["height"]

            yolo_lines = []
            for ann in data["annotations"]:
                class_name = ann["class"]
                if class_name not in class_map:
                    print(f"  警告: 未知类别 '{class_name}'，跳过")
                    continue

                class_id = class_map[class_name]
                xmin = float(ann["xmin"])
                ymin = float(ann["ymin"])
                xmax = float(ann["xmax"])
                ymax = float(ann["ymax"])

                # 转化为 YOLO 格式
                x_center = ((xmin + xmax) / 2) / img_width
                y_center = ((ymin + ymax) / 2) / img_height
                width = (xmax - xmin) / img_width
                height = (ymax - ymin) / img_height

                x_center = max(0, min(1, x_center))
                y_center = max(0, min(1, y_center))
                width = max(0, min(1, width))
                height = max(0, min(1, height))

                yolo_lines.append(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}")

            if not yolo_lines:
                skipped += 1
                continue

            # 复制图片
            shutil.copy2(img_path, os.path.join(out_img_dir, filename))

            # 保存 YOLO 标注
            txt_filename = os.path.splitext(filename)[0] + ".txt"
            with open(os.path.join(out_lbl_dir, txt_filename), "w") as f:
                f.write("\n".join(yolo_lines) + "\n")

            converted += 1

        except Exception as e:
            print(f"  错误: 处理 {filename} 时出错: {e}")
            skipped += 1

    print(f"[CSV → YOLO] 转化完成: {converted} 张，跳过: {skipped} 张")


def generate_data_yaml(output_dir: str, class_names: List[str], split: str = "train"):
    """生成 data.yaml 配置文件"""
    yaml_content = f"""path: ./{output_dir}
train: images/{split}
val: images/{split}

nc: {len(class_names)}

names:
"""
    for i, name in enumerate(class_names):
        yaml_content += f"  {i}: {name}\n"

    yaml_path = os.path.join(output_dir, "data.yaml")
    with open(yaml_path, "w", encoding="utf-8") as f:
        f.write(yaml_content)

    print(f"已生成配置文件: {yaml_path}")


def load_classes(classes_file: Optional[str]) -> List[str]:
    """加载类别列表"""
    if classes_file and os.path.exists(classes_file):
        with open(classes_file, encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    return []


def main():
    args = parse_args()

    print("=" * 50)
    print("  数据集格式转化工具")
    print("=" * 50)
    print(f"  输入目录: {args.input}")
    print(f"  输入格式: {args.format}")
    print(f"  输出目录: {args.output}")
    print(f"  数据划分: {args.split}")
    print("=" * 50)

    # 加载类别
    classes = load_classes(args.classes)
    if classes:
        print(f"  类别数量: {len(classes)}")
        class_map = {name: i for i, name in enumerate(classes)}
    else:
        print("  警告: 未指定类别文件，将自动从标注中提取")
        class_map = {}

    # 执行转化
    if args.format == "voc":
        if not class_map:
            print("错误: VOC 格式需要指定类别文件 (--classes)")
            return
        convert_voc(args.input, args.output, args.split, class_map)

    elif args.format == "coco":
        # 从 COCO 标注中提取类别
        ann_file = None
        for f in os.listdir(args.input):
            if f.endswith(".json") and ("annotation" in f.lower() or "instance" in f.lower()):
                ann_file = os.path.join(args.input, f)
                break

        if ann_file:
            with open(ann_file) as f:
                coco_data = json.load(f)
            coco_class_map = {cat["id"]: i for i, cat in enumerate(coco_data["categories"])}
            classes = [cat["name"] for cat in coco_data["categories"]]
            convert_coco(args.input, args.output, args.split, coco_class_map)
        else:
            print("错误: 找不到 COCO 标注文件")
            return

    elif args.format == "csv":
        if not class_map:
            print("错误: CSV 格式需要指定类别文件 (--classes)")
            return
        convert_csv(args.input, args.output, args.split, class_map)

    # 生成 data.yaml
    if classes:
        generate_data_yaml(args.output, classes, args.split)

    print()
    print("=" * 50)
    print("  转化完成！")
    print("=" * 50)
    print(f"  输出目录: {args.output}")
    print(f"  下一步: 修改 data.yaml 中的路径，然后运行训练")
    print(f"  python train.py --data {args.output}/data.yaml")


if __name__ == "__main__":
    main()
