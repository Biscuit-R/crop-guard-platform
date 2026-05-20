"""
农作物害虫检测模型训练脚本
支持本地 GPU / Google Colab / 任意云 GPU 环境

使用方法:
    python train.py                        # 默认参数训练
    python train.py --epochs 50 --batch 8  # 自定义参数
"""
import argparse
import os
from ultralytics import YOLO


def parse_args():
    parser = argparse.ArgumentParser(description="Crop Guard - 害虫检测模型训练")
    parser.add_argument("--data", type=str, default="data.yaml", help="数据集配置文件路径")
    parser.add_argument("--model", type=str, default="yolo11n.pt", help="预训练模型路径")
    parser.add_argument("--epochs", type=int, default=100, help="训练轮数")
    parser.add_argument("--batch", type=int, default=16, help="批次大小")
    parser.add_argument("--imgsz", type=int, default=640, help="输入图片尺寸")
    parser.add_argument("--device", type=str, default="0", help="训练设备, 0=GPU, cpu=CPU")
    parser.add_argument("--workers", type=int, default=2, help="数据加载线程数")
    parser.add_argument("--patience", type=int, default=20, help="早停轮数")
    parser.add_argument("--project", type=str, default="runs/train", help="结果保存目录")
    parser.add_argument("--name", type=str, default="crop_guard_v1", help="实验名称")
    parser.add_argument("--lr", type=float, default=0.01, help="初始学习率")
    parser.add_argument("--resume", type=str, default=None, help="恢复训练的权重路径")
    return parser.parse_args()


def main():
    args = parse_args()

    print("=" * 50)
    print("  Crop Guard - 农作物害虫检测模型训练")
    print("=" * 50)
    print(f"  模型:     {args.model}")
    print(f"  数据集:   {args.data}")
    print(f"  轮数:     {args.epochs}")
    print(f"  批次:     {args.batch}")
    print(f"  图片尺寸: {args.imgsz}")
    print(f"  设备:     {args.device}")
    print(f"  早停:     {args.patience} 轮")
    print("=" * 50)

    # 检查 GPU
    import torch
    if torch.cuda.is_available():
        print(f"  GPU: {torch.cuda.get_device_name(0)}")
        print(f"  显存: {torch.cuda.get_device_properties(0).total_mem / 1024**3:.1f} GB")
    else:
        print("  警告: 未检测到 GPU，将使用 CPU 训练（速度很慢）")
    print("=" * 50)
    print()

    # 加载模型
    if args.resume:
        print(f"恢复训练: {args.resume}")
        model = YOLO(args.resume)
        model.resume = True
    else:
        print(f"加载预训练模型: {args.model}")
        model = YOLO(args.model)

    # 开始训练
    results = model.train(
        data=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        workers=args.workers,
        patience=args.patience,
        project=args.project,
        name=args.name,
        lr0=args.lr,
        save=True,
        save_period=10,  # 每 10 轮保存一次检查点
        verbose=True,
        seed=42,
        deterministic=True,
    )

    # 输出训练结果
    print()
    print("=" * 50)
    print("  训练完成！")
    print("=" * 50)
    print(f"  最佳权重: {args.project}/{args.name}/weights/best.pt")
    print(f"  最终权重: {args.project}/{args.name}/weights/last.pt")
    print()

    # 验证
    print("正在验证最佳模型...")
    metrics = model.val()
    print(f"  mAP50:   {metrics.box.map50:.4f}")
    print(f"  mAP50-95: {metrics.box.map:.4f}")
    print()

    # 导出提示
    best_path = os.path.join(args.project, args.name, "weights", "best.pt")
    print(f"将 {best_path} 复制到 backend/ 目录即可部署。")


if __name__ == "__main__":
    main()
