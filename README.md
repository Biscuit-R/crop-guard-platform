# Crop Guard Platform

农作物病虫害智能检测平台，基于 YOLO 的农作物病虫害识别与诊断系统。

## 核心功能

- **病虫害检测**：支持单图检测、批量检测、视频检测三种模式
- **视频分析**：自动抽帧检测，生成标注视频和病虫害统计摘要
- **检测历史**：记录所有检测结果，支持关键词搜索和状态筛选
- **病虫害图鉴**：102 种常见农作物病虫害的详细资料
- **数据看板**：检测统计、趋势分析、快速预览
- **用户管理**：admin/user 两级权限，支持角色切换、账户启禁用

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

## 检测功能

### 单图检测

上传一张农作物图片，AI 自动识别病虫害类型、位置和置信度。

### 批量检测

一次上传多张图片，系统逐张检测并返回结果。支持切换查看每张图片的检测详情。

### 视频检测

上传视频文件，系统自动抽帧检测（可配置帧间隔），输出带标注框的结果视频和病虫害统计摘要。

### 检测参数

- **置信度阈值**：可调节（10%~100%），控制检测灵敏度
- **模型切换**：支持多版本模型动态切换
- **视频抽帧间隔**：可配置每 N 帧检测一次

## 用户系统

### 角色权限

| 角色 | 权限 |
|------|------|
| admin | 全部功能 + 用户管理 |
| user | 检测 / 历史 / 图鉴 / 个人中心 |

首个注册用户自动成为管理员，后续注册默认为普通用户。

### 安全特性

- JWT 认证 + JTI 黑名单机制
- Token 版本控制（修改密码自动失效旧 token）
- 记住我功能（localStorage / sessionStorage）
- 路由守卫 + 管理员权限校验

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
│   ├── static/                # 静态文件
│   ├── main.py                # 后端入口
│   └── requirements.txt
├── frontend/                   # 前端应用
│   ├── src/
│   │   ├── api/               # API 调用
│   │   ├── components/        # 组件
│   │   ├── views/             # 页面
│   │   ├── stores/            # Pinia 状态管理
│   │   └── router/            # 路由
│   └── package.json
├── training/                   # 训练相关
│   ├── train.py               # 通用训练脚本
│   ├── train_local.py         # 本地训练脚本
│   └── convert_dataset.py     # 数据集转化工具
├── database/                   # 数据集目录
└── docker-compose.yml          # 基础设施配置
```

## API 一览

### 认证

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/auth/register` | 用户注册 |
| POST | `/api/auth/login` | 用户登录 |
| POST | `/api/auth/logout` | 退出登录 |
| GET | `/api/auth/me` | 获取当前用户信息 |
| PUT | `/api/auth/password` | 修改密码 |

### 检测

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/detection/single` | 单图检测 |
| POST | `/api/detection/batch` | 批量检测 |
| POST | `/api/detection/video` | 视频检测 |
| GET | `/api/detection/pests/list` | 病虫害列表 |

### 模型管理

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/detection/model/status` | 当前模型状态 |
| POST | `/api/detection/model/reload` | 重载模型 |
| GET | `/api/detection/models` | 可用模型列表 |
| POST | `/api/detection/models/switch` | 切换模型版本 |

### 历史记录

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/history/list` | 检测历史（支持 keyword/status 筛选） |
| GET | `/api/history/{id}` | 检测详情 |
| DELETE | `/api/history/{id}` | 删除记录 |

### 管理员

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/admin/users` | 用户列表 |
| PUT | `/api/admin/users/{id}/role` | 修改用户角色 |
| PUT | `/api/admin/users/{id}/status` | 启用/禁用用户 |
| DELETE | `/api/admin/users/{id}` | 删除用户 |

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
