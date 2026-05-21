"""
本地训练脚本 - 自动使用项目 .venv 环境
直接运行: python train_local.py

功能：
1. 自动检测训练环境（GPU、数据集）
2. 执行 YOLO 模型训练
3. 自动版本管理（语义化版本 + 时间戳）
4. 训练完成后自动上传模型到 MinIO
5. 自动复制模型到 backend/models/
"""
import subprocess
import sys
import os
import shutil
import json
import argparse
from datetime import datetime

import platform

# 项目根目录（training 的父目录）
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRAINING_DIR = os.path.dirname(os.path.abspath(__file__))

# 根据平台选择 Python 路径
if platform.system() == "Windows":
    VENV_PYTHON = os.path.join(PROJECT_DIR, "backend", ".venv", "Scripts", "python.exe")
else:
    VENV_PYTHON = os.path.join(PROJECT_DIR, "backend", ".venv", "bin", "python")

DATA_YAML = os.path.join(TRAINING_DIR, "data.yaml")
DATASET_DIR = os.path.join(PROJECT_DIR, "database")


def get_default_config():
    """返回默认训练参数（避免模块级可变全局状态）"""
    return {
        "data": DATA_YAML,
        "model": os.path.join(PROJECT_DIR, "backend", "models", "yolo11n.pt"),
        "epochs": 100,
        "batch": 16,
        "imgsz": 640,
        "device": "0",       # "0" = GPU, "cpu" = CPU
        "workers": 2,
        "patience": 20,
        "project": os.path.join(TRAINING_DIR, "runs"),
        "name": "crop_guard",
        "lr0": 0.01,
        "save_period": 10,
    }


def parse_args():
    parser = argparse.ArgumentParser(description="Crop Guard - 本地训练脚本")
    parser.add_argument("--bump", type=str, default="patch", choices=["major", "minor", "patch"],
                        help="版本升级类型 (major/minor/patch)")
    parser.add_argument("--version", type=str, default=None, help="指定版本号 (如 v1.0.0)")
    parser.add_argument("--description", type=str, default="", help="版本描述")
    parser.add_argument("--no-upload", action="store_true", help="不上传到 MinIO")
    parser.add_argument("--epochs", type=int, default=None, help="覆盖训练轮数")
    parser.add_argument("--batch", type=int, default=None, help="覆盖批次大小")
    parser.add_argument("--device", type=str, default=None, help="覆盖训练设备")
    return parser.parse_args()


def check_env():
    """检查训练环境"""
    print("=" * 60)
    print("  本地训练环境检查")
    print("=" * 60)

    # 检查 Python
    if os.path.exists(VENV_PYTHON):
        print(f"  Python: {VENV_PYTHON}")
    else:
        print(f"  错误: 未找到 .venv，请先创建虚拟环境")
        sys.exit(1)

    # 检查数据集
    train_dir = os.path.join(DATASET_DIR, "images", "train")
    val_dir = os.path.join(DATASET_DIR, "images", "val")
    if os.path.exists(train_dir) and os.path.exists(val_dir):
        train_count = len(os.listdir(train_dir))
        val_count = len(os.listdir(val_dir))
        print(f"  训练集: {train_count} 张")
        print(f"  验证集: {val_count} 张")
    else:
        print(f"  错误: 未找到数据集 {DATASET_DIR}")
        sys.exit(1)

    # 检查 data.yaml
    if os.path.exists(DATA_YAML):
        print(f"  配置:   {DATA_YAML}")
    else:
        print(f"  错误: 未找到 {DATA_YAML}")
        sys.exit(1)

    # 检查 GPU
    try:
        result = subprocess.run(
            [VENV_PYTHON, "-c", "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A')"],
            capture_output=True, text=True
        )
        lines = result.stdout.strip().split("\n")
        if lines[0] == "True":
            print(f"  GPU:    {lines[1]}")
        else:
            print(f"  GPU:    未检测到，将使用 CPU（速度很慢）")
            confirm = input("  是否继续？(y/N): ")
            if confirm.lower() != "y":
                sys.exit(0)
    except Exception:
        print(f"  GPU:    检测失败，跳过")

    print("=" * 60)
    print()


def upload_to_minio(model_path: str, version_info: dict, config: dict, metrics: dict = None):
    """
    上传模型到 MinIO

    Args:
        model_path: 模型文件路径
        version_info: 版本信息
        config: 训练配置
        metrics: 训练指标
    """
    try:
        # 添加 backend 到 Python 路径
        sys.path.insert(0, os.path.join(PROJECT_DIR, "backend"))

        from app.utils.minio_utils import get_minio_client

        print()
        print("=" * 60)
        print("  上传模型到 MinIO")
        print("=" * 60)

        minio = get_minio_client()

        # 准备元数据
        metadata = {
            "version": version_info["version"],
            "timestamp": version_info["timestamp"],
            "model_name": version_info.get("model_name", config["name"]),
            "description": version_info.get("description", ""),
            "training_config": {
                "epochs": config["epochs"],
                "batch": config["batch"],
                "imgsz": config["imgsz"],
                "device": config["device"],
                "lr0": config["lr0"],
                "patience": config["patience"],
            },
            "dataset": {
                "data_yaml": config["data"],
                "train_count": len(os.listdir(os.path.join(DATASET_DIR, "images", "train"))),
                "val_count": len(os.listdir(os.path.join(DATASET_DIR, "images", "val"))),
            },
            "metrics": metrics or {},
            "trained_at": datetime.now().isoformat(),
        }

        # 上传模型
        result = minio.upload_model(
            model_path=model_path,
            model_name=version_info.get("model_name", config["name"]),
            metadata=metadata,
        )

        print(f"  版本:     {version_info['version']}")
        print(f"  模型 URL: {result['model_url']}")
        if "metadata_url" in result:
            print(f"  元数据:   {result['metadata_url']}")
        print("=" * 60)

        return result

    except Exception as e:
        print(f"  上传失败: {e}")
        print("  提示: 请确保 MinIO 服务已启动 (docker-compose up -d minio)")
        return None


def deploy_model(best_path: str, version: str):
    """
    部署模型到 backend/models/

    Args:
        best_path: 最佳权重路径
        version: 版本号
    """
    deploy_dir = os.path.join(PROJECT_DIR, "backend", "models")
    os.makedirs(deploy_dir, exist_ok=True)

    # 部署带版本号的模型
    version_path = os.path.join(deploy_dir, f"best_{version}.pt")
    shutil.copy2(best_path, version_path)
    print(f"  版本模型: {version_path}")

    # 同时更新 best.pt（当前使用的模型）
    best_deploy = os.path.join(deploy_dir, "best.pt")
    shutil.copy2(best_path, best_deploy)
    print(f"  当前模型: {best_deploy}")


def main():
    args = parse_args()

    # 创建配置副本，避免修改模块级状态
    config = get_default_config()

    # 应用命令行参数覆盖
    if args.epochs:
        config["epochs"] = args.epochs
    if args.batch:
        config["batch"] = args.batch
    if args.device:
        config["device"] = args.device

    check_env()

    # 初始化版本管理
    sys.path.insert(0, TRAINING_DIR)
    from version_manager import get_version_manager

    version_mgr = get_version_manager()

    # 创建新版本
    version_info = version_mgr.create_version(
        version=args.version,
        bump_type=args.bump,
        description=args.description,
    )

    # 生成带版本号的模型名称
    model_name = version_mgr.get_model_name(version_info["version"])
    version_info["model_name"] = model_name

    print("训练参数:")
    print(f"  版本:   {version_info['version']}")
    print(f"  模型:   {config['model']}")
    print(f"  轮数:   {config['epochs']}")
    print(f"  批次:   {config['batch']}")
    print(f"  设备:   {config['device']}")
    print(f"  早停:   {config['patience']} 轮")
    print()
    print(f"结果保存: {config['project']}/{model_name}")
    print()
    print("开始训练...")
    print()

    from ultralytics import YOLO

    model = YOLO(config["model"])
    results = model.train(
        data=config["data"],
        epochs=config["epochs"],
        imgsz=config["imgsz"],
        batch=config["batch"],
        device=config["device"],
        workers=config["workers"],
        patience=config["patience"],
        project=config["project"],
        name=model_name,
        lr0=config["lr0"],
        save_period=config["save_period"],
        save=True,
        verbose=True,
        seed=42,
    )

    # 获取最佳权重路径
    best_path = os.path.join(config["project"], model_name, "weights", "best.pt")

    print()
    print("=" * 60)
    print("  训练完成！")
    print("=" * 60)
    print(f"  版本:     {version_info['version']}")
    print(f"  最佳权重: {best_path}")

    # 获取训练指标
    metrics = {}
    try:
        if hasattr(results, 'results_dict'):
            metrics = {
                "mAP50": results.results_dict.get("metrics/mAP50(B)", 0),
                "mAP50-95": results.results_dict.get("metrics/mAP50-95(B)", 0),
                "precision": results.results_dict.get("metrics/precision(B)", 0),
                "recall": results.results_dict.get("metrics/recall(B)", 0),
            }
    except Exception:
        pass

    # 更新版本信息
    version_info["metrics"] = metrics
    version_info["model_path"] = best_path

    # 部署模型到 backend
    if os.path.exists(best_path):
        deploy_model(best_path, version_info["version"])

        # 自动上传到 MinIO
        if not args.no_upload:
            upload_to_minio(best_path, version_info, config, metrics)
    else:
        print(f"  错误: 未找到最佳权重 {best_path}")

    # 显示版本历史
    print()
    print("=" * 60)
    print("  版本历史")
    print("=" * 60)
    versions = version_mgr.list_versions(5)
    for v in versions:
        print(f"  {v['version']} - {v['created_at'][:19]} - {v.get('description', '')[:30]}")
    print("=" * 60)


if __name__ == "__main__":
    main()
