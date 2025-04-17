#!/bin/bash

echo "正在安装多模态深度学习社交媒体虚假新闻检测系统 (MM-DFD)..."

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: Python未安装！请安装Python 3.8+后重试。"
    exit 1
fi

# 检查pip是否可用
if ! command -v pip3 &> /dev/null; then
    echo "错误: pip未安装！请确保pip已正确安装。"
    exit 1
fi

echo "创建虚拟环境..."
python3 -m venv venv
source venv/bin/activate

echo "安装Python依赖..."
pip install -r requirements.txt

# 检查Node.js是否安装
if ! command -v node &> /dev/null; then
    echo "警告: Node.js未安装！前端部分需要Node.js 14+。"
    echo "您可以使用以下命令安装Node.js："
    echo "  curl -fsSL https://deb.nodesource.com/setup_16.x | sudo -E bash -"
    echo "  sudo apt-get install -y nodejs"
else
    echo "安装前端依赖..."
    cd frontend
    if [ -f package.json ]; then
        echo "正在使用npm安装依赖，这可能需要几分钟..."
        npm install --no-optional
    else
        echo "警告: 前端package.json不存在，跳过前端依赖安装。"
    fi
    cd ..
fi

# 检查MySQL是否可用
if ! command -v mysql &> /dev/null; then
    echo "警告: MySQL未安装！系统需要MySQL 8.0+。"
    echo "您可以使用以下命令安装MySQL："
    echo "  sudo apt-get install mysql-server"
    echo "  sudo mysql_secure_installation"
else
    echo "检测到MySQL..."
fi

# 创建基本目录结构
echo "创建项目结构..."
mkdir -p models/preprocessing models/text_model models/image_model models/fusion_model
mkdir -p data/raw data/processed
mkdir -p scripts docs

# 初始化Django项目(如果需要)
if [ ! -f backend/manage.py ]; then
    echo "初始化Django项目..."
    cd backend
    django-admin startproject mmdfd .
    python manage.py startapp api
    python manage.py startapp users
    python manage.py startapp detection
    cd ..
fi

echo "================================================="
echo "安装完成！请参考以下步骤运行系统："
echo "1. 启动后端服务: cd backend && python manage.py runserver"
echo "2. 启动前端服务: cd frontend && npm run serve"
echo "3. 访问系统: http://localhost:8080"
echo "================================================="
