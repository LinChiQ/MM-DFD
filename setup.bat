@echo off
echo 正在安装多模态深度学习社交媒体虚假新闻检测系统 (MM-DFD)...

REM 检查Python是否安装
python --version 2>NUL
if %ERRORLEVEL% NEQ 0 (
    echo 错误: Python未安装！请安装Python 3.8+后重试。
    exit /b 1
)

REM 检查pip是否可用
python -m pip --version 2>NUL
if %ERRORLEVEL% NEQ 0 (
    echo 错误: pip未安装！请确保pip已正确安装。
    exit /b 1
)

echo 创建虚拟环境...
python -m venv venv
call venv\Scripts\activate.bat

echo 安装Python依赖...
pip install -r requirements.txt

REM 检查Node.js是否安装
node --version 2>NUL
if %ERRORLEVEL% NEQ 0 (
    echo 警告: Node.js未安装！前端部分需要Node.js 14+。
    echo 您可以从 https://nodejs.org/ 下载并安装。
) else (
    echo 安装前端依赖...
    cd frontend
    if exist package.json (
        echo 正在使用npm安装依赖，这可能需要几分钟...
        call npm install --no-optional
    ) else (
        echo 警告: 前端package.json不存在，跳过前端依赖安装。
    )
    cd ..
)

REM 检查MySQL是否可用
mysql --version 2>NUL
if %ERRORLEVEL% NEQ 0 (
    echo 警告: MySQL未安装或不在PATH中！系统需要MySQL 8.0+。
    echo 您可以从 https://dev.mysql.com/downloads/ 下载并安装。
) else (
    echo 检测到MySQL...
)

REM 创建基本目录结构
echo 创建项目结构...
if not exist models\preprocessing mkdir models\preprocessing
if not exist models\text_model mkdir models\text_model
if not exist models\image_model mkdir models\image_model
if not exist models\fusion_model mkdir models\fusion_model
if not exist data\raw mkdir data\raw
if not exist data\processed mkdir data\processed
if not exist scripts mkdir scripts
if not exist docs mkdir docs

REM 初始化Django项目(如果需要)
if not exist backend\manage.py (
    echo 初始化Django项目...
    cd backend
    django-admin startproject mmdfd .
    python manage.py startapp api
    python manage.py startapp users
    python manage.py startapp detection
    cd ..
)

echo =================================================
echo 安装完成！请参考以下步骤运行系统：
echo 1. 启动后端服务: cd backend && python manage.py runserver
echo 2. 启动前端服务: cd frontend && npm run serve
echo 3. 访问系统: http://localhost:8080
echo =================================================
