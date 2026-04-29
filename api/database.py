"""
儿童表现记录系统 - 数据库连接
"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from api.config import settings

# 异步引擎
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)

# 异步 Session 工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """SQLAlchemy 声明式基类"""
    pass


async def get_db():
    """获取数据库会话（依赖注入）"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """初始化数据库表（开发环境使用）"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # 轻量迁移：为历史库补充密码初始化状态字段（仅首次补列时执行）
        column_check = await conn.execute(
            text(
                "SELECT 1 FROM information_schema.columns "
                "WHERE table_name = 'users' AND column_name = 'password_initialized'"
            )
        )
        if column_check.first() is None:
            await conn.execute(
                text(
                    "ALTER TABLE users "
                    "ADD COLUMN password_initialized BOOLEAN NOT NULL DEFAULT TRUE"
                )
            )
            await conn.execute(
                text(
                    "UPDATE users SET password_initialized = FALSE "
                    "WHERE wechat_openid IS NOT NULL"
                )
            )
