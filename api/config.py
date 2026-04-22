"""
儿童表现记录系统 - 应用配置
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置项"""
    
    # 应用基础配置
    APP_NAME: str = "儿童表现记录系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # 数据库配置
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@192.168.9.2:5432/child_reward"
    DATABASE_SYNC_URL: str = "postgresql+psycopg2://postgres:postgres@192.168.9.2:5432/child_reward"
    
    # JWT 认证配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 天
    
    # 微信小程序配置
    WECHAT_APP_ID: Optional[str] = None
    WECHAT_APP_SECRET: Optional[str] = None
    
    # CORS 配置
    CORS_ORIGINS: list[str] = ["*"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
