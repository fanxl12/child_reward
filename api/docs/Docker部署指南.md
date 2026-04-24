# 儿童表现记录系统 - API 服务 Docker 部署指南

## 一、环境要求

| 依赖项 | 最低版本 | 说明 |
|--------|---------|------|
| Docker | 20.10+  | 容器运行时 |
| Docker Compose | v2.0+ | 服务编排（Docker Desktop 自带） |

验证安装：

```bash
docker --version
docker compose version
```

## 二、项目目录结构

```
child_reward/
├── api/                          # API 项目根目录
│   ├── docker/
│   │   ├── Dockerfile            # API 服务镜像构建文件
│   │   └── docker-compose.yml    # 服务编排配置
│   ├── endpoints/                # API 接口模块
│   ├── models/                   # 数据模型
│   ├── schemas/                  # 请求/响应结构定义
│   ├── services/                 # 业务服务
│   ├── utils/                    # 工具模块
│   ├── .env                      # 环境变量配置（需手动创建）
│   ├── config.py
│   ├── database.py
│   ├── main.py
│   └── requirements.txt
├── database/
│   └── schema.sql                # 数据库初始化脚本（首次部署自动执行）
└── .env.example                  # 环境变量配置示例
```

## 三、部署步骤

### 3.1 准备环境变量配置

进入 `api` 目录，复制示例文件并修改配置：

```bash
cd child_reward/api
cp ../.env.example .env
```

编辑 `.env` 文件，**必须修改以下配置项**：

```ini
# 应用配置（生产环境建议设为 false）
DEBUG=false

# JWT 密钥（生产环境务必替换为强随机字符串）
SECRET_KEY=请替换为一个安全的随机字符串

# 微信小程序配置（替换为实际的 AppID 和 AppSecret）
WECHAT_APP_ID=你的微信小程序AppID
WECHAT_APP_SECRET=你的微信小程序AppSecret
```

> **注意**：`.env` 中的 `DATABASE_URL` 和 `DATABASE_SYNC_URL` 不需要修改，`docker-compose.yml` 中已通过 `environment` 覆盖了数据库连接地址，自动指向容器内的数据库服务。

### 3.2 启动服务

进入 docker 目录并执行构建启动：

```bash
cd child_reward/api/docker
docker compose up --build -d
```

首次启动会：
1. 拉取 `postgres:16-alpine` 镜像
2. 构建 API 服务镜像（安装 Python 依赖，约 2-5 分钟）
3. 启动 PostgreSQL 数据库并**自动执行 `schema.sql` 初始化表结构**
4. 数据库健康检查通过后启动 API 服务

### 3.3 验证部署

```bash
# 查看容器运行状态
docker compose ps

# 期望输出：
# NAME               IMAGE                STATUS                    PORTS
# child_reward_db    postgres:16-alpine   Up (healthy)              0.0.0.0:15432->5432/tcp
# child_reward_api   docker-api           Up                        0.0.0.0:8000->8000/tcp
```

```bash
# 健康检查
curl http://localhost:8000/health
# 期望返回：{"status":"healthy"}

# 查看 API 根路径
curl http://localhost:8000/
# 期望返回：{"name":"儿童表现记录系统","version":"1.0.0","status":"running","docs":"/docs"}
```

访问 API 文档：浏览器打开 `http://服务器IP:8000/docs`

## 四、服务端口说明

| 服务 | 容器内端口 | 宿主机映射端口 | 说明 |
|------|-----------|---------------|------|
| API  | 8000      | 8000          | FastAPI 服务 |
| DB   | 5432      | 15432         | PostgreSQL 数据库 |

> 宿主机使用 `15432` 映射避免与服务器上已有的 PostgreSQL 5432 端口冲突。如需修改，编辑 `docker-compose.yml` 中 `db.ports` 配置。

## 五、常用运维命令

### 查看服务状态

```bash
cd child_reward/api/docker
docker compose ps
```

### 查看日志

```bash
# 查看所有服务日志
docker compose logs

# 实时跟踪 API 日志
docker compose logs -f api

# 实时跟踪数据库日志
docker compose logs -f db

# 查看最近 100 行日志
docker compose logs --tail 100
```

### 重启服务

```bash
# 重启所有服务
docker compose restart

# 仅重启 API 服务（不影响数据库）
docker compose restart api
```

### 停止服务

```bash
# 停止服务（保留数据）
docker compose down

# 停止服务并删除数据卷（会清空数据库，谨慎操作！）
docker compose down -v
```

### 更新部署

代码更新后重新构建并启动：

```bash
cd child_reward/api/docker
docker compose up --build -d
```

> 此操作不会影响数据库数据，仅重新构建 API 镜像。

## 六、数据库管理

### 外部连接数据库

```
主机：服务器IP
端口：15432
用户名：postgres
密码：postgres
数据库名：child_reward
```

使用 psql 命令行连接：

```bash
psql -h 服务器IP -p 15432 -U postgres -d child_reward
```

### 数据库初始化机制

- 首次启动时，PostgreSQL 容器会自动执行 `database/schema.sql` 脚本，创建所有表、索引、触发器和注释
- **此脚本仅在数据卷为空（全新数据库）时执行一次**
- 后续启动不会重复执行初始化脚本

### 数据库备份

```bash
# 备份数据库
docker exec child_reward_db pg_dump -U postgres child_reward > backup_$(date +%Y%m%d).sql

# 恢复数据库
cat backup_20260424.sql | docker exec -i child_reward_db psql -U postgres -d child_reward
```

## 七、故障排查

### API 容器无法启动

```bash
# 查看 API 容器日志
docker compose logs api

# 常见原因：
# 1. .env 文件缺失 → 确认 api/.env 文件存在
# 2. 数据库未就绪 → 检查 db 容器健康状态
```

### 数据库容器异常

```bash
# 查看数据库日志
docker compose logs db

# 检查数据库健康状态
docker exec child_reward_db pg_isready -U postgres -d child_reward
```

### 端口冲突

```bash
# 检查端口占用
netstat -tlnp | grep -E '8000|15432'

# 如有冲突，修改 docker-compose.yml 中对应的宿主机端口映射
```

### 完全重置（清除所有数据重新开始）

```bash
cd child_reward/api/docker
docker compose down -v
docker compose up --build -d
```

> **警告**：`-v` 参数会删除数据卷，数据库中的所有数据将被清除！

## 八、生产环境建议

1. **修改数据库密码**：编辑 `docker-compose.yml` 中 `POSTGRES_PASSWORD` 以及 `DATABASE_URL` 中的密码
2. **关闭 DEBUG 模式**：`.env` 中设置 `DEBUG=false`
3. **使用强 JWT 密钥**：`.env` 中 `SECRET_KEY` 设置为 32 位以上随机字符串
4. **配置防火墙**：仅开放 8000 端口对外，15432 端口建议仅内网访问
5. **定期备份数据库**：建议使用 crontab 定时执行备份命令
