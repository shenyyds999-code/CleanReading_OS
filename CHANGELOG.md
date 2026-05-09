# 更新日志

本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/) 规范。

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
| 0.2.0 | `v0.2.0` | 2026-05-09 | Phase 2 核心借阅闭环 |
| 0.1.0 | `v0.1.0` | 2026-05-09 | Phase 1 骨架搭建 + Redis 缓存层 |
