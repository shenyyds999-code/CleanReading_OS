#!/bin/bash
set -e

# 一键部署脚本 - Ubuntu 环境
# 使用方法: sudo bash deploy.sh

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置参数
PROJECT_NAME="ClearReading"
PROJECT_DIR="/opt/ClearReading"
GIT_REPO="https://github.com/your-repo/ClearReading.git"  # 请替换为实际仓库地址
APP_PORT=5000
DB_NAME="library_system"
DB_USER="library_user"
DB_PASS=$(openssl rand -hex 16)
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET=$(openssl rand -hex 32)

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}    ClearReading 一键部署脚本              ${NC}"
echo -e "${YELLOW}========================================${NC}"

# 检查是否以 root 用户运行
if [ "$(id -u)" != "0" ]; then
    echo -e "${RED}错误: 请使用 sudo 或 root 用户运行此脚本${NC}"
    exit 1
fi

# 1. 更新系统和安装依赖
echo -e "${GREEN}步骤 1/7: 更新系统并安装基础依赖${NC}"
apt-get update -y
apt-get upgrade -y
apt-get install -y \
    python3 python3-pip python3-dev \
    mysql-server mysql-client \
    redis-server \
    nginx \
    git \
    libmysqlclient-dev \
    build-essential

# 2. 创建项目目录
echo -e "${GREEN}步骤 2/7: 创建项目目录${NC}"
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# 3. 克隆项目代码
echo -e "${GREEN}步骤 3/7: 克隆项目代码${NC}"
if [ -d ".git" ]; then
    git pull origin main
else
    git clone $GIT_REPO .
fi

# 4. 配置数据库
echo -e "${GREEN}步骤 4/7: 配置 MySQL 数据库${NC}"
mysql -u root <<EOF
CREATE DATABASE IF NOT EXISTS $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASS';
GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';
FLUSH PRIVILEGES;
EOF

# 5. 创建虚拟环境并安装依赖
echo -e "${GREEN}步骤 5/7: 安装 Python 依赖${NC}"
pip3 install virtualenv
virtualenv venv
source venv/bin/activate
pip3 install -r requirements.txt

# 6. 配置环境变量
echo -e "${GREEN}步骤 6/7: 配置环境变量${NC}"
cat > .env <<EOF
SECRET_KEY=$SECRET_KEY
JWT_SECRET_KEY=$JWT_SECRET
DATABASE_URL=mysql+pymysql://$DB_USER:$DB_PASS@127.0.0.1:3306/$DB_NAME
JWT_EXPIRATION_HOURS=24
REDIS_URL=redis://127.0.0.1:6379/0
REDIS_ENABLED=true
REDIS_CONNECT_TIMEOUT=3
REDIS_SOCKET_TIMEOUT=2
CACHE_DEFAULT_TTL=300
CACHE_USER_TTL=600
CACHE_BOOK_LIST_TTL=120
RATE_LIMIT_ENABLED=true
RATE_LIMIT_GLOBAL=60/minute
RATE_LIMIT_AUTH=10/minute
DEEPSEEK_API_KEY=your-deepseek-api-key
DEEPSEEK_BASE_URL=https://api.deepseek.com
EOF

# 7. 数据库迁移
echo -e "${GREEN}步骤 7/7: 执行数据库迁移${NC}"
flask db init || true
flask db migrate -m "Initial migration"
flask db upgrade

# 配置 systemd 服务
echo -e "${GREEN}配置 systemd 服务${NC}"
cat > /etc/systemd/system/clearreading.service <<EOF
[Unit]
Description=ClearReading Flask Application
After=network.target mysql.service redis.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin"
ExecStart=$PROJECT_DIR/venv/bin/gunicorn --workers=4 --bind=127.0.0.1:$APP_PORT run:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 配置 Nginx 反向代理
echo -e "${GREEN}配置 Nginx 反向代理${NC}"
cat > /etc/nginx/sites-available/clearreading <<EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:$APP_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # 静态文件
    location /static/ {
        root $PROJECT_DIR;
        expires 30d;
    }

    # 客户端静态文件
    location /admin/ {
        root $PROJECT_DIR;
        try_files \$uri \$uri/ =404;
    }

    location /client/ {
        root $PROJECT_DIR;
        try_files \$uri \$uri/ =404;
    }

    location /kiosk/ {
        root $PROJECT_DIR;
        try_files \$uri \$uri/ =404;
    }
}
EOF

ln -sf /etc/nginx/sites-available/clearreading /etc/nginx/sites-enabled/

# 重启服务
systemctl daemon-reload
systemctl enable clearreading
systemctl start clearreading
systemctl restart nginx

# 启用 Redis
systemctl enable redis-server
systemctl start redis-server

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}           部署完成!                      ${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}部署信息:${NC}"
echo -e "  项目目录: ${GREEN}$PROJECT_DIR${NC}"
echo -e "  数据库名: ${GREEN}$DB_NAME${NC}"
echo -e "  数据库用户: ${GREEN}$DB_USER${NC}"
echo -e "  数据库密码: ${GREEN}$DB_PASS${NC}"
echo -e "  应用端口: ${GREEN}$APP_PORT${NC}"
echo -e "  SECRET_KEY: ${GREEN}$SECRET_KEY${NC}"
echo -e "  JWT_SECRET: ${GREEN}$JWT_SECRET${NC}"
echo ""
echo -e "${YELLOW}后续操作:${NC}"
echo -e "  1. 设置域名并配置 SSL (推荐使用 Let's Encrypt)"
echo -e "  2. 在 .env 文件中配置 DEEPSEEK_API_KEY"
echo -e "  3. 查看应用日志: journalctl -u clearreading"
echo -e "  4. 重启应用: systemctl restart clearreading"