"""
农作物害虫检测模型训练脚本
支持本地 GPU / Google Colab / 任意云 GPU 环境

使用方法:
    python train.py                        # 默认参数训练（自动 patch 版本升级）
    python train.py --epochs 50 --batch 8  # 自定义参数
    python train.py --no-upload            # 训练后不上传到 MinIO
    python train.py --bump minor           # 次版本号升级
    python train.py --version v2.0.0       # 指定版本号
    python train.py --description "新增白粉病" --epochs 200
"""
import argparse
import os
import sys
import shutil
import json
from datetime import datetime
from ultralytics import YOLO

# 项目根目录
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRAINING_DIR = os.path.dirname(os.path.abspath(__file__))


def parse_args():
    parser = argparse.ArgumentParser(description="Crop Guard - 害虫检测模型训练")
    parser.add_argument("--data", type=str, default="data.yaml", help="数据集配置文件路径")
    parser.add_argument("--model", type=str, default="../backend/models/yolo11n.pt", help="预训练模型路径")
    parser.add_argument("--epochs", type=int, default=100, help="训练轮数")
    parser.add_argument("--batch", type=int, default=16, help="批次大小")
    parser.add_argument("--imgsz", type=int, default=640, help="输入图片尺寸")
    parser.add_argument("--device", type=str, default="0", help="训练设备, 0=GPU, cpu=CPU")
    parser.add_argument("--workers", type=int, default=2, help="数据加载线程数")
    parser.add_argument("--patience", type=int, default=20, help="早停轮数")
    parser.add_argument("--project", type=str, default="runs", help="结果保存目录")
    parser.add_argument("--lr", type=float, default=0.01, help="初始学习率")
    parser.add_argument("--resume", type=str, default=None, help="恢复训练的权重路径")
    parser.add_argument("--no-upload", action="store_true", help="训练后不上传到 MinIO")
    parser.add_argument("--deploy", type=str, default="../backend/models", help="模型部署目录")
    # 版本管理参数
    parser.add_argument("--bump", type=str, default="patch", choices=["major", "minor", "patch"],
                        help="版本升级类型 (major/minor/patch)")
    parser.add_argument("--version", type=str, default=None, help="指定版本号 (如 v2.0.0)")
    parser.add_argument("--description", type=str, default="", help="版本描述")
    return parser.parse_args()


def upload_to_minio(model_path: str, version_info: dict, args, metrics: dict = None):
    """
    上传模型到 MinIO

    Args:
        model_path: 模型文件路径
        version_info: 版本信息
        args: 训练参数
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

        # 统计数据集信息
        train_count = 0
        val_count = 0
        try:
            data_dir = os.path.dirname(os.path.abspath(args.data))
            train_dir = os.path.join(data_dir, "images", "train")
            val_dir = os.path.join(data_dir, "images", "val")
            if os.path.exists(train_dir):
                train_count = len(os.listdir(train_dir))
            if os.path.exists(val_dir):
                val_count = len(os.listdir(val_dir))
        except Exception:
            pass

        # 准备元数据
        metadata = {
            "version": version_info["version"],
            "timestamp": version_info["timestamp"],
            "model_name": version_info.get("model_name", "crop_guard"),
            "description": version_info.get("description", ""),
            "training_config": {
                "epochs": args.epochs,
                "batch": args.batch,
                "imgsz": args.imgsz,
                "device": args.device,
                "lr0": args.lr,
                "patience": args.patience,
            },
            "dataset": {
                "data_yaml": args.data,
                "train_count": train_count,
                "val_count": val_count,
            },
            "metrics": metrics or {},
            "trained_at": datetime.now().isoformat(),
        }

        # 上传模型
        result = minio.upload_model(
            model_path=model_path,
            model_name=version_info.get("model_name", "crop_guard"),
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


def deploy_model(best_path: str, deploy_dir: str, version: str):
    """
    部署模型到指定目录

    Args:
        best_path: 最佳权重路径
        deploy_dir: 部署目录
        version: 版本号
    """
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

    print("=" * 60)
    print("  Crop Guard - 农作物害虫检测模型训练")
    print("=" * 60)
    print(f"  版本:     {version_info['version']}")
    print(f"  模型:     {args.model}")
    print(f"  数据集:   {args.data}")
    print(f"  轮数:     {args.epochs}")
    print(f"  批次:     {args.batch}")
    print(f"  图片尺寸: {args.imgsz}")
    print(f"  设备:     {args.device}")
    print(f"  早停:     {args.patience} 轮")
    print()
    print(f"  结果保存: {args.project}/{model_name}")
    print("=" * 60)

    # 检查 GPU
    import torch
    if torch.cuda.is_available():
        print(f"  GPU: {torch.cuda.get_device_name(0)}")
        print(f"  显存: {torch.cuda.get_device_properties(0).total_mem / 1024**3:.1f} GB")
    else:
        print("  警告: 未检测到 GPU，将使用 CPU 训练（速度很慢）")
    print("=" * 60)
    print()

    # 加载模型
    if args.resume:
        print(f"恢复训练: {args.resume}")
        model = YOLO(args.resume)
    else:
        print(f"加载预训练模型: {args.model}")
        model = YOLO(args.model)

    # 开始训练
    train_kwargs = dict(
        data=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        workers=args.workers,
        patience=args.patience,
        project=args.project,
        name=model_name,
        lr0=args.lr,
        save=True,
        save_period=10,
        verbose=True,
        seed=42,
        deterministic=True,
    )
    if args.resume:
        train_kwargs["resume"] = True
    results = model.train(**train_kwargs)

    # 获取最佳权重路径
    best_path = os.path.join(args.project, model_name, "weights", "best.pt")

    # 输出训练结果
    print()
    print("=" * 60)
    print("  训练完成！")
    print("=" * 60)
    print(f"  版本:     {version_info['version']}")
    print(f"  最佳权重: {best_path}")
    print(f"  最终权重: {args.project}/{model_name}/weights/last.pt")

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

    # 验证（加载 best.pt 权重）
    print("正在验证最佳模型...")
    try:
        best_model = YOLO(best_path)
        val_metrics = best_model.val(
            data=args.data,
            imgsz=args.imgsz,
            batch=args.batch,
            device=args.device,
        )
        print(f"  mAP50:    {val_metrics.box.map50:.4f}")
        print(f"  mAP50-95: {val_metrics.box.map:.4f}")
        metrics["val_mAP50"] = val_metrics.box.map50
        metrics["val_mAP50-95"] = val_metrics.box.map
    except Exception as e:
        print(f"  验证失败: {e}")
    print()

    # 更新版本信息
    version_info["metrics"] = metrics
    version_info["model_path"] = best_path

    # 部署模型
    if os.path.exists(best_path):
        deploy_model(best_path, args.deploy, version_info["version"])

        # 自动上传到 MinIO
        if not args.no_upload:
            upload_to_minio(best_path, version_info, args, metrics)
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
