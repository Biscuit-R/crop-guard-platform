# Crop Guard Platform

农作物病虫害智能检测平台 — 基于 YOLO 的农作物病虫害识别与诊断系统

## 核心功能

- **病虫害检测**：上传农作物图片，AI 自动识别病虫害类型
- **检测历史**：记录所有检测结果，支持搜索和筛选
- **病虫害图鉴**：102 种常见农作物病虫害的详细资料
- **数据看板**：检测统计、趋势分析、快速预览

## 创新亮点

### 自动模型管理

训练完成后自动执行：
1. **模型部署**：自动复制 `best.pt` 到 `backend/models/`
2. **MinIO 上传**：自动上传模型和训练元数据到对象存储
3. **元数据记录**：保存训练参数、数据集信息、训练指标

```bash
# 训练并自动上传
python train.py

# 训练但不上传
python train.py --no-upload
```

### 智能模型加载

检测服务自动发现和加载最新模型，无需手动重启：

- **自动发现**：启动时扫描 `backend/models/`，按优先级选择（`best.pt` > 最新版本化模型 > 配置回退）
- **热重载**：每次检测前检查模型文件变更，自动切换到新模型
- **版本感知**：跟踪当前模型版本、文件修改时间、类别数量

```bash
# 查看当前模型状态
curl http://localhost:8081/api/detection/model/status

# 手动触发模型重载
curl -X POST http://localhost:8081/api/detection/model/reload
```

**模型加载优先级**：
| 优先级 | 文件 | 说明 |
|--------|------|------|
| 1 | `best.pt` | 训练脚本部署的当前模型 |
| 2 | `best_vX.X.X.pt` | 最新版本化模型（按修改时间） |
| 3 | `yolo11n.pt` | 配置文件中的默认模型 |

### API 模型版本管理

通过 REST API 管理和切换模型版本：

```bash
# 列出所有可用模型
curl http://localhost:8081/api/detection/models

# 切换到指定版本
curl -X POST http://localhost:8081/api/detection/models/switch \
  -H "Content-Type: application/json" \
  -d '{"version": "v1.0.0"}'

# 查看训练版本历史
curl http://localhost:8081/api/detection/models/history
```

**模型管理 API 一览**：
| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/detection/model/status` | 当前模型状态 |
| POST | `/api/detection/model/reload` | 重载当前模型 |
| GET | `/api/detection/models` | 列出所有可用模型 |
| POST | `/api/detection/models/switch` | 切换到指定版本 |
| GET | `/api/detection/models/history` | 训练版本历史 |

### 通用数据集转化工具

内置 `convert_dataset.py`，支持将主流格式自动转化为 YOLO 训练格式：

```bash
# VOC → YOLO (LabelImg 标注格式)
python convert_dataset.py --input ./voc_data --format voc --classes classes.txt --output ./yolo_data

# COCO → YOLO (Microsoft COCO 格式)
python convert_dataset.py --input ./coco_data --format coco --output ./yolo_data

# CSV → YOLO (自定义 CSV 格式)
python convert_dataset.py --input ./csv_data --format csv --classes classes.txt --output ./yolo_data
```

**支持的格式**：
| 格式 | 来源 | 标注文件 | 坐标格式 |
|------|------|----------|----------|
| YOLO | Ultralytics | `.txt` | 归一化中心点 (x, y, w, h) |
| VOC | Pascal VOC / LabelImg | `.xml` | 绝对坐标 (xmin, ymin, xmax, ymax) |
| COCO | Microsoft COCO | `.json` | 绝对坐标 (x, y, w, h) |
| CSV | 自定义 | `.csv` | 多种格式 |

**自动化流程**：
1. 自动识别输入格式
2. 自动转化标注格式
3. 自动复制图片文件
4. 自动生成 `data.yaml` 配置文件
5. 转化完成即可直接训练

## 技术栈

- **后端**：Python FastAPI + PostgreSQL + YOLO (ultralytics)
- **前端**：Vue 3 + Vite + Element Plus + Pinia
- **AI 模型**：YOLO11n (102 类农作物病虫害)
- **基础设施**：Docker Compose (PostgreSQL + Redis + MinIO)

## 快速启动

### 1. 启动基础设施

```bash
docker-compose up -d
```

### 2. 启动后端

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
python main.py
```

后端运行在 http://localhost:8081

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端运行在 http://localhost:5174

## 模型训练

### 数据集准备

将数据集放在 `database/` 目录，结构如下：

```
database/
├── images/
│   ├── train/    # 训练集图片
│   └── val/      # 验证集图片
└── labels/
    ├── train/    # 训练集标注 (YOLO 格式)
    └── val/      # 验证集标注 (YOLO 格式)
```

**标注格式**（每行一个目标）：
```
class_id x_center y_center width height
```
所有坐标值归一化到 0-1 范围。

### 本地训练

```bash
cd training

# 使用 GPU 训练（推荐，自动版本管理）
python train_local.py

# 自定义参数
python train.py --epochs 50 --batch 8 --device cpu

# 指定版本升级类型
python train.py --bump minor              # 次版本 v1.0.0 → v1.1.0
python train.py --bump major              # 主版本 v1.0.0 → v2.0.0

# 指定版本号
python train.py --version v2.0.0 --description "新增白粉病检测"

# 训练但不上传到 MinIO
python train.py --no-upload
```

**版本管理**：训练完成后自动执行：
1. 语义化版本命名（v1.0.0）
2. 自动部署带版本号的模型到 `backend/models/`
3. 自动上传模型 + 元数据到 MinIO
4. 记录训练指标（mAP50、precision、recall）

### 云端训练（推荐）

1. 上传 `database/`、`training/` 目录到云平台
2. 运行 `python train.py`
3. 下载 `best.pt` 放到 `backend/models/` 目录

**推荐平台**：
- Google Colab（免费 T4 GPU）
- AutoDL（国内 GPU 云平台）
- 阿里云 / 腾讯云 GPU 实例

### 使用转化工具

如果数据集不是 YOLO 格式：

```bash
cd training

# 1. 转化数据集
python convert_dataset.py --input ./your_data --format voc --classes classes.txt --output ../database

# 2. 开始训练
python train.py --data ../database/data.yaml
```

## 项目结构

```
crop-guard-platform/
├── backend/                    # 后端服务
│   ├── app/
│   │   ├── api/               # API 接口
│   │   ├── models/            # 数据库模型
│   │   ├── services/          # 业务逻辑
│   │   └── utils/             # 工具函数
│   ├── models/                # YOLO 模型文件
│   │   └── yolo11n.pt
│   ├── static/                # 静态文件
│   ├── main.py                # 后端入口
│   └── requirements.txt
├── frontend/                   # 前端应用
│   ├── src/
│   │   ├── api/               # API 调用
│   │   ├── components/        # 组件
│   │   ├── views/             # 页面
│   │   └── router/            # 路由
│   └── package.json
├── training/                   # 训练相关 ⭐
│   ├── train.py               # 通用训练脚本
│   ├── train_local.py         # 本地训练脚本
│   ├── train_colab.ipynb      # Colab 训练 notebook
│   ├── convert_dataset.py     # 数据集转化工具
│   ├── data.yaml              # 数据集配置
│   └── classes_example.txt    # 示例类别文件
├── database/                   # 数据集目录
├── docker-compose.yml          # 基础设施配置
├── ARCHITECTURE.md             # 架构文档
└── README.md
```

## 配置说明

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| 后端端口 | 8081 | FastAPI 服务端口 |
| 前端端口 | 5174 | Vite 开发服务器端口 |
| 数据库端口 | 5433 | PostgreSQL 端口 |
| Redis 端口 | 6380 | Redis 端口 |
| MinIO 端口 | 9002/9003 | MinIO API/控制台端口 |

## 许可证

MIT License
