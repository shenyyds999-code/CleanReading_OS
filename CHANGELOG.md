# 更新日志

本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/) 规范。

---

## [0.4.2] - 2026-05-13

### 新增

- **借书机端屏幕键盘** — 点击输入框弹出网页虚拟键盘，适配触摸屏操作
  - 字母/数字键 + 空格/退格/回车/关闭功能键
  - 大小写切换（Shift 键，高亮指示当前状态）
  - 智能拼音输入（拼音模式 + 候选字选择，覆盖常用汉字）
- **扫描枪适配** — 借书机端支持 USB 扫描枪即插即用
  - `inputmode="none"` 防止触摸屏弹出系统键盘
  - 自动聚焦输入框，监听回车键自动触发搜索
  - 扫描枪输入完成后自动执行借阅查询

### 优化

- **借阅按钮状态修复** — 修复图书详情页借阅按钮卡在"检查中..."的问题
- **管理后台登录页主题色** — 修复默认粉色主题未加载的问题
- **登录错误提示** — 密码错误时显示 Toast 提示，不再刷新页面
- **搜索后热门推荐** — 搜索结果页不再显示"热门推荐"区块

### 工具

- **扫描枪模拟脚本** — `kiosk/scanner-simulator.js` 可在浏览器控制台模拟扫描枪快速输入

---

## [0.4.1] - 2026-05-10

### 修复

- **借阅标签仅本人可见** — 热门图书列表中的"借过N次"标签现在只显示当前登录用户自己的借阅次数，而非全局统计
- **站点名称闪烁** — `.site-name` 元素默认 `visibility: hidden`，`loadSiteName()` 完成后才显示，消除从"校园图书馆"到自定义名称的闪烁
- **评论点赞与操作权限**
  - 点赞改为 toggle 模式（点一次点赞，再点一次取消），新增 `CommentLike` 表防重复
  - 自己的评论显示"删除"按钮，他人评论显示"举报"按钮
  - 新增 `DELETE /api/comments/<id>` 端点，用户可删除自己的评论
- **图书详情页表格背景** — 修复表格背景色与深色环境不一致的问题，统一使用 `#2E3134` 背景色和 `#e0e0e0` 文字颜色

### 新增

- **还书确认通知** — 管理员确认还书后，系统自动向用户发送通知（区分 完好 / 轻微污损 / 严重破损 三种内容）
- **评论删除通知** — 被举报的评论被管理员删除后，系统通知评论作者"评论已被移除"

### 优化

- 图书详情页表格标签颜色从 `text-muted` 优化为 `rgb(33,37,41)`

---

## [0.4.0] - 2026-05-10

### 新增 · Phase 4 管理后台与全流程贯通

#### 管理端后台 (admin/)
- 独立登录页 `login.html` — 角色验证，仅 role 2/3 可登录
- 管理主页 `index.html` — SPA 侧边栏 + 7 面板一体化
  - **仪表盘** — 8 项统计卡片（图书总量/用户总数/在借/待审核还书/捐书/图片/被举报评论/超期）+ 系统配置（站点名称修改，role=3）
  - **书籍管理** — CRUD 操作 + ISBN 自动填充（OpenLibrary API）
  - **还书审核** — 列表 + 完好/污损两级确认
  - **捐书审核** — 列表 + 通过/拒绝 + 拒绝原因
  - **图片审核** — 网格展示 + 通过/拒绝
  - **评论管理** — 列表 + 被举报过滤 + 删除
  - **用户管理** — 仅 super_admin 可见，支持信誉分调整

#### 管理端 API
- `GET /api/admin/stats` — 仪表盘统计
- `GET/POST /api/admin/books` — 书籍列表/新增
- `PUT/DELETE /api/admin/books/<id>` — 编辑/删除
- `GET /api/admin/returns` — 还书记录列表
- `GET /api/admin/donations` — 捐书列表
- `POST /api/admin/donations/review` — 审核捐书
- `GET /api/admin/images` — 图片审核列表
- `POST /api/admin/images/review` — 审核图片
- `GET /api/admin/comments` — 评论管理
- `DELETE /api/admin/comments/<id>` — 删除评论
- `GET /api/admin/users` — 用户列表（super_admin）
- `POST /api/admin/users/credit` — 信誉分调整（super_admin）

#### 系统配置
- `GET /api/system/config` — 获取站点配置
- `PUT /api/system/config` — 更新站点名称（super_admin）

#### 部署
- `deploy.sh` — Ubuntu 一键部署脚本（系统依赖/MySQL/Gunicorn/Nginx/虚拟环境）

---

## [0.3.0] - 2026-05-09

### 新增 · Phase 3 用户生态扩展

#### 评论模块
- `POST /api/comments` — 发表评论（文本 + 图片URL，敏感词过滤 1005，XSS 清洗）
- `GET /api/comments?book_id=` — 获取图书评论列表（分页）
- `POST /api/comments/<id>/like` — 点赞评论
- `POST /api/comments/<id>/report` — 举报评论（`is_reported=True`）
- 服务层 `app/services/comment_service.py`

#### 学习中心 + 称号系统
- `GET /api/learn/questions?book_id=` — 获取图书题目（随机抽样，默认5题）
- `POST /api/learn/submit` — 提交答题（自动评分，正确率≥80%通过）
- `POST /api/learn/admin/questions` — 管理员添加题目
- `GET /api/learn/titles` — 获取用户已获称号列表
- 自动称号授予：首次借阅→初识书香，累计10本→阅读达人，三体答题通过→三体学者，活着答题通过→文学鉴赏家
- 0分用户禁止使用学习中心
- 服务层 `app/services/quiz_service.py`

#### AI 对话
- `POST /api/ai/chat` — AI 对话（琪露诺人设 + 书名上下文，DeepSeek API 无状态调用）
- 未配置 API Key 时返回友好提示
- 服务层 `app/services/ai_service.py`

#### 个性化设置
- `GET /api/user/settings` — 获取用户设置（theme_color/background/learning_trigger_mode）
- `POST /api/user/settings` — 更新设置（支持颜色选择、背景图上传、学习触发模式）
- 背景图上传写入 `image_reviews` 待审核
- 服务层 `app/services/settings_service.py`

#### 通知系统
- `GET /api/notifications` — 获取通知列表（含未读数）
- `GET /api/notifications/unread-count` — 未读计数
- `POST /api/notifications/<id>/read` — 标记已读
- `POST /api/notifications/read-all` — 全部标为已读
- 服务层 `app/services/notification_service.py`

#### 封面与背景
- **OpenLibrary 封面** — `openlibrary_cover_url(isbn, size)` 自动从 ISBN 获取封面，API 返回 `cover_image_url` 优先本地 → 回退 OpenLibrary
- **网页背景** — 全部 6 个页面 + 借书机端统一使用 `bg.png` 作为背景（`background-blend-mode: soft-light`）

#### 客户端前端新增
- **图书详情页** `book.html` — 重写加入评论区（发表/点赞/举报/计数）+ AI 聊天浮动窗（琪露诺气泡对话）+ 答题闯关入口
- **学习中心** `learn.html` — 题目展示（选择/填空/简答三类渲染）、提交评分、称号展示
- **个性化设置** `settings.html` — 6 色主题选择器、背景图上传、学习触发模式开关
- **通知中心** `notifications.html` — 通知列表、未读高亮、单条已读/全部已读
- **导航栏升级** — index.html + mine.html 加入通知铃铛（红点 + 30s 轮询）+ 设置齿轮入口

#### 种子数据增强
- 新增 6 道题库题目（三体×3 / 活着×2 / 百年孤独×1）

---

## [0.2.0] - 2026-05-09

### 新增 · Phase 2 核心借阅闭环

#### 图书管理模块
- `GET /api/books` — 图书搜索（支持 `?q=&type=fuzzy|exact&page=&per_page=`，缓存 2 分钟）
- `GET /api/books/<id>` — 图书详情（缓存 2 分钟，借出时自动清除）
- 服务层 `app/services/book_service.py` — 搜索/详情业务逻辑，返回 `can_borrow` 状态

#### 借书模块
- `POST /api/borrow/request` — 借书请求（需 `{book_id}`）
- 信誉分校验：≥5分可借4本/31天，3-4分可借2本/15天，≤2分拒借
- 馆藏校验：`available_copies > 0` 且 `status == 可借`
- 借阅上限校验：自动统计当前借阅中记录数
- 借书成功自动扣减 `available_copies`，归还时恢复
- 服务层 `app/services/borrow_service.py`

#### 还书模块
- `POST /api/return/submit` — 还书提交（`multipart/form-data`，图片必填，最多3张，格式校验）
- 提交后状态 → "已提交归还"，图片写入 `image_reviews` 表待审核
- `GET /api/return/my` — 我的借阅记录（分页，按借阅日期倒序）
- `GET /api/return/pending` — 管理员待确认归还列表（`@admin_required`）
- `POST /api/return/confirm` — 管理员确认归还（支持 完好/轻微污损/严重破损 三级）
  - 完好：无扣分，直接归档
  - 轻微污损：扣1分 + 写入 `credit_logs`
  - 严重破损：扣2分 + 写入 `credit_logs`
- 服务层 `app/services/return_service.py`

#### 信誉分定时任务
- APScheduler 后台调度器，每小时检查一次超期记录
- 每超过应还日期7天自动扣1分
- 写入 `credit_logs` 和 `notifications` 通知
- 0分用户不再扣分
- `app/services/scheduler_service.py` — `check_overdue_and_penalize()` 函数

#### 借书机端后端拦截
- `app/utils/kiosk.py` — `@kiosk_blocked` 装饰器
- 检测 `X-Client-Type: kiosk` 请求头
- 允许：`/api/auth/*`, `/api/borrow/*`, `/api/books/*`, `/api/health`
- 拦截：`/api/return/submit`, `/api/comment/*`, `/api/learn/*`, `/api/ai/*`, `/api/user/settings`, `/api/donations/*`
- 拦截返回 `403 借书机端不支持此操作`

#### 客户端前端 (client/) 更新
- **首页** `index.html` — 重写为图书搜索页：模糊/精确搜索、图书卡片网格、加载/空/阻断三态、信誉分≤2分显示锁定提示
- **图书详情** `book.html` — 图书信息展示 + 借阅按钮（确认框含应还日期/借阅天数）+ 防重复提交
- **我的借阅** `mine.html` — 借阅列表表格 + 还书入口（图片上传预览、多图选择、防重复提交、格式/大小校验）

#### 借书机端前端 (kiosk/) 🆕
- `kiosk/index.html` — 极简触屏借书界面：登录→ISBN搜索→确认借阅→结果展示
- `kiosk/js/app.js` — 专用工具模块，默认携带 `X-Client-Type: kiosk` 请求头
- 按钮大尺寸适配触屏，信誉分不足时显示阻断提示

#### 路由更新
- 借书机端静态文件路由 `/kiosk/` → `kiosk/` 目录
- 文件上传静态路由 `/uploads/<filename>` → `uploads/` 目录

---

## [0.1.0] - 2026-05-09

### 新增 · Phase 1 骨架搭建

#### 后端骨架
- Flask 工厂模式应用 (`app/__init__.py`)
- 配置类 `config.py`（环境变量驱动，含 Redis / 限流参数）
- 依赖管理 `requirements.txt`（flask, sqlalchemy, jwt, apscheduler, redis, bleach 等 12 个包）
- `run.py` 启动入口 + `.env.example` 模板 + `.gitignore`

#### 数据库 (13 张核心表)
- `users` — 用户表（username, password_hash, role, credit_score, avatar_url）
- `credit_logs` — 信誉分变动日志（change_amount, reason, detail）
- `books` — 图书信息（title, author, isbn, total_copies, available_copies 等）
- `borrow_records` — 借阅记录（borrow_date, due_date, return_date, status, damage_level, fine_score）
- `comments` — 评论（content, image_urls, parent_id, like_count, is_reported）
- `quiz_questions` / `quiz_attempts` — 学习中心题库与答题记录
- `titles` / `user_titles` — 称号系统
- `donations` — 捐书申请（status 审核流）
- `image_reviews` — 图片审核（image_type, status）
- `user_settings` — 用户个性化设置
- `notifications` — 站内通知（type, is_read）

#### 认证模块
- `POST /api/auth/register` — 用户注册（默认 role=1, credit_score=5）
- `POST /api/auth/login` — 用户登录（返回 JWT）
- `POST /api/auth/logout` — 退出登录（JWT 加入黑名单）
- `GET /api/auth/me` — 获取当前用户信息（支持缓存命中）
- `@login_required` / `@admin_required` 装饰器
- 密码 Werkzeug 哈希 + BLeach XSS 过滤

#### 工具层
- **缓存层** `app/utils/cache.py`
  - Redis 连接管理（连接池，ping 验证，断开自动降级）
  - `SimpleCache` 内存缓存（`RLock` 线程安全，LRU 淘汰）
  - `cache_get/set/delete/exists/incr/keys/flush` 统一接口
  - `@cache_result(prefix, ttl)` — 自动缓存函数返回值
  - `@cache_invalidate(prefix)` — 写入后自动清空相关缓存
  - `CacheKey` 命名空间 (`lib:{module}:{entity}:{key}`)
- **限流中间件** `app/utils/rate_limiter.py`
  - 滑动窗口计数器，支持按秒/分钟/小时配置
  - `@rate_limit(limit_str='10/minute')` 装饰器
  - 自动设置 `X-RateLimit-*` 响应头
- **JWT 增强** `app/utils/jwt_helper.py`
  - 每次登录生成唯一 `jti` (uuid4)
  - 登出后 `jti` 写入缓存黑名单（TTL = JWT 有效期）
  - Token 验证时检查黑名单
- **统一响应** `app/utils/response.py` — `success()`, `error()`, `paginated()`
- **安全工具** `app/utils/security.py` — XSS 过滤 + 敏感词检测

#### API 健康检查
- `GET /api/health` — 返回服务状态 + 缓存层类型与状态

#### 客户端前端 (client/)
- `login.html` — 登录页（Bootstrap 5 响应式，表单验证，防重复提交）
- `register.html` — 注册页（二次密码确认）
- `index.html` — 首页（导航栏 + 信誉分徽章 + 退出按钮）
- `js/app.js` — 公共模块（`apiGet/apiPost`，Token 自动携带，401 自动跳转登录页，`showToast` 轻提示）

#### CLI 命令
- `flask seed` — 插入 3 个测试账号 + 4 本图书 + 4 个称号

#### 环境变量配置
- Redis 连接：`REDIS_URL`, `REDIS_ENABLED`, `REDIS_CONNECT_TIMEOUT`, `REDIS_SOCKET_TIMEOUT`
- 缓存 TTL：`CACHE_DEFAULT_TTL`, `CACHE_USER_TTL`, `CACHE_BOOK_LIST_TTL`
- 限流配置：`RATE_LIMIT_ENABLED`, `RATE_LIMIT_GLOBAL`, `RATE_LIMIT_AUTH`

---

## 版本标识

| 版本 | 标签 | 日期 | 说明 |
|------|------|------|------|
| 0.4.1 | `v0.4.1` | 2026-05-10 | 修复 + 通知增强 |
| 0.4.0 | `v0.4.0` | 2026-05-10 | Phase 4 管理后台与全流程贯通 |
| 0.3.0 | `v0.3.0` | 2026-05-09 | Phase 3 用户生态扩展 |
| 0.2.0 | `v0.2.0` | 2026-05-09 | Phase 2 核心借阅闭环 |
| 0.1.0 | `v0.1.0` | 2026-05-09 | Phase 1 骨架搭建 + Redis 缓存层 |
