# Crop Guard Platform

作物虫害检测与知识问答平台：上传作物照片检测虫害（YOLO 推理服务化），并基于虫害图鉴语料提供 RAG 知识问答（症状检索 / 防治方案，带来源溯源与置信度分级）。

> 范围说明：本项目统一使用**虫害**——检测模型与语料均为虫/螨（102 类），**不含真菌/细菌/病毒病害**。

当前版本 **v2.0.0**（从零重建版）。v1 旧版历史保留在 [`v1-legacy`](../../tree/v1-legacy) 分支。

## 功能

### 🔍 虫害检测
- 单图上传，返回标注结果图、置信度、检测框坐标
- 检测历史入库（PostgreSQL），可回看、可删除
- 检测结果与图鉴联动：`class_name` 精确查表直出虫害档案（不经 LLM）

### 💬 知识问答（RAG）
- 症状描述 → BGE 向量检索（pgvector，306 块图鉴语料）→ DeepSeek 生成，附来源溯源
- 三档置信度语义（阈值由实测分数分布定值）：
  | 检索分 | 行为 |
  |---|---|
  | ≥ 0.75 | confident：正常作答 |
  | 0.60 ~ 0.75 | caution：作答 + 「仅供参考」标注 |
  | < 0.60 | 低分分支：LLM 意图分类 → 无关则指引 / 信息不足则出选择题·判断题追问；追问一轮仍低分 → 零调用拒答 |
- 降级语义分级：作答路径 LLM 故障 → fail-open 返回检索原文；澄清路径故障 → fail-closed 拒答
- 多轮对话：Redis 会话记忆（最近 5 轮 / TTL 30min），支持指代续问
- Query 改写：每轮先改写再检索（口语规范化 + 指代消解）；改写只喂检索器、作答用原问题；失败 fail-open 回退原问题

### 👤 账号体系
- JWT 注册 / 登录，注册接入短信验证码（演示模式：验证码随响应弹窗展示）
- 验证码安全设计：Redis `SETEX 300s` 有效期 + `SET NX EX 60s` 原子限频；`compare_digest` 防时序攻击；一次性 DELETE 防重放

### 📖 图鉴
- 102 类虫害全量浏览，按名称 / 寄主植物查找

## 技术栈

| 层 | 选型 |
|---|---|
| 后端 | Python 3.12 · FastAPI · SQLAlchemy · Alembic · uv |
| 检测 | YOLO（外部模型，平台只做推理服务化） |
| RAG | BGE 本地 embedding · pgvector · DeepSeek API（不用 LangChain） |
| 基础设施 | PostgreSQL(pgvector) · Redis · MinIO · Docker Compose |
| 前端 | Vue 3 · TypeScript · Element Plus · Pinia · Vite |

关键工程决策及理由见 [`docs/decisions.md`](docs/decisions.md)。

## 快速开始

### Docker Compose（推荐）

```bash
git clone https://github.com/Biscuit-R/crop-guard-platform.git
cd crop-guard-platform

cp backend/.env.example backend/.env   # 填 DEEPSEEK_API_KEY 等
docker compose up -d                   # postgres(pgvector) / redis / minio / backend / frontend
```

- 前端：http://localhost:5173
- 后端健康检查：http://localhost:8000/health

### 本地开发（后端）

```bash
cd backend
uv sync                                # 依赖安装（Python 3.12）
uv run pytest                          # 跑测试
uv run alembic upgrade head            # 数据库迁移
uv run uvicorn app.main:app --reload
```

### 本地开发（前端）

```bash
cd frontend
npm install
npm run dev
```

## 项目结构

```
├── backend/
│   ├── app/
│   │   ├── modules/          # auth / detection / rag 路由层
│   │   ├── rag/              # 检索、改写、问答编排、会话记忆、评测脚本
│   │   ├── data/             # 102 类虫害图鉴语料
│   │   └── core/             # 配置
│   ├── migrations/           # Alembic
│   ├── evals/                # query 改写多轮评测
│   └── tests/                # pytest（108 条）
├── frontend/
│   └── src/
│       ├── views/            # 检测 / 历史 / 问答 / 图鉴 / 登录注册
│       ├── components/
│       └── api/
├── docs/                     # 需求、决策记录、流程、复盘笔记
└── docker-compose.yml
```

## 质量与评测

- 后端 `pytest` **108 passed**：三档语义、fail-open/closed、会话续问、验证码限频/重放、改写红线均有测试锁定
- RAG 评测：40 题口语化评测集 top-3 命中率 87%（验收线 ≥80%），无关题拒答率 100%
- Query 改写多轮评测：turn-2 top-3 命中率 25% → 62%（改写 on/off 对比，`backend/evals/`）
- CI（GitHub Actions）：后端 uv sync + pytest；compose 起依赖容器 + 后端健康检查

## 已知边界

- 检测模型为外部产物，本项目不含训练 / 微调
- 短信验证码为演示模式，生产需接真实网关
- 摄像头 / 视频 / 批量检测按需求砍序，不在 v2 范围

## 文档

- [`docs/requirements.md`](docs/requirements.md) — 需求与验收标准
- [`docs/decisions.md`](docs/decisions.md) — 技术决策记录（含否决理由）
- [`docs/workflow.md`](docs/workflow.md) — 开发流程
- [`docs/notes.md`](docs/notes.md) — 过程复盘笔记
