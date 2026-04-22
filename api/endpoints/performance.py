"""
API 端点 - 表现记录管理
"""
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, and_, extract
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.database import get_db
from api.models.child import Child
from api.models.performance import PerformanceRecord, RewardRecord
from api.models.reward import CoinTransaction
from api.models.user import User
from api.schemas.performance import (
    PerformanceCreateRequest,
    PerformanceUpdateRequest,
    PerformanceResponse,
    PerformanceSummary,
    MonthlyPerformanceResponse,
    RewardRecordResponse,
)
from api.utils.deps import get_current_user

router = APIRouter(prefix="/api/children/{child_id}/performance", tags=["表现记录"])


async def _verify_child_ownership(
    child_id: UUID, user_id: UUID, db: AsyncSession
) -> Child:
    """验证儿童归属权"""
    result = await db.execute(
        select(Child).where(Child.id == child_id, Child.user_id == user_id)
    )
    child = result.scalar_one_or_none()
    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到该儿童信息",
        )
    return child


@router.get("/monthly", response_model=MonthlyPerformanceResponse)
async def get_monthly_performance(
    child_id: UUID,
    year: int = Query(..., ge=2020, le=2100, description="年份"),
    month: int = Query(..., ge=1, le=12, description="月份"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取指定月份的表现日历数据
    
    - **year**: 年份
    - **month**: 月份（1-12）
    
    返回该月每天的表现摘要，用于日历展示。
    """
    await _verify_child_ownership(child_id, current_user.id, db)
    
    result = await db.execute(
        select(PerformanceRecord)
        .where(
            PerformanceRecord.child_id == child_id,
            extract("year", PerformanceRecord.record_date) == year,
            extract("month", PerformanceRecord.record_date) == month,
        )
        .order_by(PerformanceRecord.record_date.asc())
    )
    records = result.scalars().all()
    
    summaries = []
    good_days = 0
    bad_days = 0
    total_earned = 0
    total_deducted = 0
    
    for record in records:
        summaries.append(PerformanceSummary(
            record_date=record.record_date,
            overall_rating=record.overall_rating,
            coins_earned=record.coins_earned,
            coins_deducted=record.coins_deducted,
        ))
        if record.overall_rating == "good":
            good_days += 1
        else:
            bad_days += 1
        total_earned += record.coins_earned
        total_deducted += record.coins_deducted
    
    return MonthlyPerformanceResponse(
        year=year,
        month=month,
        child_id=child_id,
        records=summaries,
        good_days=good_days,
        bad_days=bad_days,
        total_coins_earned=total_earned,
        total_coins_deducted=total_deducted,
    )


@router.get("/{record_date}", response_model=PerformanceResponse)
async def get_daily_performance(
    child_id: UUID,
    record_date: date,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取指定日期的表现详情
    
    - **record_date**: 日期，格式 YYYY-MM-DD
    
    返回当日总体评价、评语、奖惩明细。
    """
    await _verify_child_ownership(child_id, current_user.id, db)
    
    result = await db.execute(
        select(PerformanceRecord)
        .options(selectinload(PerformanceRecord.reward_records))
        .where(
            PerformanceRecord.child_id == child_id,
            PerformanceRecord.record_date == record_date,
        )
    )
    record = result.scalar_one_or_none()
    
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"未找到 {record_date} 的表现记录",
        )
    
    return PerformanceResponse(
        id=record.id,
        child_id=record.child_id,
        record_date=record.record_date,
        overall_rating=record.overall_rating,
        comment=record.comment,
        coins_earned=record.coins_earned,
        coins_deducted=record.coins_deducted,
        reward_records=[
            RewardRecordResponse.model_validate(rr) for rr in record.reward_records
        ],
        created_at=record.created_at,
    )


@router.post("", response_model=PerformanceResponse, status_code=status.HTTP_201_CREATED)
async def create_performance(
    child_id: UUID,
    request: PerformanceCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    创建每日表现记录
    
    - **record_date**: 记录日期
    - **overall_rating**: 总体评价 good/bad
    - **comment**: 评语（可选）
    - **reward_records**: 奖惩明细列表
    
    系统会自动计算奖励币并更新儿童余额。
    """
    child = await _verify_child_ownership(child_id, current_user.id, db)
    
    # 检查当日是否已有记录
    existing = await db.execute(
        select(PerformanceRecord).where(
            PerformanceRecord.child_id == child_id,
            PerformanceRecord.record_date == request.record_date,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{request.record_date} 的表现记录已存在，请使用更新接口",
        )
    
    # 计算奖惩币数
    coins_earned = sum(
        r.coins for r in request.reward_records if r.type == "reward"
    )
    coins_deducted = sum(
        r.coins for r in request.reward_records if r.type == "punishment"
    )
    
    # 创建表现记录
    performance = PerformanceRecord(
        child_id=child_id,
        record_date=request.record_date,
        overall_rating=request.overall_rating,
        comment=request.comment,
        coins_earned=coins_earned,
        coins_deducted=coins_deducted,
        created_by=current_user.id,
    )
    db.add(performance)
    await db.flush()
    
    # 创建奖惩明细
    for item in request.reward_records:
        reward_record = RewardRecord(
            performance_id=performance.id,
            type=item.type,
            description=item.description,
            coins=item.coins,
        )
        db.add(reward_record)
    
    # 更新儿童奖励币余额
    net_coins = coins_earned - coins_deducted
    new_balance = max(0, child.coin_balance + net_coins)
    
    # 记录奖励币交易
    if coins_earned > 0:
        earn_transaction = CoinTransaction(
            child_id=child_id,
            type="earn",
            amount=coins_earned,
            balance_after=child.coin_balance + coins_earned,
            description=f"{request.record_date} 表现奖励",
            related_performance_id=performance.id,
        )
        db.add(earn_transaction)
    
    if coins_deducted > 0:
        deduct_transaction = CoinTransaction(
            child_id=child_id,
            type="deduct",
            amount=-coins_deducted,
            balance_after=new_balance,
            description=f"{request.record_date} 表现惩罚",
            related_performance_id=performance.id,
        )
        db.add(deduct_transaction)
    
    child.coin_balance = new_balance
    await db.flush()
    
    # 重新加载带关联的记录
    result = await db.execute(
        select(PerformanceRecord)
        .options(selectinload(PerformanceRecord.reward_records))
        .where(PerformanceRecord.id == performance.id)
    )
    performance = result.scalar_one()
    
    return PerformanceResponse(
        id=performance.id,
        child_id=performance.child_id,
        record_date=performance.record_date,
        overall_rating=performance.overall_rating,
        comment=performance.comment,
        coins_earned=performance.coins_earned,
        coins_deducted=performance.coins_deducted,
        reward_records=[
            RewardRecordResponse.model_validate(rr) for rr in performance.reward_records
        ],
        created_at=performance.created_at,
    )


@router.put("/{record_date}", response_model=PerformanceResponse)
async def update_performance(
    child_id: UUID,
    record_date: date,
    request: PerformanceUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    更新指定日期的表现记录
    
    支持更新总体评价、评语和奖惩明细。
    更新奖惩明细时会重新计算奖励币变动。
    """
    child = await _verify_child_ownership(child_id, current_user.id, db)
    
    result = await db.execute(
        select(PerformanceRecord)
        .options(selectinload(PerformanceRecord.reward_records))
        .where(
            PerformanceRecord.child_id == child_id,
            PerformanceRecord.record_date == record_date,
        )
    )
    performance = result.scalar_one_or_none()
    
    if not performance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"未找到 {record_date} 的表现记录",
        )
    
    # 更新基本字段
    if request.overall_rating is not None:
        performance.overall_rating = request.overall_rating
    if request.comment is not None:
        performance.comment = request.comment
    
    # 如果提供了新的奖惩明细，重新计算
    if request.reward_records is not None:
        # 恢复旧的奖励币变动
        old_net = performance.coins_earned - performance.coins_deducted
        child.coin_balance = max(0, child.coin_balance - old_net)
        
        # 删除旧的奖惩明细
        for rr in performance.reward_records:
            await db.delete(rr)
        
        # 创建新的奖惩明细
        new_earned = sum(r.coins for r in request.reward_records if r.type == "reward")
        new_deducted = sum(r.coins for r in request.reward_records if r.type == "punishment")
        
        performance.coins_earned = new_earned
        performance.coins_deducted = new_deducted
        
        for item in request.reward_records:
            reward_record = RewardRecord(
                performance_id=performance.id,
                type=item.type,
                description=item.description,
                coins=item.coins,
            )
            db.add(reward_record)
        
        # 更新余额
        new_net = new_earned - new_deducted
        child.coin_balance = max(0, child.coin_balance + new_net)
    
    await db.flush()
    
    # 重新加载
    result = await db.execute(
        select(PerformanceRecord)
        .options(selectinload(PerformanceRecord.reward_records))
        .where(PerformanceRecord.id == performance.id)
    )
    performance = result.scalar_one()
    
    return PerformanceResponse(
        id=performance.id,
        child_id=performance.child_id,
        record_date=performance.record_date,
        overall_rating=performance.overall_rating,
        comment=performance.comment,
        coins_earned=performance.coins_earned,
        coins_deducted=performance.coins_deducted,
        reward_records=[
            RewardRecordResponse.model_validate(rr) for rr in performance.reward_records
        ],
        created_at=performance.created_at,
    )
