"""
儿童表现记录系统 - FastAPI 主入口
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import settings
from api.database import init_db
from api.endpoints.user import router as auth_router, user_router
from api.endpoints.child import router as child_router
from api.endpoints.performance import router as performance_router
from api.endpoints.reward import reward_router, coin_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库表
    if settings.DEBUG:
        await init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## 儿童表现记录系统 API

面向家长的儿童日常表现管理系统，支持：

- **用户认证**：注册、登录、个人信息管理
- **儿童管理**：添加、编辑、删除儿童信息
- **表现记录**：每日表现评价、评语、奖惩明细
- **奖励币系统**：奖励/扣除奖励币，查看余额与流水
- **奖励商城**：自定义奖励选项，兑换奖励

### 认证方式

所有需要认证的接口使用 Bearer Token 方式，在请求头中添加：
```
Authorization: Bearer <access_token>
```
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(child_router)
app.include_router(performance_router)
app.include_router(reward_router)
app.include_router(coin_router)


@app.get("/", tags=["系统"])
async def root():
    """系统根路径 - 健康检查"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["系统"])
async def health_check():
    """健康检查接口"""
    return {"status": "healthy"}
