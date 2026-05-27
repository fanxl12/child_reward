"""
Pydantic Schema - 家庭相关
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class FamilyCreateRequest(BaseModel):
    """创建家庭请求"""
    name: str = Field(..., min_length=1, max_length=50, description="家庭名称")


class FamilyJoinRequest(BaseModel):
    """通过家庭编号加入家庭请求"""
    code: str = Field(..., min_length=6, max_length=6, description="家庭编号")


class FamilySwitchRequest(BaseModel):
    """切换当前家庭请求"""
    family_id: UUID = Field(..., description="家庭 ID")


class FamilyResponse(BaseModel):
    """家庭信息响应"""
    id: UUID
    name: str
    code: str
    owner_user_id: UUID
    is_owner: bool = False
    role: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class FamilyListResponse(BaseModel):
    """家庭列表响应"""
    families: list[FamilyResponse]
    current_family_id: UUID | None = None
    total: int = 0
