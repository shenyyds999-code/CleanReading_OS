# CleanReading OS

> 基于 Flask 的三端一体线上图书借阅管理平台

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1-green.svg)](https://flask.palletsprojects.com/)
[![Version](https://img.shields.io/badge/version-0.4.4-orange.svg)](CHANGELOG.md)

CleanReading OS 是一个面向校园图书馆的借阅管理系统。后端提供一套 REST API，同时服务三个前端：读者客户端、管理后台、自助借书机。系统包含信誉分、借还闭环、评论互动、答题称号、AI 出题等能力。

---

## 功能特性

**读者端（client）**

- 图书搜索、分类浏览、热门推荐、ISBN 自动填充
- 借书（受信誉分与借阅上限约束）、上传照片还书
- 图书评分（1–5 星）、评论 / 回复 / 点赞 / 举报
- 学习中心答题闯关，通过后获得称号
- 借阅记录、信誉分流水、站内通知
- 个性化设置（主题深浅色、看板娘开关等）
- Live2D 雷姆看板娘

**管理端（admin）**

- 仪表盘统计与站点名称配置
- 图书 CRUD、ISBN 信息与封面获取
- 还书审核（完好 / 污损）、捐书审核、图片审核
- 评论管理
- 用户管理、信誉分调整、删除用户（仅超级管理员）

**借书机端（kiosk）**

- 极简触屏界面，扫码 / 输入 ISBN 快速借书
- 通过 `X-Client-Type: kiosk` 请求头与白名单接口交互

**后端能力**

- JWT 认证（HS256，默认 24 小时）+ jti 黑名单
- 角色权限：读者(1) / 图书管理员(2) / 超级管理员(3)
- 缓存：Redis 优先，连接失败自动降级为进程内缓存
- 固定窗口接口限流（登录 / 注册 10 次/分钟）
- APScheduler 每小时检查超期借阅并扣减信誉分
- 统一响应格式、XSS 过滤、ORM 防注入

---

## 技术栈

| 层次 | 技术 |
| --- | --- |
| 后端 | Python 3.10+ / Flask 3.1（应用工厂 + Blueprint） |
| 数据库 | MySQL 8.0，开发环境可用 SQLite |
| ORM / 迁移 | Flask-SQLAlchemy 3.1 / Flask-Migrate |
| 认证 | PyJWT + 内存/Redis 黑名单 |
| 缓存 | Redis 7 + 进程内 `SimpleCache` 降级 |
| 定时任务 | APScheduler 3.x |
| 前端 | 原生 HTML5 + CSS3 + JavaScript（Bootstrap 5） |
| 外部服务 | DeepSeek API（AI 出题）、OpenLibrary API（ISBN 查询） |
| 部署 | Docker / docker-compose |

---

## 项目结构

```
CleanReading/
├── serve.py                  # 启动入口（0.0.0.0:5000）
├── config.py                 # 配置类，读取 .env
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
│
├── app/
│   ├── __init__.py           # create_app / 蓝图注册 / 静态路由 / seed 命令 / 定时任务
│   ├── api/                  # 10 个蓝图
│   │   ├── auth.py           # 注册、登录、登出、当前用户、改名改密
│   │   ├── books.py          # 列表、详情、热门、评分、推荐、ISBN/封面
│   │   ├── borrow.py         # 借书、借阅状态
│   │   ├── return_api.py     # 提交还书、审核还书、待审核、我的记录
│   │   ├── comment.py        # 评论增删查、点赞、举报
│   │   ├── learn.py          # 取题、交卷、称号、题库管理、AI 出题
│   │   ├── settings_api.py   # 用户个性化设置
│   │   ├── notification.py   # 通知列表、未读数、已读
│   │   ├── admin_api.py      # 仪表盘、书籍/用户管理、审核、图片上传
│   │   └── system_api.py     # 站点配置
│   ├── models/
│   │   └── models.py         # 16 张表
│   ├── services/             # 业务逻辑层（每个领域一个 service）
│   └── utils/
│       ├── cache.py          # Redis / 内存缓存、缓存 key、限流计数
│       ├── jwt_helper.py     # Token 生成与校验、权限装饰器
│       ├── kiosk.py          # 借书机白名单
│       ├── rate_limiter.py   # 限流装饰器
│       ├── response.py       # 统一响应
│       └── security.py       # 内容清洗
│
├── client/                   # 读者端页面
├── admin/                    # 管理端页面
├── kiosk/                    # 借书机页面
├── migrations/               # Alembic 迁移脚本
├── uploads/                  # 上传文件（还书照片、头像等）
└── issues/                   # 版本问题与优化记录
```

---

## 数据模型（16 张表）

| 表 | 说明 | 表 | 说明 |
| --- | --- | --- | --- |
| `users` | 用户 | `titles` | 称号 |
| `credit_logs` | 信誉分流水 | `user_titles` | 用户称号 |
| `books` | 图书 | `donations` | 捐书申请 |
| `book_ratings` | 图书评分 | `image_reviews` | 图片审核 |
| `borrow_records` | 借阅记录 | `user_settings` | 个性化设置 |
| `comments` | 评论 / 回复 | `notifications` | 站内通知 |
| `comment_likes` | 评论点赞 | `system_config` | 系统配置 |
| `quiz_questions` | 题库 | `quiz_attempts` | 答题记录 |

核心规则：

- 用户初始信誉分 5 分；超期按周扣分，捐书可加分
- 信誉分不达标或达到借阅上限时禁止借书
- 答题正确率 ≥ 80% 视为通过，可获得对应称号

---

## 快速开始（本地）

### 1. 准备环境

- Python 3.10+
- 可选：MySQL 8（默认）、Redis 7（不启用也可运行）

```bash
git clone <your-repo-url>
cd CleanReading
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux / macOS
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
copy .env.example .env       # Windows
# cp .env.example .env       # Linux / macOS
```

本地快速体验可直接使用 SQLite，编辑 `.env`：

```env
SECRET_KEY=dev-secret-key
JWT_SECRET_KEY=dev-jwt-secret
DATABASE_URL=sqlite:///library_system.db
REDIS_ENABLED=false
DEEPSEEK_API_KEY=
```

如果使用 MySQL：

```env
DATABASE_URL=mysql+pymysql://root:password@127.0.0.1:3306/library_system
```

> 首次启动时应用会自动执行 `db.create_all()` 建表，无需手动迁移。

### 3. 写入种子数据

```bash
flask --app serve seed
```

种子数据包含 3 个账号、4 本图书、4 个称号、6 道题目。

### 4. 启动

```bash
python serve.py
```

访问地址：

| 入口 | 地址 |
| --- | --- |
| 读者客户端 | http://127.0.0.1:5000/client/ |
| 管理后台 | http://127.0.0.1:5000/admin/ |
| 借书机 | http://127.0.0.1:5000/kiosk/ |
| 健康检查 | http://127.0.0.1:5000/api/health |

### 种子账号

| 角色 | 用户名 | 密码 | role |
| --- | --- | --- | --- |
| 超级管理员 | `admin` | `admin123` | 3 |
| 图书管理员 | `librarian` | `lib123` | 2 |
| 读者 | `reader` | `reader123` | 1 |

> 注册接口固定创建读者账号（role=1），管理员账号只能由超管在后台或种子数据产生。

---

## Docker 部署

```bash
docker-compose up -d      # 启动 MySQL + Redis + 应用
docker-compose logs -f    # 查看日志
docker-compose down       # 停止
```

服务地址：http://localhost:5000

`docker-compose.yml` 默认使用：

- MySQL：数据库 `library_system`，账号 `library / librarypassword`
- Redis：`redis://redis:6379/0`
- 应用端口：5000，挂载 `./uploads`

首次启动后仍需执行一次种子命令：

```bash
docker-compose exec app flask --app serve seed
```

---

## 环境变量

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `SECRET_KEY` | `dev-secret-key` | Flask 密钥 |
| `JWT_SECRET_KEY` | `dev-jwt-secret` | JWT 签名密钥 |
| `JWT_EXPIRATION_HOURS` | `24` | Token 有效期（小时） |
| `DATABASE_URL` | MySQL 连接串 | 数据库连接 |
| `REDIS_ENABLED` | `true` | 是否启用 Redis |
| `REDIS_URL` | `redis://127.0.0.1:6379/0` | Redis 地址 |
| `CACHE_DEFAULT_TTL` | `300` | 默认缓存秒数 |
| `CACHE_BOOK_LIST_TTL` | `120` | 图书缓存秒数 |
| `RATE_LIMIT_ENABLED` | `true` | 是否开启限流 |
| `DEEPSEEK_API_KEY` | 空 | AI 出题所需，未配置时该功能不可用 |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com` | AI 接口地址 |

---

## API 概览

统一响应：

```json
{ "code": 200, "message": "success", "data": {} }
```

分页数据位于 `data`：`{ "items": [], "total": 0, "page": 1, "per_page": 20 }`

### 认证 `/api/auth`

| 方法 | 路径 | 说明 | 权限 |
| --- | --- | --- | --- |
| POST | `/register` | 注册（固定读者） | 公开 |
| POST | `/login` | 登录 | 公开 |
| POST | `/logout` | 登出（Token 拉黑） | 登录 |
| GET | `/me` | 当前用户 | 登录 |
| POST | `/change-username` | 修改用户名 | 登录 |
| POST | `/change-password` | 修改密码 | 登录 |

### 图书 `/api/books`

| 方法 | 路径 | 说明 | 权限 |
| --- | --- | --- | --- |
| GET | `` | 列表 / 搜索（`q`、`search_type`、`page`、`per_page`） | 公开 |
| GET | `/popular` | 热门图书 | 公开 |
| GET | `/<id>` | 图书详情 | 公开 |
| POST | `/<id>/rating` | 评分 | 登录 |
| GET | `/<id>/recommendations` | 相关推荐 | 公开 |
| GET | `/isbn-lookup` | ISBN 查询 | 公开 |
| GET | `/cover-search` | 封面搜索 | 公开 |
| POST | `/cover-download` | 下载封面 | 管理 |

### 借还 `/api/borrow`、`/api/return`

| 方法 | 路径 | 说明 | 权限 |
| --- | --- | --- | --- |
| GET | `/api/borrow/status` | 借阅状态 | 登录 |
| POST | `/api/borrow/request` | 借书 | 登录 |
| POST | `/api/return/submit` | 提交还书 | 登录 |
| GET | `/api/return/my` | 我的借阅 | 登录 |
| GET | `/api/return/pending` | 待审核还书 | 管理 |
| POST | `/api/return/confirm` | 确认还书 | 管理 |

### 评论 `/api/comments`

| 方法 | 路径 | 说明 | 权限 |
| --- | --- | --- | --- |
| GET | `` | 评论列表 | 公开 |
| POST | `` | 发表评论 / 回复 | 登录 |
| POST | `/<id>/like` | 点赞 / 取消点赞 | 登录 |
| POST | `/<id>/report` | 举报 | 登录 |
| DELETE | `/<id>` | 删除自己的评论 | 登录 |

### 学习 `/api/learn`

| 方法 | 路径 | 说明 | 权限 |
| --- | --- | --- | --- |
| GET | `/questions?book_id=` | 取题（不含答案） | 登录 |
| POST | `/submit` | 交卷 | 登录 |
| GET | `/titles` | 我的称号 | 登录 |
| GET/POST | `/admin/questions` | 题库列表 / 新增 | 管理 |
| DELETE | `/admin/questions/<id>` | 删除题目 | 管理 |
| POST | `/ai/generate` | AI 生成题目 | 管理 |

### 设置 / 通知 / 系统

| 方法 | 路径 | 说明 | 权限 |
| --- | --- | --- | --- |
| GET/POST | `/api/user/settings` | 个性化设置 | 登录 |
| GET | `/api/notifications` | 通知列表 | 登录 |
| GET | `/api/notifications/unread-count` | 未读数 | 登录 |
| POST | `/api/notifications/<id>/read` | 单条已读 | 登录 |
| POST | `/api/notifications/read-all` | 全部已读 | 登录 |
| GET | `/api/system/config` | 站点配置 | 公开 |
| PUT | `/api/system/config` | 修改站点名称 | 超管 |
| GET | `/api/health` | 健康检查 | 公开 |

### 管理端 `/api/admin`

| 方法 | 路径 | 说明 | 权限 |
| --- | --- | --- | --- |
| GET | `/stats` | 仪表盘 | 管理 |
| GET/POST | `/books` | 书籍列表 / 新增 | 管理 |
| PUT/DELETE | `/books/<id>` | 编辑 / 删除 | 管理 |
| GET | `/returns` | 还书记录 | 管理 |
| GET | `/donations` | 捐书列表 | 管理 |
| POST | `/donations/review` | 审核捐书 | 管理 |
| GET | `/images` | 图片审核列表 | 管理 |
| POST | `/images/review` | 审核图片 | 管理 |
| GET | `/comments` | 评论管理 | 管理 |
| DELETE | `/comments/<id>` | 删除评论 | 管理 |
| POST | `/upload-image` | 上传图片 | 管理 |
| GET | `/users` | 用户列表 | 超管 |
| POST | `/users/credit` | 调整信誉分 | 超管 |
| DELETE | `/users/<id>` | 删除用户 | 超管 |

### 错误码

| code | 含义 |
| --- | --- |
| 200 | 成功 |
| 400 | 参数错误 |
| 401 | 未登录 / Token 失效 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 429 | 请求过于频繁 |
| 500 | 服务器错误 |

---

## 安全说明

- 密码使用 Werkzeug 哈希存储，不可逆
- 注册接口不接受 `role` 参数，避免越权提权
- 评论等内容经 bleach 清洗，防 XSS
- 删除用户 / 图书时级联清理关联数据，避免脏数据与外键报错
- 生产环境请务必修改 `SECRET_KEY`、`JWT_SECRET_KEY` 与数据库密码，并开启 Redis

---

## 许可证

MIT License
