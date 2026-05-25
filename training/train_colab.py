# Google Colab 训练脚本
# 使用方法：
# 1. 上传 data_balanced.yaml 到 Colab
# 2. 上传数据库到 Google Drive
# 3. 运行此脚本

# ============ 安装依赖 ============
# !pip install ultralytics

# ============ 挂载 Google Drive ============
# from google.colab import drive
# drive.mount('/content/drive')

# ============ 训练配置 ============
from ultralytics import YOLO

# 数据集路径（修改为你的路径）
DATA_YAML = "/content/drive/MyDrive/crop-guard/database/data_balanced.yaml"

# 训练参数
MODEL_SIZE = "s"  # n=5.4MB, s=22MB, m=50MB, l=87MB, x=131MB
EPOCHS = 150
BATCH_SIZE = 16
IMG_SIZE = 640

# ============ 开始训练 ============
model = YOLO(f"yolo11{MODEL_SIZE}.pt")

results = model.train(
    data=DATA_YAML,
    epochs=EPOCHS,
    batch=BATCH_SIZE,
    imgsz=IMG_SIZE,
    device="0",  # GPU
    project="/content/drive/MyDrive/crop-guard/runs",
    name="train_balanced",
    exist_ok=True,
    # 优化器
    optimizer="AdamW",
    lr0=0.001,
    lrf=0.01,
    momentum=0.937,
    weight_decay=0.0005,
    warmup_epochs=5,
    # 数据增强
    hsv_h=0.015,
    hsv_s=0.7,
    hsv_v=0.4,
    degrees=10.0,
    translate=0.1,
    scale=0.5,
    shear=2.0,
    flipud=0.1,
    fliplr=0.5,
    mosaic=1.0,
    mixup=0.1,
    copy_paste=0.1,
    # 训练策略
    close_mosaic=20,
    amp=True,
    patience=30,
    save_period=10,
)

print("训练完成！")
print(f"最佳权重: /content/drive/MyDrive/crop-guard/runs/train_balanced/weights/best.pt")

# ============ 验证模型 ============
model = YOLO("/content/drive/MyDrive/crop-guard/runs/train_balanced/weights/best.pt")
results = model.val(data=DATA_YAML)
print(f"mAP50: {results.box.map50:.4f}")
print(f"mAP50-95: {results.box.map:.4f}")

# ============ 导出模型 ============
# model.export(format="onnx")  # 导出 ONNX 格式
