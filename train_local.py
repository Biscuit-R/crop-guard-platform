"""
本地训练脚本 - 自动使用项目 .venv 环境
直接运行: python train_local.py
"""
import subprocess
import sys
import os

# 项目根目录
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_PYTHON = os.path.join(PROJECT_DIR, "backend", ".venv", "Scripts", "python.exe")
DATA_YAML = os.path.join(PROJECT_DIR, "data.yaml")
DATASET_DIR = os.path.join(PROJECT_DIR, "database")

# 训练参数
CONFIG = {
    "data": DATA_YAML,
    "model": "yolo11n.pt",
    "epochs": 100,
    "batch": 16,
    "imgsz": 640,
    "device": "0",       # "0" = GPU, "cpu" = CPU
    "workers": 2,
    "patience": 20,
    "project": os.path.join(PROJECT_DIR, "runs", "train"),
    "name": "crop_guard_local",
    "lr0": 0.01,
    "save_period": 10,
}


def check_env():
    """检查训练环境"""
    print("=" * 50)
    print("  本地训练环境检查")
    print("=" * 50)

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

    print("=" * 50)
    print()


def build_command():
    """构建训练命令"""
    cmd = [
        VENV_PYTHON, "-m", "ultralytics", "train",
        f"data={CONFIG['data']}",
        f"model={CONFIG['model']}",
        f"epochs={CONFIG['epochs']}",
        f"batch={CONFIG['batch']}",
        f"imgsz={CONFIG['imgsz']}",
        f"device={CONFIG['device']}",
        f"workers={CONFIG['workers']}",
        f"patience={CONFIG['patience']}",
        f"project={CONFIG['project']}",
        f"name={CONFIG['name']}",
        f"lr0={CONFIG['lr0']}",
        f"save_period={CONFIG['save_period']}",
        "save=True",
        "verbose=True",
        "seed=42",
    ]
    return cmd


def main():
    check_env()

    cmd = build_command()

    print("训练参数:")
    print(f"  模型:   {CONFIG['model']}")
    print(f"  轮数:   {CONFIG['epochs']}")
    print(f"  批次:   {CONFIG['batch']}")
    print(f"  设备:   {CONFIG['device']}")
    print(f"  早停:   {CONFIG['patience']} 轮")
    print()
    print(f"结果保存: {CONFIG['project']}/{CONFIG['name']}")
    print()
    print("开始训练...")
    print()

    # 执行训练
    result = subprocess.run(cmd, cwd=PROJECT_DIR)

    if result.returncode == 0:
        print()
        print("=" * 50)
        print("  训练完成！")
        print("=" * 50)
        best = os.path.join(CONFIG["project"], CONFIG["name"], "weights", "best.pt")
        print(f"  最佳权重: {best}")
        print(f"  部署: 复制 best.pt 到 backend/ 目录")
    else:
        print(f"\n训练失败，返回码: {result.returncode}")
        sys.exit(1)


if __name__ == "__main__":
    main()
