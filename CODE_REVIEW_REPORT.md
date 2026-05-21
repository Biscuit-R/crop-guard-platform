# 代码审查报告

**日期**：2026-05-21
**范围**：crop-guard-platform 全部代码
**审查标准**：生产环境规范、安全性、可读性、可维护性

---

## 一、严重程度总览

| 等级 | 数量 | 说明 |
|------|------|------|
| CRITICAL | 6 | 安全漏洞，必须立即修复 |
| HIGH | 12 | 影响稳定性/安全性，优先修复 |
| MEDIUM | 18 | 代码质量/可维护性问题 |
| LOW | 14 | 规范性/可读性问题 |

---

## 二、CRITICAL（必须修复）

### C1. ZIP 路径穿越漏洞
- **文件**：`backend/app/api/dataset.py:65-66`
- **问题**：`zip_ref.extractall()` 未校验 ZIP 内文件路径，恶意 ZIP 可写入任意目录（CWE-22）
- **修复**：遍历 `zip_ref.infolist()`，校验每个成员的 `../` 路径

### C2. .env 布尔值解析错误
- **文件**：`backend/app/config.py:55`
- **问题**：`bool("false")` 在 Python 中返回 `True`，导致 `.env` 中 `DEBUG=false` 无效
- **修复**：自定义 `_parse_bool()` 函数处理 `"false"/"0"/"no"` 等值

### C3. 硬编码安全凭据默认值
- **文件**：`backend/app/config.py:30,25-26,37-38`
- **问题**：JWT 密钥、数据库密码、MinIO 凭据硬编码在源码中
- **修复**：启动时检测默认值并输出警告；生产环境必须通过 `.env` 覆盖

### C4. JWT 使用本地时间计算过期
- **文件**：`backend/app/utils/auth_utils.py:25`
- **问题**：`datetime.now()` 使用服务器本地时区，非 UTC，导致 token 过期时间不准确
- **修复**：改用 `datetime.utcnow()` 或 `datetime.now(timezone.utc)`

### C5. DEBUG 默认为 True
- **文件**：`backend/app/config.py:8`
- **问题**：未配置 `.env` 时默认开启 DEBUG，泄露 SQL 语句和堆栈
- **修复**：默认值改为 `False`

### C6. 模型管理端点无认证
- **文件**：`backend/app/api/detection.py:57-120`
- **问题**：`/model/status`、`/model/reload`、`/models`、`/models/switch` 无鉴权，任何人可切换/重载模型
- **修复**：添加 `get_current_user` 依赖

---

## 三、HIGH（优先修复）

### H1. 无文件上传大小限制
- **文件**：`backend/app/api/detection.py:25`、`backend/app/api/dataset.py:26`
- **问题**：攻击者可上传超大文件耗尽磁盘/内存
- **修复**：在 `file_utils.py` 中添加 `MAX_UPLOAD_SIZE` 检查

### H2. 上传文件未清理
- **文件**：`backend/app/api/detection.py:31`、`backend/app/services/detection_service.py:209`
- **问题**：检测后图片和结果图片永久保留，磁盘无限增长
- **修复**：添加定时清理或检测完成后删除临时文件

### H3. 无输入校验（注册接口）
- **文件**：`backend/app/api/auth.py`、`backend/app/models/schemas.py:51-54`
- **问题**：用户名/邮箱/密码无长度、格式校验
- **修复**：`UserCreate` 添加 `Field(min_length=...)` 约束

### H4. 检测服务无线程安全
- **文件**：`backend/app/services/detection_service.py:71-88,180-227`
- **问题**：`check_and_reload()` 可与 `detect_single_image()` 并发执行，模型可能在推理中途被替换
- **修复**：添加 `threading.Lock` 保护模型读写

### H5. `datetime.now()` 用于数据库默认值
- **文件**：`backend/app/models/db_models.py:14-15,33`
- **问题**：`datetime.now()` 使用本地时区，跨时区部署会产生歧义
- **修复**：改用 `datetime.utcnow()` 或 `func.now()`

### H6. `datetime.utcnow()` 已废弃
- **文件**：`backend/app/utils/auth_utils.py:25`
- **问题**：Python 3.12 中 `datetime.utcnow()` 已标记废弃
- **修复**：使用 `datetime.now(timezone.utc)`

### H7. 数据库无连接池配置
- **文件**：`backend/app/database.py:10`
- **问题**：未设置 `pool_size`、`pool_recycle`、`pool_pre_ping`
- **修复**：添加连接池参数

### H8. `get_file_url` 硬编码 localhost
- **文件**：`backend/app/utils/file_utils.py:27`
- **问题**：生产环境 URL 全部指向 `localhost`
- **修复**：从配置或请求上下文获取 host

### H9. `save_upload_file` 全量读入内存
- **文件**：`backend/app/utils/file_utils.py:19-21`
- **问题**：大文件一次性读入内存可能导致 OOM
- **修复**：分块流式写入

### H10. `list_models` 目录不存在时崩溃
- **文件**：`backend/app/services/detection_service.py:111`
- **问题**：`os.listdir(models_dir)` 在目录不存在时抛出 `FileNotFoundError`
- **修复**：添加 `os.path.exists()` 检查

### H11. MinIO 响应流未关闭
- **文件**：`backend/app/utils/minio_utils.py:123-124`
- **问题**：`get_object()` 返回的流未调用 `close()`/`release_conn()`，连接泄漏
- **修复**：使用 `with` 语句或手动关闭

### H12. MinIO URL 协议未跟随 secure 设置
- **文件**：`backend/app/utils/minio_utils.py:50`
- **问题**：URL 始终使用 `http://`，即使 `MINIO_SECURE=True`
- **修复**：根据 `settings.MINIO_SECURE` 选择协议

---

## 四、MEDIUM（代码质量）

### M1. `print()` 替换为 `logging`
- **文件**：全部后端文件
- **修复**：统一使用 `logging.getLogger(__name__)`

### M2. `@app.on_event("startup")` 已废弃
- **文件**：`backend/main.py:42`
- **修复**：改用 `lifespan` 上下文管理器

### M3. `Base.metadata.create_all()` 在模块级别执行
- **文件**：`backend/main.py:15`
- **修复**：移入 startup 生命周期

### M4. 数据库查询缺少索引
- **文件**：`backend/app/models/db_models.py:24,33`
- **问题**：`user_id` 和 `created_at` 无索引
- **修复**：添加 `index=True`

### M5. 数据库无级联删除
- **文件**：`backend/app/models/db_models.py:24`
- **问题**：删除用户时外键约束报错
- **修复**：添加 `cascade="all, delete-orphan"`

### M6. Pydantic Schema 类型不严格
- **文件**：`backend/app/models/schemas.py:75,88,118,150`
- **问题**：`dict`、`list` 未参数化，`model_mtime` 用 `str` 存时间
- **修复**：使用具体类型如 `Optional[List[DetectionBox]]`、`Optional[datetime]`

### M7. `version_manager.py` `lstrip("v")` 行为错误
- **文件**：`training/version_manager.py:59`
- **问题**：`lstrip` 会剥离字符集合而非前缀，`"version1.0.0"` 会被错误处理
- **修复**：改用 `removeprefix("v")`（Python 3.9+）

### M8. `version_manager.py` JSON 解析无异常处理
- **文件**：`training/version_manager.py:27`
- **问题**：`versions.json` 损坏时直接崩溃
- **修复**：添加 `try/except json.JSONDecodeError`

### M9. `train.py` resume 功能无效
- **文件**：`training/train.py:201`
- **问题**：`model.resume = True` 不是 ultralytics 的有效 API
- **修复**：在 `model.train()` 中传入 `resume=True`

### M10. `train.py` 验证使用最后 epoch 而非 best 权重
- **文件**：`training/train.py:253`
- **问题**：`model.val()` 验证的是训练结束时的权重，不是 best.pt
- **修复**：加载 `best.pt` 后再验证

### M11. `train_local.py` CONFIG 可变全局状态
- **文件**：`training/train_local.py:28-41`
- **问题**：模块级 dict 被 `main()` 修改，重复调用会累积变更
- **修复**：在 `main()` 内创建配置副本

### M12. `train_local.py` 硬编码 Windows 路径
- **文件**：`training/train_local.py:23`
- **问题**：`Scripts/python.exe` 仅 Windows 可用
- **修复**：根据 `sys.platform` 选择路径

### M13. `train.py`/`train_local.py` 代码重复
- **文件**：`training/train.py` 和 `training/train_local.py`
- **问题**：`upload_to_minio`、`deploy_model` 几乎完全重复
- **修复**：提取到共享模块 `training/model_deploy.py`

### M14. 前端 `style.css` 缺少 `--bg-color` 变量
- **文件**：`frontend/src/style.css`
- **问题**：`DatasetToolsPage.vue` 引用 `var(--bg-color)` 但未定义
- **修复**：在 `:root` 中添加 `--bg-color: #f0fdfa`

### M15. 前端路由名称用中文字符串
- **文件**：`frontend/src/router/index.js`
- **问题**：`name: "登录"` 作为程序标识符不稳定
- **修复**：改用英文标识，中文标题放入 `meta.title`

### M16. 前端 401 硬刷新丢失状态
- **文件**：`frontend/src/utils/request.js:29`
- **问题**：`window.location.href = '/login'` 重载页面丢失所有状态
- **修复**：使用 `router.push('/login')`

### M17. 前端 `document.querySelector` 替代模板 ref
- **文件**：`frontend/src/views/DetectionPage.vue:233`
- **问题**：直接 DOM 操作绕过 Vue 响应式
- **修复**：使用 `ref()` 绑定 file input

### M18. 前端 `URL.createObjectURL` 内存泄漏
- **文件**：`frontend/src/views/DetectionPage.vue:261`
- **问题**：未调用 `revokeObjectURL` 释放引用
- **修复**：在 `onUnmounted` 或新图片上传时释放

---

## 五、LOW（规范性）

| # | 文件 | 问题 | 修复 |
|---|------|------|------|
| L1 | `backend/main.py:30` | CORS `allow_headers=["*"]` 过于宽泛 | 列举必要 header |
| L2 | `backend/app/api/history.py:67` | DELETE 返回 raw dict，非 Pydantic 模型 | 统一响应格式 |
| L3 | `backend/app/api/dashboard.py:4` | `timedelta` 导入未使用 | 删除 |
| L4 | `backend/app/api/dashboard.py` | 4 次独立查询可合并 | 使用聚合查询 |
| L5 | `backend/app/api/detection.py:126-141` | 病虫害列表硬编码 | 迁移到配置/数据库 |
| L6 | `backend/app/utils/minio_utils.py` | 全局单例非线程安全 | 使用 threading.Lock |
| L7 | `docker-compose.yml:1` | `version: '3.8'` 已废弃 | 删除 |
| L8 | `docker-compose.yml:57-60` | 声明了未使用的 named volumes | 删除 |
| L9 | `.gitignore` | 缺少 `training/versions.json`、`.ipynb_checkpoints/` | 添加 |
| L10 | `backend/requirements.txt:19` | `ultralytics>=8.0.0` 范围过宽 | 收窄为 `>=8.3.0,<9.0.0` |
| L11 | `frontend/src/components/Header.vue:11,15` | 铃铛图标无功能、头像 URL 硬编码 | 实现或移除 |
| L12 | `frontend/src/views/LoginPage.vue:90` | `loading` ref 未绑定到按钮 `:loading` | 绑定 |
| L13 | `frontend/src/views/HistoryPage.vue:150` | 使用原生 `confirm()` 而非 `ElMessageBox` | 替换 |
| L14 | `frontend/src/views/DashboardPage.vue:118` | `res.success !== false` 不一致 | 统一为 `res.success` |

---

## 六、建议修复顺序

1. **第一批（安全）**：C1-C6 + H1-H2
2. **第二批（稳定性）**：H3-H12 + M4-M5
3. **第三批（代码质量）**：M1-M3, M6-M18
4. **第四批（规范性）**：L1-L14
