"""
Pydantic Schema - 儿童信息相关
"""
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================
# 请求模型
# ============================================

class ChildCreateRequest(BaseModel):
    """添加儿童请求"""
    name: str = Field(..., min_length=1, max_length=50, description="儿童姓名")
    gender: Optional[str] = Field(None, pattern="^(male|female|other)$", description="性别")
    birthday: Optional[date] = Field(None, description="出生日期")
    avatar_url: Optional[str] = Field(None, max_length=500, description="头像地址")


class ChildUpdateRequest(BaseModel):
    """更新儿童信息请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=50, description="儿童姓名")
    gender: Optional[str] = Field(None, pattern="^(male|female|other)$", description="性别")
    birthday: Optional[date] = Field(None, description="出生日期")
    avatar_url: Optional[str] = Field(None, max_length=500, description="头像地址")


# ============================================
# 响应模型
# ============================================

class ChildResponse(BaseModel):
    """儿童信息响应"""
    id: UUID
    name: str
    gender: Optional[str] = None
    birthday: Optional[date] = None
    avatar_url: Optional[str] = None
    coin_balance: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class ChildListResponse(BaseModel):
    """儿童列表响应"""
    children: list[ChildResponse]
    total: int
