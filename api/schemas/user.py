"""
Pydantic Schema - 用户相关
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================
# 请求模型
# ============================================

class UserRegisterRequest(BaseModel):
    """用户注册请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=100, description="密码")
    phone: Optional[str] = Field(None, max_length=20, description="手机号码")
    nickname: Optional[str] = Field(None, max_length=50, description="昵称")


class UserLoginRequest(BaseModel):
    """用户登录请求"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class WechatLoginRequest(BaseModel):
    """微信小程序登录请求"""
    code: str = Field(..., description="微信登录临时凭证 code")


class UserUpdateRequest(BaseModel):
    """用户信息更新请求"""
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="用户名")
    nickname: Optional[str] = Field(None, max_length=50, description="昵称")
    avatar_url: Optional[str] = Field(None, max_length=500, description="头像地址")
    phone: Optional[str] = Field(None, max_length=20, description="手机号码")


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    old_password: str = Field(..., description="原密码")
    new_password: str = Field(..., min_length=6, max_length=100, description="新密码")


class SetPasswordRequest(BaseModel):
    """设置密码请求（微信用户首次设置）"""
    new_password: str = Field(..., min_length=6, max_length=100, description="新密码")


# ============================================
# 响应模型
# ============================================

class UserResponse(BaseModel):
    """用户信息响应"""
    id: UUID
    username: str
    phone: Optional[str] = None
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    has_password: bool = True
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """令牌响应"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class MessageResponse(BaseModel):
    """通用消息响应"""
    message: str
    success: bool = True
