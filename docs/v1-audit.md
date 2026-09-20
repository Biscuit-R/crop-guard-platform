# v1 代码审计报告

> 对象：`E:\rsod-web-platform\archive\crop-guard-platform`，git HEAD `e394606`
> 规模：后端 26 个 Python 文件 6385 行 ｜ 前端 7172 行 JS/Vue（不含 `node_modules` / `dist`）
> 方法：读代码，不采信 README / CHANGELOG。所有行号为实际文件行号。
> 用途：`docs/requirements.md` 的「v1 证据」栏指向本文档条目号。

---

## 0. 可信度说明

本文档区分三级证据，请勿混用：

| 标记 | 含义 |
|---|---|
| **【已核实】** | 本文档作者（Claude）用独立命令复现确认过 |
| 【读码】 | 由代码阅读得出，未独立复现 |
| 【未验证】 | 依赖运行环境或版本，标注了推测成分 |

**过程中已发现并纠正的一处误报**：分析报告曾声称 `backend/.env`（含真实 JWT 密钥）已提交进仓库。实测 `git ls-files | grep -i env` 只返回 `backend/.env.example`，且 `git check-ignore -v backend/.env` 命中 `.gitignore:12`。**该文件既未被追踪、也被正确忽略，不存在泄露。**

**未读取的文件**：`backend/.env`（含真实凭据）——读取会把凭据写进会话记录，权限策略拦截。所有环境变量结论来自 `.env.example` 与 `app/config.py` 默认值。

---

## 1. 统计

| 分级 | 数量 |
|---|---|
| 🔴 P0 — 严重 | 7 |
| 🟡 P1 — 中等 | 38 |
| 🟢 值得保留的好设计 | 17 |

---

## 2. 🔴 P0 — 严重问题

### A-01 【已核实】异步端点内执行阻塞式 CPU 推理，事件循环被独占
`app/api/detection.py:33, 75, 119, 230`

四个检测端点全部声明为 `async def`，但内部直接调用同步的 `detection_service.detect_single_image()` / `detect_video()` / `model.predict()`。

```
$ grep -rn "run_in_executor\|to_thread\|BackgroundTask" backend/
No matches found
```

单个请求在推理期间**阻塞整个事件循环**，其它所有端点（包括 `/health`、登录）全部排队。`asyncio.Semaphore(5)`（`:29`）限制的是协程进入数，无法把工作交给线程池。

**v2 对策**：`NFR-P1`、`FR-2.3`

### A-02 【已核实】模型管理端点权限过低，任何登录用户可全局换模型
`app/api/detection.py:181`（`/model/reload`）、`:203`（`/models/switch`）

```
$ grep -n "Depends(get_current_(user|admin))" backend/app/api/detection.py
37:  Depends(get_current_user)
79:  Depends(get_current_user)
124: Depends(get_current_user)
170: Depends(get_current_user)
181: Depends(get_current_user)
192: Depends(get_current_user)
203: Depends(get_current_user)
219: Depends(get_current_user)
234: Depends(get_current_user)
```

全部 9 个端点都是 `get_current_user`，**无一处 `get_current_admin`**。普通用户调一次 `POST /api/detection/models/switch {"version":"model_67.pt"}` 即可让**全平台**切换模型。`switch_model` 还支持模糊匹配 `glob(f"*{version}*.pt")`（`detection_service.py:395`），传 `"model"` 之类前缀即可命中。

全局单例（`detection_service.py:642`）+ 全局锁（`:260`）意味着影响所有并发用户。对照 `/dashboard/stats/cache` 的清理都要求 admin（`dashboard.py:109`）——admin 依赖是现成的，此处属遗漏。

**v2 对策**：`FR-7`、`NFR-S1`

### A-03 【已核实】全库无事务边界，无一处 `rollback`
`app/api/detection.py:108-109`，及所有 `db.commit()` 调用点

```
$ grep -rn "rollback" backend/
No matches found
```

批量检测的 `except Exception as e` 只记录错误字符串。若异常来自 `db.commit()`（唯一约束、连接断开等），SQLAlchemy Session 进入 invalid 状态，后续循环里 `db.add(history)` + `db.commit()`（`:101-102`）持续抛 `PendingRollbackError` → **一张图的 DB 失败会让整批剩余全部连锁失败**，且 `results` 里表现为"每张都失败"而非"仅第一张失败"。

`get_db()`（`database.py:25-30`）也只 `close` 不 `rollback`。

**v2 对策**：`NFR-R1`、`FR-2.2`

### A-04 模型切换失败会永久卡死 UI
`frontend/src/views/DetectionPage.vue:612-625`

`ElLoading.service()` 全屏遮罩（`:614`）在 `await switchModel`（`:615`）之后才 `loading.close()`（`:616`）。一旦接口 reject，直接进 `catch`（`:622-624`）只弹错误、**不关遮罩**。之后整页被 `rgba(0,0,0,0.5)` 蒙层挡住且无关闭途径，只能刷新浏览器。

**v2 对策**：`FR-9`

### A-05 数据集转换：整包读入内存 + 无解压大小上限
`app/api/dataset.py:58-59, 66-72`

`content = await file.read()` 一次性把整个 ZIP 读入内存，**不走同仓库已有的分块限流实现**（对比 `file_utils.py:26-34` 是正确的）。解压前只校验了路径穿越，**没有总大小或文件数上限** → 压缩比 1000:1 的 ZIP 炸弹可写爆磁盘。

**v2 对策**：`NFR-P5`、`NFR-S4`、`NFR-S5`、`FR-8`

### A-06 `data.yaml` 的 `val` 指向 `train`，验证集不存在
`app/api/dataset.py:456-471` ｜ `training/convert_dataset.py:393-394`

两行都是 `images/{split}`，且所有转换器只往 `images/train` / `labels/train` 写（`dataset.py:177-180, 261-264, 348-351, 404-407`）。用该产物训练，**验证指标严重乐观**（在训练集上评估）。对比 `training/data.yaml:2-3` 是正确分离的。

> 此条由两份独立分析各自发现，可视为已确认。

**v2 对策**：`FR-8`

### A-07 两套模型的类别索引不一致，混用权重导致中文名整体错位
`training/data.yaml:44` vs `training/data_balanced.yaml:43`

`data.yaml`（102 类）第 44 项是 `sericaorient_alismots_chulsky`，`data_balanced.yaml`（67 类）第 43 项是 `alfalfa_weevil`。**同一 index 指向不同物种**，而 `backend/app/config.py:111-241` 的 `CHINESE_CLASS_NAMES` 是一份共用映射 → 混用权重会整体错位。类别定义散布在 4 处（两个 yaml、`classes_example.txt`、`CHINESE_CLASS_NAMES`），全部靠手工保持一致。

**v2 对策**：`FR-5`、`FR-8`

---

## 3. 🟡 P1 — 中等问题

### 3.1 后端接口与业务

| 编号 | 问题 | 位置 |
|---|---|---|
| A-08 | `except Exception` 吞掉 `HTTPException`，把 413 变成 500。上传超限时用户看到"检测失败: 413: 文件大小超过限制"。**同一文件内 `/video` 却写对了**（显式 `except HTTPException: raise`） | `detection.py:70-71` vs `:163-164` |
| A-09 | 图片检测的原始文件名丢失，存的是 `temp_{uuid}.jpg`，而历史搜索的 `keyword` 正是对 `filename` 做 `ilike` → **用户搜自己的文件名永远搜不到**。视频却保留原名 → 是缺陷不是取舍 | `detection.py:41` vs `:137` |
| A-10 | `model_name` 请求参数被完全忽略（`current_model_version or model_name`）；默认值 `"pest-v1"` **不匹配任何真实文件**；`/models/history` 读的 `training/versions.json` **从不存在**，永远返回 `[]` | `detection.py:44,82,131`；`detection_service.py:408-410` |
| A-11 | ~600 行未接线死代码（近 10% 代码量）：`minio_utils.py`(175行，零引用)、`validators.py`(333行，无调用方)、`logging_utils.py`(93行，无调用方)、`ForumCommentCreate`/`ForumPostCreate`(定义了却用裸 `dict`) | 各文件 |
| A-12 | `revoked_tokens` 只增不删，无 TTL、无清理任务；**每次带凭据的请求都要查一次这张表**。`exp` 到期后记录已无意义 | `db_models.py:51-56`；`auth.py:125`；`auth_utils.py:58` |
| A-13 | 论坛列表 N+1：`comment_count=len(post.comments)` + `post.user.username` 对每条帖子各触发两次加载 → `page_size=50` 时最多 **101 次查询**。全库无 `joinedload`/`selectinload` | `forum.py:36-37` |
| A-14 | 看板统计拆成 6 次独立查询，可合并为 1 次聚合 | `dashboard.py:53-74` |
| A-19 | 短信模块与账号体系**完全脱节**：无表存手机号，`/verify` 成功后不签发任何凭据；且 `/send` `/verify` **均无鉴权** | `sms.py:3-4, 64, 123` |
| A-20 | `success_rate` 是恒 100% 的死指标：所有写入路径硬编码 `status="completed"`，无代码写过其它值。`status` 筛选参数同理只能匹配一种值 | `dashboard.py:65-68`；`detection.py:56,99,149` |
| A-21 | 检测失败不落库，且失败路径不清理已写出的半成品 MP4 与关键帧 → 孤儿文件 | `detection.py:165-166` |
| A-22 | 时区口径不一致：检测记录按 UTC 切"今日"，短信限次按北京时间切天，**同一天边界差 8 小时**（对国内用户，晚上 8 点后的检测会落到"明天"）。两处各有注释说明理由，属未统一而非疏忽 | `db_models.py:8` vs `sms.py:50-52` |
| A-23 | 响应契约不统一：`/dashboard/stats` 与 `/history/{id}` 返回**裸模型**，其余返回 `{success,data}` 信封。前端被迫记两套读法，且**只有信封型带业务文案** | `dashboard.py:88`；`history.py:43` |
| A-24 | 同一模块内三套错误契约并存：`/frame` 返回 200 + `success=false`（4 处）；`/batch` 返回 200 + **恒为 `true`** 的 `success`（即使全部失败）；`/single` `/video` 抛 500 | `detection.py:242-300, 112, 70` |
| A-25 | **无生产部署路径**：全仓库无任何 `Dockerfile` / `nginx.conf`；`docker-compose.yml` 只有 3 个基础设施服务，无 backend / frontend。`vite.config.js` 的 proxy 只对 dev server 生效，`frontend/dist/` 是孤儿产物 | `docker-compose.yml` |
| A-26 | compose 把 `./storage/postgres/init` 挂成初始化目录，但该目录**在磁盘上不存在** → Docker 创建空目录，初始化 SQL 永远不执行 | `docker-compose.yml:14` |
| A-27 | 视频检测的逐帧框数据**不落库**（`boxes` 恒为 `[]`），只存在于结果 MP4 里，无法二次分析 | `detection.py:148` |
| A-28 | 数据集转换的临时目录按 `user_id` 持久复用、**从不清理**；同一用户并发两次 `/convert` 会**互相删除对方目录**。`finally` 只删了 zip | `dataset.py:62-64, 136-138` |
| A-29 | 看板把**全平台口径**数据（总用户数、全站今日量）对**所有登录用户**开放，与个人数据混在同一响应里 | `dashboard.py:34-50` |
| A-30 | 改角色传非法值时**静默忽略**（`if` 无 `else`），仍返回"角色已更新"，前端无法感知失败 | `admin.py:50-51` |
| A-31 | 无「最后一个管理员」保护，可把唯一管理员降级 | `admin.py` |
| A-38 | 无登录失败次数限制（可无限暴力尝试）、无注册频率限制、密码仅要求 6 位且无强度校验 | `auth.py:60-79` |
| A-39 | `CORS_ORIGINS` 硬编码且 **`.env` 无法覆盖**（默认值是 list，env 解析需 JSON 格式）→ 部署到非 localhost 必须改代码 | `config.py:61`；`main.py:120-126` |
| A-40 | `/health` 恒返回 `{"status":"healthy"}`，**不探测 DB / Redis / 模型**，不能用于探针 | `main.py:149-151` |
| A-41 | 迁移无版本号、无回滚，靠 `information_schema` 探测 + 裸 `ALTER TABLE`，且**与 `create_all` 两套 schema 演进路径并存** | `main.py:30-84` |
| A-42 | **【已核实】零测试、零 CI**。`find` 结果中所有测试文件均在 `.venv/Lib/site-packages/` 下（第三方库自带）；无 `.github/workflows` | 全仓库 |
| A-43 | COCO 转换假设 `category_id` 从 0 连续编号，稀疏 id 的合法数据集会导致类索引错位 | `dataset.py:337` |
| A-45 | 无请求级超时/熔断；DB 无 `statement_timeout`，慢查询可无限期占用连接；视频与批量检测可长期占用 worker | `database.py:10-17` |

### 3.2 前端

| 编号 | 问题 | 位置 |
|---|---|---|
| A-15 | 批量检测后「重新检测」按钮**恒不可用**：只认 `lastImageFile`，而批量流程从不设置它，`resetDetection()` 还会清空它。按钮在非 camera 模式下无条件渲染 | `DetectionPage.vue:597-605` vs `:697-725` |
| A-16 | 401 双重错误提示：`request.js` 在跳转登录后**仍 reject**，各页 `catch` 再弹一次业务文案，把"登录已过期"掩盖成"检测失败，请稍后重试" | `utils/request.js:28-33` |
| A-32 | `DetectionPage.vue` **1306 行**，单文件揉进 4 个功能：上传表单、4 条检测链路、摄像头实时管线（含 IoU/EMA 算法）、canvas 绘制引擎。约 30 个顶层 ref/let、12 个模块级可变变量。另有**三份结构相同的模板**重复（camera 那次独缺 `@redetect` 绑定） | `DetectionPage.vue` |
| A-33 | **鉴权状态无单一来源**：凭据读取散落 3 处、清除逻辑重复 4 处，store 只是其中一个副本，`request.js` 与路由守卫都绕过 store 直读 storage → store 里 token 的变化不影响另外两处。且 `userInfo` 不持久化，首屏为空 → 管理员菜单与审核 Tab **晚一拍出现** | `utils/request.js:12`；`router/index.js:98`；`stores/user.js:18` |
| A-34 | 历史页直接渲染英文 `class_name`（如 `rice_leaf_roller`），而检测页与图鉴浮窗都用 `chinese_name` → 同一份数据两种呈现 | `HistoryPage.vue:104-105` |
| A-35 | 数据集下载按**当前用户 ID** 寻址而非转换任务；`userInfo` 未加载时直接报错，而该页挂载时**不触发** `fetchUserInfo` → 硬刷新后直接进该页，转换能成功、下载必失败 | `DatasetToolsPage.vue:70-91` |
| A-36 | 无 404 通配路由，未匹配路径渲染**空白页** | `router/index.js` |
| A-37 | 重复实现：日期格式化 4 处且行为不一（3 种格式、2 个不同函数名）；状态码→中文映射另有 3 份；「按 class_id 聚合物种」有 2 份**语义不同**却同名同目的的实现。无 `utils/format.js` | 各文件 |
| A-44 | 【未验证】`torch.cuda.get_device_properties(0).total_mem` 疑似 API 名称错误（PyTorch 2.x 已更名为 `total_memory`）。该行不在 `try` 内，仅在 GPU 可用时执行 → **只在真正有 GPU 的机器上崩**。未实测 | `train.py:191` |

### 3.3 训练与数据管线

| 编号 | 问题 | 位置 |
|---|---|---|
| A-17 | `load_classes` 不跳 `#` 注释行（只过滤空行），而官方示例 `classes_example.txt` 自带 3 行注释（含一行"使用方法"的调用命令）→ 按文档执行，类别 0/1/2 会变成注释文本，**102 类整体偏移 3 位**，`nc` 变 105 | `convert_dataset.py:414`；`classes_example.txt:1-3` |
| A-18 | 版本号在 `model.train()` **之前**就落库，失败/中断的 run 同样推进 `current_version` 并追加一条空 metrics 记录 | `train.py:162`；`train_local.py:232` |

---

## 4. 🟢 值得保留的好设计

这些是 v1 里真正做对的部分，v2 **直接复用**。

| 编号 | 设计 | 位置 | 为什么好 |
|---|---|---|---|
| G-01 | **Lua 原子「比对即删」** | `redis_utils.py:60-70` | 验证码校验杜绝 `GET→比对→DEL` 之间的并发重放。全仓库最扎实的并发处理 |
| G-02 | **Lua `INCR` + 首次 `EXPIRE`** | `redis_utils.py:52-70` | 消除"两条命令之间崩溃导致计数永不过期"的窗口 |
| G-03 | **fail-open / fail-closed 双模降级 + 30s 熔断** | `redis_utils.py:72-94, 242-246` | 缓存类失败静默直连 DB；安全类失败抛异常拒绝服务，且注释明确写了"安全边界不允许静默放行"。熔断避免每请求卡满 socket 超时，`time.monotonic()` 基准、熔断期内不重复刷日志。**设计意图最清晰的一处** |
| G-04 | **`token_version` 全端强制登出** | `auth_utils.py:78-83` | 改密码 / 禁用账号时 +1，所有已签发凭据立即失效。比维护 jti 黑名单优雅。附带好处：`role` claim 冗余而判据查库，角色变更立即生效 |
| G-05 | **ZIP 路径穿越防护** | `dataset.py:66-72` | realpath 前缀校验，优于多数同类实现 |
| G-06 | **流式分块写盘 + 超限即删** | `file_utils.py:26-34` | 上传大小限制实现是正确的（可惜数据集模块没有复用） |
| G-07 | **短信限流的顺序设计** | `sms.py:97-134` | 先抢 60s 间隔锁 → 再存码 → 最后才计数（避免存码失败却白烧配额）；超限时**回滚已写的验证码**；失败锁定检查**必须在比对之前**（否则锁定期内输对正确码仍会放行）。三处都有注释说明动机 |
| G-08 | **密码学安全随机源** | `sms.py:87` | `secrets.randbelow(1000000)` 而非 `random` |
| G-09 | **用 `scan_iter` 替代 `KEYS`** | `redis_utils.py:189` | 注释明确"避免 KEYS 阻塞 Redis" |
| G-10 | **连接池自愈** | `database.py:10-17` | `pool_pre_ping=True` + `pool_recycle=3600`，避免拿到已被服务端关闭的连接 |
| G-11 | **模型热更新** | `detection_service.py:311-330` | 每次检测前比较文件路径与 mtime，变化则持锁重载 → "训练脚本覆盖文件即生效"的轻量 MLOps |
| G-12 | **视频跨帧 IoU 追踪去重** | `detection_service.py:508-592` | 自研轻量 tracker（无额外依赖），按轨迹计数而非按帧计数。已知取舍：贪心匹配非匈牙利算法，密集虫群下 ID 易跳变；`confidence` 取 max 会让汇总偏乐观——**这两个取舍要写进文档而不是藏起来** |
| G-13 | **摄像头前端管线** | `DetectionPage.vue:861-930` | 半分辨率 + JPEG q=0.5 降采样、IoU>0.3 匹配后 EMA(α=0.6) 平滑、600ms 滞留框、独立 rAF 绘制循环、连续 5 次失败自动停。**四种能力里唯一有真实前端算法的一条** |
| G-14 | **首个注册用户自动成为管理员** | `main.py:48-56` | 优雅解决了"冷启动时第一个管理员从哪来" |
| G-15 | **不安全默认凭据启动告警** | `config.py:77-95` | 启动时检测 4 项默认凭据并告警（可惜只告警不阻断 → `NFR-S2` 要改成 fail-fast） |
| G-16 | **缓存显式绑定 IPv4** | `config.py:37` | `REDIS_HOST` 默认 `127.0.0.1` 而非 `localhost`，注释说明是为避开 IPv6 `::1` 的首轮超时——**说明踩过这个坑** |
| G-17 | **`HTTPException` 正确透传** | `detection.py:163-164` | 视频路径显式 `except HTTPException: raise`，保住了 413 的状态码语义（可惜 `/single` 没这么写 → `A-08`） |

---

## 5. v1 的能力清单（从代码反推的需求）

用于核对 `requirements.md` 的覆盖完整性。

1. 多用户 Web 平台：注册/登录（JWT 24h）、两档角色、管理员管用户启停与角色、首个注册者自动成为管理员
2. YOLO 病虫害检测：单图、批量图、视频、摄像头单帧四种能力；两套模型可切换；结果图带美化标注（圆角框 + 四角装饰 + 半透明填充 + 置信度进度条）；中英双语类别名
3. 视频检测跨帧去重计数：按轨迹计虫数 + 类别汇总 + 关键帧截图 + 标注视频
4. 模型热更新：覆盖 `models/` 下文件即自动生效；版本化文件发现；手动重载；版本历史（预留）
5. 检测历史：按用户隔离的分页/关键词/状态查询、单条与批量删除
6. 数据看板：全平台今日量 + 个人累计量 + 活跃天数，60s 缓存，管理员可清缓存
7. 数据集格式转换：Web 上传 ZIP（VOC/XML/COCO/CSV）→ 转 YOLO + 生成 `data.yaml` + 打包下载
8. 讨论区（审核制 UGC）：发帖（可带图）→ 管理员审核 → 展示；评论、置顶、删除
9. 102 类病虫害图鉴：静态百科数据，公开可读
10. 短信验证码演示：60s 间隔 + 5 次/日 + 连续错误锁定；未接网关、未打通账号体系
11. 基础设施与可观测性：缓存熔断降级、限流 fail-closed 语义、不安全默认凭据启动告警、连接池自愈
12. 前端壳：14 条路由（全懒加载）、13 个页面组件、单一 Pinia store、axios 单实例双拦截器

**已知预留但未接线**：对象存储（`minio_utils.py`）、数据集验证器管道（`validators.py`）、统一日志模块（`logging_utils.py`）、异步检测状态机（`status` 字段）。
