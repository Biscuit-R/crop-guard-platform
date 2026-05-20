"""
数据集转化 API
支持通过 Web 界面上传并转化数据集格式
"""
import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from app.utils.auth_utils import get_current_user
from app.models.db_models import User

router = APIRouter(prefix="/dataset", tags=["数据集工具"])

# 临时文件目录
TEMP_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "temp", "datasets")
os.makedirs(TEMP_DIR, exist_ok=True)


@router.post("/convert")
async def convert_dataset(
    file: UploadFile = File(..., description="数据集压缩包 (ZIP)"),
    format: str = Form(..., description="输入格式: voc / coco / csv"),
    classes: Optional[str] = Form(None, description="类别列表（每行一个）"),
    current_user: User = Depends(get_current_user),
):
    """
    上传数据集压缩包并转化为 YOLO 格式

    支持格式:
    - **voc**: Pascal VOC (XML 标注)
    - **coco**: Microsoft COCO (JSON 标注)
    - **csv**: CSV 格式

    返回转化后的 ZIP 压缩包下载链接
    """
    if format not in ["voc", "coco", "csv"]:
        raise HTTPException(status_code=400, detail="不支持的格式，请选择: voc / coco / csv")

    # 验证文件类型
    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="请上传 ZIP 压缩包")

    # 创建临时工作目录
    user_id = current_user.id
    work_dir = os.path.join(TEMP_DIR, str(user_id))
    os.makedirs(work_dir, exist_ok=True)

    try:
        # 保存上传文件
        zip_path = os.path.join(work_dir, file.filename)
        with open(zip_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # 解压
        extract_dir = os.path.join(work_dir, "extracted")
        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_dir)

        # 查找数据集目录（可能有一层嵌套）
        dataset_dir = extract_dir
        subdirs = os.listdir(extract_dir)
        if len(subdirs) == 1 and os.path.isdir(os.path.join(extract_dir, subdirs[0])):
            dataset_dir = os.path.join(extract_dir, subdirs[0])

        # 解析类别
        class_list = []
        if classes:
            class_list = [c.strip() for c in classes.split("\n") if c.strip()]

        # 执行转化
        output_dir = os.path.join(work_dir, "yolo_output")
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir)

        if format == "voc":
            if not class_list:
                raise HTTPException(status_code=400, detail="VOC 格式需要提供类别列表")
            converted = _convert_voc(dataset_dir, output_dir, class_list)
        elif format == "coco":
            converted, class_list = _convert_coco(dataset_dir, output_dir)
        elif format == "csv":
            if not class_list:
                raise HTTPException(status_code=400, detail="CSV 格式需要提供类别列表")
            converted = _convert_csv(dataset_dir, output_dir, class_list)

        if converted == 0:
            raise HTTPException(status_code=400, detail="转化失败：未找到有效的标注文件")

        # 生成 data.yaml
        _generate_data_yaml(output_dir, class_list)

        # 打包为 ZIP
        output_zip = os.path.join(work_dir, "yolo_dataset.zip")
        if os.path.exists(output_zip):
            os.remove(output_zip)

        with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(output_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, output_dir)
                    zipf.write(file_path, arcname)

        return {
            "message": f"转化成功！共转化 {converted} 张图片",
            "download_url": f"/api/dataset/download/{user_id}",
            "classes_count": len(class_list),
            "converted_count": converted,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"转化失败: {str(e)}")
    finally:
        # 清理上传的文件
        if os.path.exists(zip_path):
            os.remove(zip_path)


@router.get("/download/{user_id}")
async def download_converted_dataset(
    user_id: int,
    current_user: User = Depends(get_current_user),
):
    """下载转化后的数据集"""
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="无权访问")

    output_zip = os.path.join(TEMP_DIR, str(user_id), "yolo_dataset.zip")
    if not os.path.exists(output_zip):
        raise HTTPException(status_code=404, detail="未找到转化结果，请先上传数据集")

    return FileResponse(
        output_zip,
        media_type="application/zip",
        filename="yolo_dataset.zip",
    )


def _convert_voc(dataset_dir: str, output_dir: str, class_list: list) -> int:
    """转化 VOC 格式"""
    import xml.etree.ElementTree as ET

    ann_dir = os.path.join(dataset_dir, "Annotations")
    img_dir = os.path.join(dataset_dir, "JPEGImages")

    if not os.path.exists(ann_dir) or not os.path.exists(img_dir):
        raise HTTPException(status_code=400, detail="VOC 数据集需要 Annotations/ 和 JPEGImages/ 目录")

    class_map = {name: i for i, name in enumerate(class_list)}
    img_extensions = {".jpg", ".jpeg", ".png", ".bmp"}

    out_img_dir = os.path.join(output_dir, "images", "train")
    out_lbl_dir = os.path.join(output_dir, "labels", "train")
    os.makedirs(out_img_dir, exist_ok=True)
    os.makedirs(out_lbl_dir, exist_ok=True)

    converted = 0
    for xml_file in Path(ann_dir).glob("*.xml"):
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()

            size = root.find("size")
            img_width = int(size.find("width").text)
            img_height = int(size.find("height").text)

            filename = root.find("filename").text
            img_path = None
            for ext in img_extensions:
                candidate = os.path.join(img_dir, filename)
                if not os.path.splitext(filename)[1]:
                    candidate += ext
                if os.path.exists(candidate):
                    img_path = candidate
                    break

            if not img_path:
                continue

            yolo_lines = []
            for obj in root.findall("object"):
                class_name = obj.find("name").text
                if class_name not in class_map:
                    continue

                bbox = obj.find("bndbox")
                xmin = float(bbox.find("xmin").text)
                ymin = float(bbox.find("ymin").text)
                xmax = float(bbox.find("xmax").text)
                ymax = float(bbox.find("ymax").text)

                x_center = ((xmin + xmax) / 2) / img_width
                y_center = ((ymin + ymax) / 2) / img_height
                width = (xmax - xmin) / img_width
                height = (ymax - ymin) / img_height

                yolo_lines.append(f"{class_map[class_name]} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}")

            if yolo_lines:
                img_filename = os.path.basename(img_path)
                shutil.copy2(img_path, os.path.join(out_img_dir, img_filename))
                txt_filename = os.path.splitext(img_filename)[0] + ".txt"
                with open(os.path.join(out_lbl_dir, txt_filename), "w") as f:
                    f.write("\n".join(yolo_lines) + "\n")
                converted += 1
        except Exception:
            continue

    return converted


def _convert_coco(dataset_dir: str, output_dir: str) -> tuple:
    """转化 COCO 格式"""
    import json

    ann_file = None
    for f in os.listdir(dataset_dir):
        if f.endswith(".json"):
            ann_file = os.path.join(dataset_dir, f)
            break

    if not ann_file:
        raise HTTPException(status_code=400, detail="找不到 COCO 标注文件 (.json)")

    img_dir = os.path.join(dataset_dir, "images")
    if not os.path.exists(img_dir):
        img_dir = dataset_dir

    with open(ann_file) as f:
        coco_data = json.load(f)

    class_map = {cat["id"]: i for i, cat in enumerate(coco_data["categories"])}
    class_list = [cat["name"] for cat in coco_data["categories"]]
    img_map = {img["id"]: img for img in coco_data["images"]}

    ann_map = {}
    for ann in coco_data["annotations"]:
        img_id = ann["image_id"]
        if img_id not in ann_map:
            ann_map[img_id] = []
        ann_map[img_id].append(ann)

    out_img_dir = os.path.join(output_dir, "images", "train")
    out_lbl_dir = os.path.join(output_dir, "labels", "train")
    os.makedirs(out_img_dir, exist_ok=True)
    os.makedirs(out_lbl_dir, exist_ok=True)

    converted = 0
    for img_id, img_info in img_map.items():
        try:
            img_filename = img_info["file_name"]
            img_path = os.path.join(img_dir, img_filename)

            if not os.path.exists(img_path):
                continue

            annotations = ann_map.get(img_id, [])
            if not annotations:
                continue

            yolo_lines = []
            for ann in annotations:
                class_id = class_map[ann["category_id"]]
                bbox = ann["bbox"]
                x_center = (bbox[0] + bbox[2] / 2) / img_info["width"]
                y_center = (bbox[1] + bbox[3] / 2) / img_info["height"]
                width = bbox[2] / img_info["width"]
                height = bbox[3] / img_info["height"]
                yolo_lines.append(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}")

            if yolo_lines:
                shutil.copy2(img_path, os.path.join(out_img_dir, img_filename))
                txt_filename = os.path.splitext(img_filename)[0] + ".txt"
                with open(os.path.join(out_lbl_dir, txt_filename), "w") as f:
                    f.write("\n".join(yolo_lines) + "\n")
                converted += 1
        except Exception:
            continue

    return converted, class_list


def _convert_csv(dataset_dir: str, output_dir: str, class_list: list) -> int:
    """转化 CSV 格式"""
    import csv

    csv_file = None
    for f in os.listdir(dataset_dir):
        if f.endswith(".csv"):
            csv_file = os.path.join(dataset_dir, f)
            break

    if not csv_file:
        raise HTTPException(status_code=400, detail="找不到 CSV 标注文件")

    img_dir = os.path.join(dataset_dir, "images")
    if not os.path.exists(img_dir):
        img_dir = dataset_dir

    class_map = {name: i for i, name in enumerate(class_list)}

    out_img_dir = os.path.join(output_dir, "images", "train")
    out_lbl_dir = os.path.join(output_dir, "labels", "train")
    os.makedirs(out_img_dir, exist_ok=True)
    os.makedirs(out_lbl_dir, exist_ok=True)

    img_annotations = {}
    with open(csv_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            filename = row["filename"]
            if filename not in img_annotations:
                img_annotations[filename] = {
                    "width": int(row["width"]),
                    "height": int(row["height"]),
                    "annotations": [],
                }
            img_annotations[filename]["annotations"].append(row)

    converted = 0
    for filename, data in img_annotations.items():
        try:
            img_path = os.path.join(img_dir, filename)
            if not os.path.exists(img_path):
                continue

            yolo_lines = []
            for ann in data["annotations"]:
                class_name = ann["class"]
                if class_name not in class_map:
                    continue

                xmin = float(ann["xmin"])
                ymin = float(ann["ymin"])
                xmax = float(ann["xmax"])
                ymax = float(ann["ymax"])

                x_center = ((xmin + xmax) / 2) / data["width"]
                y_center = ((ymin + ymax) / 2) / data["height"]
                width = (xmax - xmin) / data["width"]
                height = (ymax - ymin) / data["height"]

                yolo_lines.append(f"{class_map[class_name]} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}")

            if yolo_lines:
                shutil.copy2(img_path, os.path.join(out_img_dir, filename))
                txt_filename = os.path.splitext(filename)[0] + ".txt"
                with open(os.path.join(out_lbl_dir, txt_filename), "w") as f:
                    f.write("\n".join(yolo_lines) + "\n")
                converted += 1
        except Exception:
            continue

    return converted


def _generate_data_yaml(output_dir: str, class_list: list):
    """生成 data.yaml"""
    yaml_content = f"""path: .
train: images/train
val: images/train

nc: {len(class_list)}

names:
"""
    for i, name in enumerate(class_list):
        yaml_content += f"  {i}: {name}\n"

    with open(os.path.join(output_dir, "data.yaml"), "w", encoding="utf-8") as f:
        f.write(yaml_content)
