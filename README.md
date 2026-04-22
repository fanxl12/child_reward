# 儿童表现记录系统 (童星记录)

一个面向家长的儿童日常表现管理系统，通过微信小程序和后端API实现儿童表现记录、奖励币管理和奖励商城功能。

## 📱 项目概述

"童星记录"是一个帮助家长记录和管理儿童日常表现的系统。家长可以通过微信小程序记录孩子的日常表现，给予奖励或惩罚，并通过奖励币系统激励孩子养成良好习惯。

## ✨ 核心功能

### 用户管理
- 用户注册和登录（支持传统账号密码和微信小程序一键登录）
- 个人信息管理
- 密码修改

### 儿童管理
- 添加、编辑、删除儿童信息
- 管理多个孩子的档案

### 表现记录
- 每日表现评价（好/差）
- 详细评语记录
- 奖惩明细管理

### 奖励币系统
- 奖励/扣除奖励币
- 查看余额和交易流水
- 自动计算每日币数变动

### 奖励商城
- 自定义奖励选项
- 奖励币兑换
- 兑换记录管理

## 🏗️ 技术架构

### 后端技术栈
- **框架**: FastAPI 0.115.6
- **数据库**: PostgreSQL 15+ (asyncpg + SQLAlchemy)
- **认证**: JWT Token (python-jose)
- **依赖管理**: requirements.txt
- **API文档**: Swagger UI / ReDoc

### 前端技术栈
- **平台**: 微信小程序
- **语言**: JavaScript
- **UI框架**: 微信原生组件
- **状态管理**: 本地存储

### 数据库设计
- 用户表 (users)
- 儿童信息表 (children)
- 每日表现记录表 (performance_records)
- 奖惩明细记录表 (reward_records)
- 奖励商城商品表 (reward_items)
- 奖励币交易流水表 (coin_transactions)
- 兑换记录表 (redemption_records)

## 📁 项目结构

```
child_reward/
├── api/                    # FastAPI 后端
│   ├── endpoints/          # API 路由
│   ├── models/             # 数据库模型
│   ├── schemas/            # 数据验证模式
│   ├── services/           # 业务逻辑
│   ├── utils/              # 工具函数
│   ├── config.py           # 配置文件
│   ├── database.py         # 数据库连接
│   ├── main.py             # 应用入口
│   └── requirements.txt    # 后端依赖
├── miniprogram/            # 微信小程序前端
│   ├── components/         # 自定义组件
│   ├── pages/              # 页面文件
│   ├── utils/              # 工具函数
│   ├── app.js              # 小程序入口
│   ├── app.json            # 小程序配置
│   └── app.wxss            # 全局样式
├── database/               # 数据库相关文件
│   └── schema.sql          # 数据库结构定义
├── docs/                   # 文档
│   └── API.md              # API 接口文档
├── prototype/              # 原型设计 (TypeScript/React)
├── .env.example            # 环境变量示例
└── README.md               # 项目说明文档
```

## 🚀 快速开始

### 环境要求
- Python 3.10+
- PostgreSQL 15+
- 微信开发者工具

### 后端部署

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd child_reward
   ```

2. **创建虚拟环境**
   ```bash
   python -m venv api/.venv
   # Windows
   api\.venv\Scripts\activate
   # Linux/Mac
   source api/.venv/bin/activate
   ```

3. **安装依赖**
   ```bash
   pip install -r api/requirements.txt
   ```

4. **配置环境变量**
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，配置数据库和微信相关参数
   ```

5. **初始化数据库**
   ```bash
   # 使用 schema.sql 创建表结构
   psql -U your_username -d child_reward -f database/schema.sql
   ```

6. **启动服务**
   ```bash
   cd api
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

7. **访问API文档**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### 小程序部署

1. **导入项目**
   - 打开微信开发者工具
   - 导入 `miniprogram` 目录

2. **配置AppID**
   - 在 `project.config.json` 中配置您的小程序AppID

3. **配置API地址**
   - 修改 `miniprogram/utils/api.js` 中的后端API地址

4. **编译运行**
   - 点击编译按钮运行小程序

## 📖 API 文档

详细的API接口文档请参考 [docs/API.md](docs/API.md) 或访问运行中的服务：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🔧 环境变量配置

| 变量名 | 描述 | 默认值 |
|--------|------|--------|
| DEBUG | 调试模式 | true |
| DATABASE_URL | 异步数据库连接URL | postgresql+asyncpg://... |
| DATABASE_SYNC_URL | 同步数据库连接URL | postgresql+psycopg2://... |
| SECRET_KEY | JWT密钥 | your-very-secret-key... |
| WECHAT_APP_ID | 微信小程序AppID | wx1234567890abcdef |
| WECHAT_APP_SECRET | 微信小程序AppSecret | your-wechat-app-secret |

## 🧪 测试

### 后端测试
```bash
pytest
```

### 小程序测试
使用微信开发者工具进行模拟测试，详细测试指南请参考 [miniprogram/TEST_GUIDE.md](miniprogram/TEST_GUIDE.md)

## 📝 数据库设计

完整的数据库结构定义请参考 [database/schema.sql](database/schema.sql)

主要表结构：
- 用户表：存储家长账户信息
- 儿童表：存储儿童基本信息和奖励币余额
- 表现记录表：存储每日表现评价
- 奖惩明细表：存储具体的奖惩事件
- 奖励商品表：存储可兑换的奖励项
- 交易流水表：记录奖励币变动历史
- 兑换记录表：存储奖励兑换申请和状态

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进这个项目。

## 📄 许可证

[待添加许可证信息]

## 📞 联系方式

[待添加联系方式]