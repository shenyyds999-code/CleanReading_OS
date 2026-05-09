# 校园图书馆借阅系统 · Clean Reading

> 基于 Flask + MySQL 的三端分离线上借阅管理平台

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.1.0-orange.svg)](CHANGELOG.md)

---

## 项目简介

本项目为学校图书馆构建一套完整的线上借阅管理系统，核心特点：

- **三端分离** — 客户端（H5 全功能）、管理端（独立后台）、借书机端（极简触屏），共享同一后端 API
- **信誉分体系** — 用户初始 5 分，超期扣分、捐书加分，不同分数段对应不同借阅权限
- **学习激励** — 答题闯关系统，通过阅读检验获得称号
- **AI 助手** — 接入 DeepSeek API，以琪露诺人设提供书籍问答
- **Live2D 看板娘** — 信誉分 > 0 展示，0 分隐藏
- **Redis 缓存层** — 支持 Redis（生产）和内存缓存（开发降级），内置 API 限流与 JWT 黑名单

---

## 技术栈

| 层次     | 技术选型                                    |
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
| 安全     | Werkzeug 密码哈希 / Bleach XSS 过滤 / ORM 防注入 |

---

## 系统架构

```
┌──────────┐  ┌──────────┐  ┌──────────┐
│  客户端    │  │  管理端    │  │  借书机端   │
│  :80      │  │  :5001   │  │  :5002   │
└─────┬────┘  └─────┬────┘  └─────┬────┘
      └──────────────┼──────────────┘
                     │ Bearer JWT / X-Client-Type
          ┌──────────▼──────────┐
          │   Flask API :5000    │
          │  ┌────────────────┐ │
          │  │  限流中间件     │ │
          │  ├────────────────┤ │
          │  │  缓存层         │ │
          │  │  Redis / 内存   │ │
          │  ├────────────────┤ │
          │  │  auth blueprint │ │
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
│   ├── __init__.py                 # Flask 工厂 + /api/health + seed 命令
│   ├── api/
│   │   ├── __init__.py
│   │   └── auth.py                 # 认证蓝图 (register/login/logout/me)
│   ├── models/
│   │   ├── __init__.py
│   │   └── models.py               # 13 张核心表 SQLAlchemy 模型
│   ├── services/
│   │   ├── __init__.py
│   │   └── auth_service.py         # 认证业务逻辑
│   └── utils/
│       ├── __init__.py
│       ├── cache.py                # 缓存层 (Redis / 内存降级 / 装饰器)
│       ├── jwt_helper.py           # JWT 生成/验证/黑名单/装饰器
│       ├── rate_limiter.py         # API 频率限制中间件
│       ├── response.py             # 统一响应格式
│       └── security.py             # XSS 过滤 / 敏感词检测
│
├── client/                         # 客户端前端
│   ├── login.html                  # 登录页
│   ├── register.html               # 注册页
│   ├── index.html                  # 首页（信誉分显示）
│   └── js/
│       └── app.js                  # apiGet/apiPost / Token 管理
│
└── migrations/                     # Alembic 数据库迁移
```

---

## 数据库核心表 (13 张)

| 表名 | 说明 | 表名 | 说明 |
|------|------|------|------|
| `users` | 用户表 | `titles` | 称号表 |
| `credit_logs` | 信誉分变动日志 | `user_titles` | 用户-称号关联 |
| `books` | 图书信息 | `donations` | 捐书申请 |
| `borrow_records` | 借阅记录 | `image_reviews` | 图片审核 |
| `comments` | 评论 | `user_settings` | 用户个性化设置 |
| `quiz_questions` | 学习中心题库 | `notifications` | 站内通知 |
| `quiz_attempts` | 用户答题记录 | | |

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
| 客户端首页 | http://127.0.0.1:5000/client/index.html |
| 登录页 | http://127.0.0.1:5000/client/login.html |
| 健康检查 | http://127.0.0.1:5000/api/health |

### 种子测试账号

| 角色 | 用户名 | 密码 | 权限 |
|------|--------|------|------|
| 开发者 | `admin` | `admin123` | role=3，全部权限 |
| 图书管理员 | `librarian` | `lib123` | role=2，管理后台 |
| 读者 | `reader` | `reader123` | role=1，普通用户 |

---

## API 端点 (Phase 1)

| 方法 | 路径 | 说明 | 认证 | 限流 |
|------|------|------|------|------|
| `POST` | `/api/auth/register` | 用户注册 | 否 | 10/min |
| `POST` | `/api/auth/login` | 用户登录 | 否 | 10/min |
| `POST` | `/api/auth/logout` | 退出登录（JWT 黑名单） | 是 | 否 |
| `GET` | `/api/auth/me` | 获取当前用户信息 | 是 | 否 |
| `GET` | `/api/health` | 健康检查（含缓存状态） | 否 | 否 |

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

---

## 缓存层说明

系统内置两级缓存架构：

| 层级 | 触发条件 | 实现 |
|------|----------|------|
| **Redis 缓存** | `REDIS_ENABLED=true` 且 Redis 可连接 | `redis-py` 连接池 |
| **内存降级** | Redis 不可用或未启用 | `SimpleCache(RLock)` 线程安全 |

缓存功能：
- **用户信息缓存**（TTL 10 分钟）— 登录时预热，登出时清除
- **JWT 黑名单** — 登出后令牌写入缓存，验证时检查
- **装饰器支持** — `@cache_result` / `@cache_invalidate` 供后续模块使用

---

## 开发阶段

| 阶段 | 目标 | 状态 |
|------|------|------|
| Phase 1 | 骨架搭建：数据库 + 认证 + 客户端壳子 + 缓存层 | ✅ 完成 |
| Phase 2 | 核心借阅闭环：搜索/借书/还书/定时扣分/借书机 | 🔜 待开发 |
| Phase 3 | 用户生态：评论/学习中心/AI/个性化/看板娘 | 待开发 |
| Phase 4 | 管理后台 + 全流程贯通 | 待开发 |

---

## 许可证

MIT License
