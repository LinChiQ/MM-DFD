# 多模态深度学习社交媒体虚假新闻检测系统 (MM-DFD)

## 项目概述
本项目旨在开发一个基于多模态深度学习的社交媒体虚假新闻检测系统，通过分析新闻文本与图像内容，自动识别虚假新闻信息。系统整合了最新的多模态深度学习技术，结合文本与图像特征进行综合分析，提供高精度的虚假新闻检测服务。

## 功能特点
- 多模态数据分析：同时处理文本与图像数据，提高检测准确性
- 用户友好界面：直观的Web交互平台，便于用户上传和管理检测内容
- 历史记录管理：用户可查询和管理历史检测记录
- 数据可视化：直观展示检测结果与统计分析
- 高效API接口：提供便捷的编程接口，支持第三方系统集成

## 技术栈
- **前端**：Vue.js, Element UI, Echarts
- **后端**：Django REST Framework, Python
- **数据库**：MySQL
- **深度学习**：Transformer, CNN, 多模态融合模型
- **模型选项**：Janus, CLIP, 或调用第三方多模态API
- **部署**：Docker (可选)

## 项目结构
```
MM-DFD/
├── frontend/                # 前端Vue.js项目
│   ├── public/              # 静态资源
│   ├── src/                 # 源代码
│   │   ├── assets/          # 资源文件
│   │   ├── components/      # 组件
│   │   ├── views/           # 页面
│   │   ├── router/          # 路由
│   │   ├── store/           # 状态管理
│   │   └── api/             # API调用
│   ├── package.json         # 依赖配置
│   └── README.md            # 前端说明
├── backend/                 # Django后端项目
│   ├── mmdfd/               # 主应用
│   │   ├── settings.py      # 项目设置
│   │   ├── urls.py          # URL配置
│   │   └── wsgi.py          # WSGI配置
│   ├── api/                 # API应用
│   ├── users/               # 用户管理应用
│   ├── detection/           # 检测核心应用
│   ├── manage.py            # Django管理脚本
│   └── README.md            # 后端说明
├── models/                  # 模型文件夹
│   ├── preprocessing/       # 数据预处理模块
│   ├── text_model/          # 文本分析模型
│   ├── image_model/         # 图像分析模型
│   ├── fusion_model/        # 模态融合模型
│   └── README.md            # 模型说明
├── data/                    # 数据文件夹
│   ├── raw/                 # 原始数据
│   ├── processed/           # 处理后数据
│   └── README.md            # 数据说明
├── scripts/                 # 实用脚本
│   ├── setup_db.py          # 数据库设置脚本
│   ├── data_collection.py   # 数据收集脚本
│   └── model_evaluation.py  # 模型评估脚本
├── docs/                    # 文档
│   ├── api_docs.md          # API文档
│   ├── model_docs.md        # 模型文档
│   └── user_guide.md        # 用户指南
├── setup.sh                 # Linux安装脚本
├── setup.bat                # Windows安装脚本
├── requirements.txt         # Python依赖
├── docker-compose.yml       # Docker配置
└── README.md                # 项目主README
```

## 安装与部署
### 系统要求
- Python 3.8+
- Node.js 14+
- MySQL 8.0+

### Windows安装
```bash
# 执行安装脚本
setup.bat
```

### Linux安装
```bash
# 执行安装脚本
bash setup.sh
```

## 数据集构建
本项目使用以下公开数据集：
- Twitter MediaEval数据集
- Weibo多模态虚假新闻数据集
- FakeNewsNet数据集

## 许可证
MIT

## 联系方式
项目维护者邮箱：your-email@example.com
