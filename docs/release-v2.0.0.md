# Crop Guard Platform v2.0.0

作物虫害检测与知识问答平台 —— 从零重建版（v1 归档后重写）。

> 范围用词统一为**虫害**：检测模型与语料均为虫/螨（102 类），不含真菌/细菌/病毒病害。

## 功能总览

### 检测（YOLO 推理服务化）
- 单图上传检测，返回标注结果图、置信度、bbox
- 检测历史入库（PostgreSQL），可回看、可删除
- 结果与图鉴联动：`class_name` 精确查表直出虫害档案（不过 LLM）

### 知识问答（RAG）
- 症状描述 → BGE 向量检索（pgvector，306 块图鉴语料）→ DeepSeek 生成，带来源溯源
- 三档置信度语义（阈值由实测分数分布定值，非拍脑袋）：
  - `score ≥ 0.75` confident 正常作答
  - `0.60 ≤ score < 0.75` caution 作答 + 「仅供参考」标注
  - `score < 0.60` 低分分支：LLM 意图分类 → 无关（off_topic）指引进对话 / 相关但信息不足（clarify）出选择题·判断题追问；追问一轮仍低分 → 零调用拒答（防无限循环）
- 降级语义分级：作答路径 LLM 挂 → fail-open 返回检索原文；澄清路径 LLM 挂 → fail-closed 拒答
- 多轮对话：Redis 会话记忆（最近 5 轮 / TTL 30min），支持指代续问
- **query 改写**：每轮先改写再检索（口语规范化 + 历史指代消解，一次 LLM 调用）；改写只喂检索器、作答仍用原问题；失败 fail-open 回退原问题；红线 = 禁止引入对话未提及的虫名
  - 多轮评测（8 对，turn-2 top-3 命中率）：改写前 25% → 改写后 62%；指代消解型 4 对全中；评测同时暴露「改写非银弹」（口语规范化型 2 对改写后变差，已记录根因）

### 账号体系
- 注册 / 登录（JWT），注册接入**短信验证码**：
  - 6 位码 `secrets` 生成；Redis 双 key：`SETEX 300s` 有效期 + `SET NX EX 60s` 原子限频
  - 校验 `compare_digest` 防时序攻击 + 一次性 DELETE 防重放
  - 演示模式开关：验证码随响应弹窗展示（未接真实网关的显式降级）
- 图鉴全量页（102 类，按名称/寄主查找）

## 工程决策（详见 docs/decisions.md）

| 决策 | 选择 | 一句话理由 |
|---|---|---|
| LLM | DeepSeek API | 云 API 起步，不训练模型（考核点是工程能力） |
| Embedding | BGE 本地编码 | 语义对称性 + 分数落在 [0,1] 可直接驱动拒答阈值 |
| 向量库 | pgvector | 数据已在 PostgreSQL，不引独立向量库 |
| LLM 框架 | 不用 LangChain | 框架把检索变黑盒；降级语义不在其概念里 |
| 依赖管理 | uv | 锁文件即环境可复现依据 |
| 双入口 | 检测结果=查表 / 症状描述=RAG | 精确 key 查询不该过向量库 |

## 质量与验证

- 后端 pytest **108 passed**（三档语义、fail-open/closed、会话续问、验证码限频/重放、改写红线均有测试锁定）
- RAG 评测：40 题口语化评测集 top-3 命中率 87%（≥80% 达标）；无关题拒答率 100%
- query 改写多轮评测：on/off 对比 25% → 62%，含红线定性检查（0 违规）
- 前端 vue-tsc + vitest + build 全绿
- CI（GitHub Actions）：后端 uv sync + pytest；compose 起依赖容器 + 后端健康检查

## 部署

```bash
docker compose up -d     # postgres(pgvector) / redis / minio / backend / frontend
```

配置见 `.env.example`（`.env` 不入库）。

## 已知边界

- 检测模型为外部产物（YOLO 推理服务化），不含训练/微调
- 短信为演示模式，生产需接真实网关
- 摄像头/视频/批量检测按需求砍序，不在 v2 范围
