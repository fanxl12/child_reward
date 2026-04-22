"""
Pydantic Schema - 奖励商城 & 交易流水 & 兑换记录
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================
# 奖励商品请求模型
# ============================================

class RewardItemCreateRequest(BaseModel):
    """创建奖励商品请求"""
    name: str = Field(..., min_length=1, max_length=100, description="奖励名称")
    description: Optional[str] = Field(None, description="奖励描述")
    coin_cost: int = Field(..., gt=0, description="所需奖励币")
    icon: str = Field(default="🎁", max_length=100, description="图标")
    sort_order: int = Field(default=0, description="排序权重")


class RewardItemUpdateRequest(BaseModel):
    """更新奖励商品请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="奖励名称")
    description: Optional[str] = Field(None, description="奖励描述")
    coin_cost: Optional[int] = Field(None, gt=0, description="所需奖励币")
    icon: Optional[str] = Field(None, max_length=100, description="图标")
    sort_order: Optional[int] = Field(None, description="排序权重")
    is_active: Optional[bool] = Field(None, description="是否启用")


# ============================================
# 奖励商品响应模型
# ============================================

class RewardItemResponse(BaseModel):
    """奖励商品响应"""
    id: UUID
    name: str
    description: Optional[str] = None
    coin_cost: int
    icon: str = "🎁"
    sort_order: int = 0
    is_active: bool = True
    created_at: datetime

    model_config = {"from_attributes": True}


class RewardItemListResponse(BaseModel):
    """奖励商品列表响应"""
    items: list[RewardItemResponse]
    total: int


# ============================================
# 兑换请求/响应模型
# ============================================

class RedeemRequest(BaseModel):
    """兑换奖励请求"""
    reward_item_id: UUID = Field(..., description="要兑换的奖励商品 ID")


class RedemptionResponse(BaseModel):
    """兑换记录响应"""
    id: UUID
    child_id: UUID
    reward_item_id: UUID
    reward_name: str
    coins_spent: int
    remaining_balance: int
    created_at: datetime

    model_config = {"from_attributes": True}


class RedemptionListResponse(BaseModel):
    """兑换记录列表响应"""
    records: list[RedemptionResponse]
    total: int


# ============================================
# 交易流水响应模型
# ============================================

class CoinTransactionResponse(BaseModel):
    """交易流水响应"""
    id: UUID
    type: str
    amount: int
    balance_after: int
    description: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CoinBalanceResponse(BaseModel):
    """奖励币余额响应"""
    child_id: UUID
    child_name: str
    balance: int
    transactions: list[CoinTransactionResponse] = []
    total_transactions: int = 0
