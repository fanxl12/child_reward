"""
Pydantic Schema - 表现记录相关
"""
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================
# 奖惩明细模型
# ============================================

class RewardRecordItem(BaseModel):
    """奖惩明细项"""
    type: str = Field(..., pattern="^(reward|punishment)$", description="类型")
    description: str = Field(..., min_length=1, description="描述")
    coins: int = Field(..., gt=0, description="奖励币数量")


class RewardRecordResponse(BaseModel):
    """奖惩明细响应"""
    id: UUID
    type: str
    description: str
    coins: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================
# 表现记录请求模型
# ============================================

class PerformanceCreateRequest(BaseModel):
    """创建每日表现记录请求"""
    record_date: date = Field(..., description="记录日期")
    overall_rating: str = Field(..., pattern="^(good|bad)$", description="总体评价")
    comment: Optional[str] = Field(None, max_length=500, description="评语")
    reward_records: list[RewardRecordItem] = Field(default=[], description="奖惩明细列表")


class PerformanceUpdateRequest(BaseModel):
    """更新每日表现记录请求"""
    overall_rating: Optional[str] = Field(None, pattern="^(good|bad)$", description="总体评价")
    comment: Optional[str] = Field(None, max_length=500, description="评语")
    reward_records: Optional[list[RewardRecordItem]] = Field(None, description="奖惩明细列表")


# ============================================
# 表现记录响应模型
# ============================================

class PerformanceResponse(BaseModel):
    """表现记录详情响应"""
    id: UUID
    child_id: UUID
    record_date: date
    overall_rating: str
    comment: Optional[str] = None
    coins_earned: int = 0
    coins_deducted: int = 0
    reward_records: list[RewardRecordResponse] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class PerformanceSummary(BaseModel):
    """表现日历摘要（用于日历展示）"""
    record_date: date
    overall_rating: str
    coins_earned: int = 0
    coins_deducted: int = 0


class MonthlyPerformanceResponse(BaseModel):
    """月度表现日历响应"""
    year: int
    month: int
    child_id: UUID
    records: list[PerformanceSummary]
    good_days: int = 0
    bad_days: int = 0
    total_coins_earned: int = 0
    total_coins_deducted: int = 0
