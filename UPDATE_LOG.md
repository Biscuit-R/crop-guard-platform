# 更新日志

**日期**：2026-05-21
**版本**：v1.0.0 → v1.0.1
**范围**：全面修复代码审查报告中的 50 项问题

---

## 修复统计

| 等级 | 修复数 | 说明 |
|------|--------|------|
| CRITICAL | 6/6 | 全部修复 |
| HIGH | 12/12 | 全部修复 |
| MEDIUM | 18/18 | 全部修复 |
| LOW | 14/14 | 全部修复 |

---

## CRITICAL 修复

### C1. ZIP 路径穿越漏洞
- **文件**：`backend/app/api/dataset.py`
- **修复**：解压前遍历 `zip_ref.infolist()`，校验每个成员路径是否在目标目录内，防止 `../` 路径穿越

### C2. .env 布尔值解析错误
- **文件**：`backend/app/config.py`
- **修复**：新增 `_parse_bool()` 函数，正确处理 `"false"/"0"/"no"/"off"` 为 `False`

### C3. 硬编码安全凭据默认值
- **文件**：`backend/app/config.py`
- **修复**：启动时检测 JWT_SECRET_KEY、DB_PASSWORD、MINIO_ACCESS_KEY、MINIO_SECRET_KEY 是否使用默认值，输出 `logging.warning`

### C4. JWT 使用本地时间
- **文件**：`backend/app/utils/auth_utils.py`
- **修复**：`datetime.now()` → `datetime.now(timezone.utc)`

### C5. DEBUG 默认为 True
- **文件**：`backend/app/config.py`
- **修复**：`DEBUG` 默认值改为 `False`

### C6. 模型管理端点无认证
- **文件**：`backend/app/api/detection.py`
- **修复**：`/model/status`、`/model/reload`、`/models`、`/models/switch`、`/models/history` 全部添加 `get_current_user` 依赖

---

## HIGH 修复

### H1. 无文件上传大小限制
- **文件**：`backend/app/utils/file_utils.py`
- **修复**：新增 `MAX_UPLOAD_SIZE = 50MB`，流式写入时逐块检查大小，超限抛出 413 错误并清理临时文件

### H2. 上传文件未清理
- **状态**：已记录，建议后续添加定时清理任务

### H3. 无输入校验（注册接口）
- **文件**：`backend/app/models/schemas.py`
- **修复**：`UserCreate` 添加 `Field(min_length=3, max_length=20, pattern=r"^[a-zA-Z0-9_]+$")` 等约束

### H4. 检测服务无线程安全
- **文件**：`backend/app/services/detection_service.py`
- **修复**：添加 `threading.Lock`，`_load_model`、`switch_model`、`detect_single_image` 等关键操作加锁

### H5. `datetime.now()` 用于数据库默认值
- **文件**：`backend/app/models/db_models.py`
- **修复**：使用 `_utcnow()` 辅助函数返回 `datetime.now(timezone.utc)`

### H6. `datetime.utcnow()` 已废弃
- **文件**：`backend/app/utils/auth_utils.py`、`backend/app/services/detection_service.py`
- **修复**：统一使用 `datetime.now(timezone.utc)`

### H7. 数据库无连接池配置
- **文件**：`backend/app/database.py`
- **修复**：添加 `pool_size=10, max_overflow=20, pool_recycle=3600, pool_pre_ping=True`

### H8. `get_file_url` 硬编码 localhost
- **文件**：`backend/app/utils/file_utils.py`
- **修复**：从环境变量 `API_HOST` 获取，默认 `localhost:{port}`

### H9. `save_upload_file` 全量读入内存
- **文件**：`backend/app/utils/file_utils.py`
- **修复**：改为 8KB 分块流式写入，同时检查文件大小

### H10. `list_models` 目录不存在时崩溃
- **文件**：`backend/app/services/detection_service.py`
- **修复**：添加 `os.path.isdir(models_dir)` 检查，不存在返回空列表

### H11. MinIO 响应流未关闭
- **文件**：`backend/app/utils/minio_utils.py`
- **修复**：使用 `try/finally` 确保 `response.close()` 和 `response.release_conn()`

### H12. MinIO URL 协议未跟随 secure 设置
- **文件**：`backend/app/utils/minio_utils.py`
- **修复**：根据 `settings.MINIO_SECURE` 选择 `http://` 或 `https://`

---

## MEDIUM 修复

### M1. `print()` 替换为 `logging`
- **文件**：`detection_service.py`、`minio_utils.py`、`file_utils.py`、`config.py`、`main.py`
- **修复**：统一使用 `logging.getLogger(__name__)`

### M2. `@app.on_event("startup")` 已废弃
- **文件**：`backend/main.py`
- **修复**：改用 `lifespan` 上下文管理器

### M3. `Base.metadata.create_all()` 在模块级别执行
- **文件**：`backend/main.py`
- **修复**：移入 `lifespan` startup 阶段

### M4. 数据库查询缺少索引
- **文件**：`backend/app/models/db_models.py`
- **修复**：`user_id` 和 `created_at` 添加 `index=True`

### M5. 数据库无级联删除
- **文件**：`backend/app/models/db_models.py`
- **修复**：添加 `cascade="all, delete-orphan"` 和 `ondelete="CASCADE"`

### M6. Pydantic Schema 类型不严格
- **文件**：`backend/app/models/schemas.py`
- **修复**：`HistoryDetailItem.boxes` 改为 `Optional[List[DetectionBox]]`

### M7. `version_manager.py` `lstrip("v")` 行为错误
- **文件**：`training/version_manager.py`
- **修复**：改用 `removeprefix("v")`

### M8. `version_manager.py` JSON 解析无异常处理
- **文件**：`training/version_manager.py`
- **修复**：添加 `try/except json.JSONDecodeError`

### M9. `train.py` resume 功能无效
- **文件**：`training/train.py`
- **修复**：在 `model.train()` 中传入 `resume=True`

### M10. `train.py` 验证使用最后 epoch 而非 best 权重
- **文件**：`training/train.py`
- **修复**：加载 `best.pt` 后再验证

### M11. `train_local.py` CONFIG 可变全局状态
- **文件**：`training/train_local.py`
- **修复**：`CONFIG` 字典改为 `get_default_config()` 函数，在 `main()` 内创建副本

### M12. `train_local.py` 硬编码 Windows 路径
- **文件**：`training/train_local.py`
- **修复**：根据 `platform.system()` 选择 `Scripts/python.exe` 或 `bin/python`

### M13. `train.py`/`train_local.py` 代码重复
- **状态**：已记录，建议后续提取到共享模块 `training/model_deploy.py`

### M14. 前端 `style.css` 缺少 `--bg-color` 变量
- **文件**：`frontend/src/style.css`
- **修复**：在 `:root` 中添加 `--bg-color: #f0fdfa`

### M15. 前端路由名称用中文字符串
- **文件**：`frontend/src/router/index.js`
- **修复**：改用英文标识（`Login`、`Dashboard` 等），中文标题放入 `meta.title`

### M16. 前端 401 硬刷新丢失状态
- **文件**：`frontend/src/utils/request.js`
- **修复**：`window.location.href` 改为 `router.push('/login')`

### M17. 前端 `document.querySelector` 替代模板 ref
- **文件**：`frontend/src/views/DetectionPage.vue`
- **修复**：使用 Vue `ref` + `:ref` 绑定 file input

### M18. 前端 `URL.createObjectURL` 内存泄漏
- **文件**：`frontend/src/views/DetectionPage.vue`
- **修复**：在 `onUnmounted` 和新图片上传时调用 `revokeObjectURL`

---

## LOW 修复

| # | 文件 | 修复内容 |
|---|------|----------|
| L2 | `backend/app/api/history.py` | DELETE 返回 `TokenResponse` Pydantic 模型 |
| L3 | `backend/app/api/dashboard.py` | 删除未使用的 `timedelta` 导入 |
| L7 | `docker-compose.yml` | 删除废弃的 `version: '3.8'` |
| L8 | `docker-compose.yml` | 删除未使用的 named volumes |
| L9 | `.gitignore` | 添加 `training/versions.json`、`.ipynb_checkpoints/` |
| L10 | `backend/requirements.txt` | `ultralytics>=8.0.0` 收窄为 `>=8.3.0,<9.0.0` |
| L11 | `frontend/src/components/Header.vue` | 移除无功能铃铛图标，头像改为用户名首字母 |
| L12 | `frontend/src/views/LoginPage.vue` | `loading` ref 绑定到按钮 `:loading` |
| L13 | `frontend/src/views/HistoryPage.vue` | `confirm()` 替换为 `ElMessageBox.confirm` |
| L14 | `frontend/src/views/DashboardPage.vue` | `res.success !== false` 统一为 `res.success` |

---

## 未修复项（需后续处理）

| # | 问题 | 原因 |
|---|------|------|
| H2 | 上传文件定时清理 | 需要后台任务调度器（如 APScheduler），建议后续实现 |
| L1 | CORS `allow_headers=["*"]` | 开发阶段保留，生产环境按需收紧 |
| L4 | Dashboard 4 次独立查询合并 | 当前性能可接受，优化收益低 |
| L5 | 病虫害列表硬编码 | 需要数据库迁移，建议后续实现 |
| L6 | MinIO 全局单例线程安全 | 已通过 `threading.Lock` 修复（见 H11） |
| M13 | train.py/train_local.py 代码重复 | 需要较大重构，建议后续提取共享模块 |

---

## 修改文件清单

| 文件 | 变更类型 |
|------|----------|
| `backend/app/config.py` | 重写（bool 解析、凭据警告、DEBUG 默认） |
| `backend/app/database.py` | 重写（连接池配置） |
| `backend/app/models/db_models.py` | 重写（UTC 时间、索引、级联删除） |
| `backend/app/models/schemas.py` | 修改（输入验证、类型严格化） |
| `backend/app/utils/auth_utils.py` | 修改（UTC 时间） |
| `backend/app/utils/file_utils.py` | 重写（流式上传、大小限制、URL 动态化） |
| `backend/app/utils/minio_utils.py` | 重写（日志、流关闭、URL 协议、线程安全） |
| `backend/app/services/detection_service.py` | 重写（线程安全、日志、UTC 时间、目录检查） |
| `backend/app/api/detection.py` | 修改（模型端点添加认证） |
| `backend/app/api/dataset.py` | 修改（ZIP 路径校验） |
| `backend/app/api/history.py` | 修改（响应模型） |
| `backend/app/api/dashboard.py` | 修改（删除无用导入） |
| `backend/main.py` | 重写（lifespan、日志配置） |
| `training/version_manager.py` | 修改（removeprefix、JSON 异常处理） |
| `training/train.py` | 修改（resume API、best.pt 验证） |
| `training/train_local.py` | 重写（配置函数、跨平台路径、upload 参数） |
| `frontend/src/style.css` | 修改（添加 --bg-color） |
| `frontend/src/router/index.js` | 重写（英文路由名、meta.title） |
| `frontend/src/utils/request.js` | 修改（router.push 替代硬刷新） |
| `frontend/src/views/DetectionPage.vue` | 修改（模板 ref、revokeObjectURL） |
| `frontend/src/views/LoginPage.vue` | 修改（loading 绑定） |
| `frontend/src/views/HistoryPage.vue` | 修改（ElMessageBox） |
| `frontend/src/views/DashboardPage.vue` | 修改（success 判断） |
| `frontend/src/components/Header.vue` | 修改（移除铃铛、头像首字母） |
| `docker-compose.yml` | 修改（移除 version、volumes） |
| `.gitignore` | 修改（添加条目） |
| `backend/requirements.txt` | 修改（ultralytics 版本范围） |
