# Crop Guard Platform

农作物病虫害智能检测平台

## 技术栈

- 后端：Python FastAPI + PostgreSQL + YOLO (ultralytics)
- 前端：Vue 3 + Vite + Element Plus + Pinia
- 基础设施：Docker Compose (PostgreSQL + Redis + MinIO)

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

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173
