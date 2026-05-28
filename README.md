# CleanReading OS

> 基于 Flask + MySQL 的三端分离线上借阅管理平台

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.4.2-orange.svg)](CHANGELOG.md)

---

## 项目简介

本项目为学校图书馆构建一套完整的线上借阅管理系统，核心特点：

- **三端分离** — 客户端（H5 全功能）、管理端（独立后台）、借书机端（极简触屏），共享同一后端 API
- **信誉分体系** — 用户初始 5 分，超期扣分、捐书加分，不同分数段对应不同借阅权限
- **学习激励** — 答题闯关系统，通过阅读检验获得称号
- **AI 助手** — 接入 DeepSeek API，以雷姆人设提供书籍问答，支持页面内容总结
- **Live2D 看板娘** — 雷姆角色，整合AI聊天面板，支持互动对话和页面总结，可点击隐藏/显示
- **权限分离** — 超级管理员(role=3) 管理全局，图书管理员(role=2) 管理书籍/还书
- **缓存层** — 支持 Redis（生产）和内存缓存（开发降级），内置 API 限流与 JWT 黑名单
- **站点名称可配** — 后台实时修改全站名称，默认 "CleanReading OS"

---

## 技术栈

| 层次     | 技术选代                                    |
| -------- | ------------------------------------------- |
| 后端框架 | Python 3.10+ / Flask (工厂模式)             |
| 数据库   | MySQL 8.0（开发可用 SQLite）                |
| ORM      | Flask-SQLAlchemy                            |
| 迁移     | Flask-Migrate (Alembic)                     |
| 认证     | JWT (PyJWT) + 黑名单机制                    |
| 缓存     | Redis 7.x + 内存降级 (RLock)                |
| 限流     | 滑动窗口计数器（内存 / Redis）              |
| 定时任务 | APScheduler                                 |
| 前端     | HTML5 + CSS3 + JavaScript + Bootstrap 5     |
| AI 接口  | DeepSeek API                                |
| 图书信息 | OpenLibrary API（ISBN 自动填充）             |
| 看板娘   | live2d-widget@3.0.5（雷姆）                 |
| 安全     | Werkzeug 密码哈希 / Bleach XSS 过滤 / ORM 防注入 |

---

## 系统架构

```
┌──────────┐  ┌──────────┐  ┌──────────┐
│  客户端    │  │  管理端    │  │  借书机端   │
│  :5000    │  │  :5000    │  │  :5000    │
│  /client/ │  │  /admin/  │  │  /kiosk/  │
└─────┬────┘  └─────┬────┘  └─────┬────┘
      └──────────────┼──────────────┘
                     │ Bearer JWT / X-Client-Type
          ┌──────────▼──────────┐
          │  Flask API :5000     │
          │  ┌────────────────┐ │
          │  │  限流中间件     │ │
          │  ├────────────────┤ │
          │  │  缓存层         │ │
          │  │  Redis / 内存   │ │
          │  ├────────────────┤ │
          │  │  权限校验       │ │
          │  │ login_required  │ │
          │  │ admin_required  │ │
          │  │ super_admin_req │ │
          │  └────────────────┘ │
          └──────────┬──────────┘
                     │
      ┌──────────────┼──────────────┐
┌─────▼─────┐  ┌─────▼─────┐  ┌─────▼─────┐
│   MySQL   │  │   Redis   │  │  内存降级   │
│   主存储   │  │  (可选)   │  │  自动回退   │
└───────────┘  └───────────┘  └───────────┘
```

---

## 项目结构

```
ClearReading/
├── run.py                          # 应用启动入口
├── config.py                       # 配置类（环境变量驱动）
├── requirements.txt                # Python 依赖
├── .env                            # 环境变量（不入库）
├── .env.example                    # 环境变量模板
├── .gitignore
│
├── app/
│   ├── __init__.py                 # Flask 工厂 + /api/health + seed 命令 + 定时任务
│   ├── api/
│   │   ├── auth.py                 # 认证蓝图 (register/login/logout/me)
│   │   ├── books.py                # 图书搜索/详情/热门/ISBN查询
│   │   ├── borrow.py               # 借书/借阅状态
│   │   ├── return_api.py           # 还书提交/确认/pending
│   │   ├── comment.py              # 评论的增删查
│   │   ├── learn.py                # 学习中心答题
│   │   ├── ai.py                   # AI 对话
│   │   ├── settings_api.py         # 用户个性化设置
│   │   ├── notification.py         # 站内通知
│   │   ├── admin_api.py            # 管理后台 API（仪表盘/书籍CRUD/用户管理/审核）
│   │   └── system_api.py           # 系统配置 API（站点名称等）
│   ├── models/
│   │   ├── __init__.py
│   │   └── models.py               # 14 张核心表 SQLAlchemy 模型
│   ├── services/
│   │   ├── auth_service.py         # 认证业务逻辑
│   │   ├── book_service.py         # 图书搜索/详情/OpenLibrary/热门
│   │   ├── borrow_service.py       # 借阅逻辑（含重复借阅检查）
│   │   ├── return_service.py       # 还书业务
│   │   ├── comment_service.py      # 评论业务
│   │   ├── quiz_service.py         # 答题/称号
│   │   ├── ai_service.py           # AI 对话
│   │   ├── settings_service.py     # 用户设置
│   │   ├── notification_service.py # 通知
│   │   ├── admin_service.py        # 管理后台业务
│   │   ├── system_service.py       # 系统配置
│   │   └── scheduler_service.py    # 超期扣分定时任务
│   └── utils/
│       ├── cache.py                # 缓存层 (Redis / 内存降级 / 装饰器)
│       ├── jwt_helper.py           # JWT 生成/验证/黑名单/登录/admin/super_admin 装饰器
│       ├── kiosk.py                # 借书机端访问控制
│       ├── rate_limiter.py         # API 频率限制中间件
│       ├── response.py             # 统一响应格式
│       └── security.py             # XSS 过滤 / 敏感词检测
│
├── client/                         # 客户端前端（H5 全功能）
│   ├── login.html / register.html  # 登录/注册
│   ├── index.html                  # 首页（搜索+热门推荐）
│   ├── book.html                   # 图书详情+评论+借阅
│   ├── mine.html                   # 我的借阅记录+还书
│   ├── learn.html                  # 学习中心答题
│   ├── settings.html              # 个性化设置
│   ├── notifications.html          # 通知中心
│   ├── img/                        # 图片资源（bg.png 背景等）
│   └── js/
│       ├── app.js                  # 全局工具（apiGet/apiPost/Token/站点名加载）
│       └── live2d-widget.js        # 雷姆看板娘
│
├── admin/                          # 管理端前端（独立后台 SPA）
│   ├── login.html                  # 管理员登录（角色验证）
│   ├── index.html                  # 管理主页（侧边栏+7面板一体化）
│   │                                #   - 仪表盘(统计+系统配置)
│   │                                #   - 书籍管理(CRUD+ISBN自动填充)
│   │                                #   - 还书审核(完好/污损确认)
│   │                                #   - 捐书审核
│   │                                #   - 图片审核
│   │                                #   - 评论管理
│   │                                #   - 用户管理(仅超级管理员)
│   ├── img/                        # 图片资源（bg-admin.png 背景等）
│   └── js/
│       └── admin.js                # 管理端工具（adminGet/Post/Put/Delete/站点名加载）
│
├── kiosk/                          # 借书机端（极简触屏）
│   ├── index.html                  # 借书机登录/ISBN扫描借书
│   ├── img/                        # 背景图片
│   └── js/
│       └── app.js                  # 借书机端 JS 工具
│
└── migrations/                     # Alembic 数据库迁移
```

---

## 数据库核心表 (14 张)

| 表名 | 说明 | 表名 | 说明 |
|------|------|------|------|
| `users` | 用户表 | `titles` | 称号表 |
| `credit_logs` | 信誉分变动日志 | `user_titles` | 用户-称号关联 |
| `books` | 图书信息 | `donations` | 捐书申请 |
| `borrow_records` | 借阅记录 | `image_reviews` | 图片审核 |
| `comments` | 评论 | `user_settings` | 用户个性化设置 |
| `quiz_questions` | 学习中心题库 | `notifications` | 站内通知 |
| `quiz_attempts` | 用户答题记录 | `system_config` | 系统全局配置 |

---

## 角色权限体系

| 角色 | role | 可访问 |
|------|------|--------|
| 读者 | 1 | 客户端（搜索/借书/还书/评论/答题/设置） |
| 图书管理员 | 2 | 管理端（仪表盘/书籍管理/还书审核/捐书审核/图片审核/评论管理） |
| 超级管理员 | 3 | 管理端全部 + 用户管理 + 信誉分调整 + 系统配置 |

---

## 快速开始

### 1. 克隆仓库

```bash
git clone https://gitee.com/sanchaomingfang/clean-reading-os.git
cd clean-reading-os
```

### 2. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate      # Linux/Mac
venv\Scripts\activate         # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`，根据需要修改：

```env
SECRET_KEY=your-random-secret-key
JWT_SECRET_KEY=your-jwt-secret
DATABASE_URL=sqlite:///library_system.db    # 开发用 SQLite
# 生产环境切换为：
# DATABASE_URL=mysql+pymysql://user:pass@127.0.0.1:3306/library_system
REDIS_ENABLED=false                         # 开发环境关闭 Redis
DEEPSEEK_API_KEY=sk-your-key                # AI 对话（可选）
```

### 5. 数据库迁移

```bash
flask db upgrade
```

### 6. 插入种子数据

```bash
flask seed
```

### 7. 启动服务

```bash
flask run --port 5000
# 或
python run.py
```

### 8. 访问系统

| 入口 | 地址 |
|------|------|
| 客户端首页 | http://127.0.0.1:5000/client/ |
| 管理端 | http://127.0.0.1:5000/admin/ |
| 借书机端 | http://127.0.0.1:5000/kiosk/ |
| 健康检查 | http://127.0.0.1:5000/api/health |

### 种子测试账号

| 角色 | 用户名 | 密码 | 权限 |
|------|--------|------|------|
| 超级管理员 | `admin` | `admin123` | role=3，全部权限 |
| 图书管理员 | `librarian` | `lib123` | role=2，书籍/还书管理 |
| 读者 | `reader` | `reader123` | role=1，普通用户 |

### Docker 一键部署

```bash
# 构建并启动容器
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

容器启动后，服务访问地址：http://localhost:5000

---

## API 端点概览

### 认证认证

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| `POST` | `/api/auth/register` | 用户注册 | 否 |
| `POST` | `/api/auth/login` | 用户登录 | 否 |
| `POST` | `/api/auth/logout` | 退出登录 | 是 |
| `GET` | `/api/auth/me` | 当前用户信息 | 是 |

### 图书 & 借阅

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| `GET` | `/api/books` | 图书搜索 | 公开 |
| `GET` | `/api/books/popular` | 热门推荐（按借阅次数） | 公开 |
| `GET` | `/api/books/<id>` | 图书详情 | 公开 |
| `GET` | `/api/books/isbn-lookup` | ISBN 自动填充（OpenLibrary） | 登录 |
| `POST` | `/api/borrow/request` | 借书 | 登录 |
| `GET` | `/api/borrow/status` | 查询某书借阅状态 | 登录 |
| `POST` | `/api/return/submit` | 提交归还（上传照片） | 登录 |
| `POST` | `/api/return/confirm` | 管理员确认还书 | 管理 |
| `GET` | `/api/return/pending` | 待确认归还列表 | 管理 |
| `GET` | `/api/return/my` | 我的借阅记录 | 登录 |

### 评论 & 学习 & AI

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| `GET/POST` | `/api/comments` | 评论列表/发表 | 登录 |
| `DELETE` | `/api/comments/<id>` | 删除评论 | 登录(本人) |
| `GET` | `/api/learn/questions` | 获取答题 | 登录 |
| `POST` | `/api/learn/submit` | 提交答题 | 登录 |
| `POST` | `/api/ai/chat` | AI 对话 | 登录 |

### 设置 & 通知

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| `GET/POST` | `/api/user/settings` | 个性化设置 | 登录 |
| `GET` | `/api/notifications` | 通知列表 | 登录 |
| `POST` | `/api/notifications/read` | 标记已读 | 登录 |

### 管理端

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| `GET` | `/api/admin/stats` | 仪表盘统计 | role 2/3 |
| `GET/POST` | `/api/admin/books` | 书籍列表/新增 | role 2/3 |
| `PUT/DELETE` | `/api/admin/books/<id>` | 编辑/删除 | role 2/3 |
| `GET` | `/api/admin/returns` | 还书记录 | role 2/3 |
| `GET` | `/api/admin/donations` | 捐书列表 | role 2/3 |
| `POST` | `/api/admin/donations/review` | 审核捐书 | role 2/3 |
| `GET` | `/api/admin/images` | 图片审核列表 | role 2/3 |
| `POST` | `/api/admin/images/review` | 审核图片 | role 2/3 |
| `GET` | `/api/admin/comments` | 评论管理 | role 2/3 |
| `DELETE` | `/api/admin/comments/<id>` | 删除评论 | role 2/3 |
| `GET` | `/api/admin/users` | 用户列表 | **role=3 only** |
| `POST` | `/api/admin/users/credit` | 信誉分调整 | **role=3 only** |

### 系统

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| `GET` | `/api/system/config` | 获取站点配置 | 公开 |
| `PUT` | `/api/system/config` | 更新站点名称 | **role=3 only** |
| `GET` | `/api/health` | 健康检查 | 公开 |

### 统一响应格式

```json
{
    "code": 200,
    "message": "success",
    "data": { ... }
}
```

### 错误码

| code | 含义 |
|------|------|
| 200  | 成功 |
| 400  | 请求参数错误 |
| 401  | 未登录或 Token 过期/失效 |
| 403  | 权限不足 |
| 404  | 资源不存在 |
| 429  | 请求过于频繁 |
| 500  | 服务器内部错误 |
| 1001 | 信誉分不足 |
| 1002 | 借阅数量已达上限 |
| 1003 | 图书不可借 |
| 1004 | 已借过该书 |

---

## 开发阶段

| 阶段 | 目标 | 状态 |
|------|------|------|
| Phase 1 | 骨架搭建：数据库 + 认证 + 客户端壳子 + 缓存层 | ✅ 完成 |
| Phase 2 | 核心借阅闭环：搜索/借书/还书/定时扣分/借书机 | ✅ 完成 |
| Phase 3 | 用户生态：评论/学习中心/AI/个性化/看板娘 | ✅ 完成 |
| Phase 4 | 管理后台：权限分离/书籍CRUD/还书审核/用户管理/系统配置/ISBN自动填充 | ✅ 完成 |

---

## 许可证

MIT License
