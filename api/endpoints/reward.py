"""
API 端点 - 奖励商城 & 奖励币 & 兑换管理
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db
from api.models.child import Child
from api.models.performance import PerformanceRecord, RewardRecord
from api.models.reward import RewardItem, CoinTransaction, RedemptionRecord
from api.models.user import User
from api.schemas.reward import (
    RewardItemCreateRequest,
    RewardItemUpdateRequest,
    RewardItemResponse,
    RewardItemListResponse,
    RedeemRequest,
    RedemptionResponse,
    RedemptionListResponse,
    CoinTransactionResponse,
    CoinBalanceResponse,
)
from api.services.family import get_current_family, get_current_member_role, require_family_owner
from api.utils.deps import get_current_user

# ============================================
# 奖励商城路由
# ============================================
reward_router = APIRouter(prefix="/api/reward-items", tags=["奖励商城"])


def _reward_item_response(item: RewardItem, can_manage: bool) -> RewardItemResponse:
    """把奖励商品模型转换成带管理权限的响应"""
    data = RewardItemResponse.model_validate(item)
    data.can_manage = can_manage
    return data


@reward_router.get("", response_model=RewardItemListResponse)
async def list_reward_items(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前家庭配置的所有奖励商品"""
    family = await get_current_family(db, current_user)
    if not family:
        return RewardItemListResponse(items=[], total=0, can_manage=False, has_family=False)
    can_manage = family.owner_user_id == current_user.id
    result = await db.execute(
        select(RewardItem)
        .where(RewardItem.family_id == family.id)
        .order_by(RewardItem.sort_order.asc(), RewardItem.created_at.asc())
    )
    items = result.scalars().all()
    
    return RewardItemListResponse(
        items=[_reward_item_response(item, can_manage) for item in items],
        total=len(items),
        can_manage=can_manage,
        has_family=True,
    )


@reward_router.post("", response_model=RewardItemResponse, status_code=status.HTTP_201_CREATED)
async def create_reward_item(
    request: RewardItemCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    创建奖励商品
    
    - **name**: 奖励名称（如"看电视30分钟"）
    - **coin_cost**: 所需奖励币数量
    - **description**: 奖励描述（可选）
    - **icon**: 图标（可选，默认🎁）
    """
    family = await require_family_owner(db, current_user)
    item = RewardItem(
        user_id=current_user.id,
        family_id=family.id,
        name=request.name,
        description=request.description,
        coin_cost=request.coin_cost,
        icon=request.icon,
        sort_order=request.sort_order,
    )
    db.add(item)
    await db.flush()
    await db.refresh(item)
    
    return _reward_item_response(item, True)


@reward_router.put("/{item_id}", response_model=RewardItemResponse)
async def update_reward_item(
    item_id: UUID,
    request: RewardItemUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新奖励商品"""
    family = await require_family_owner(db, current_user)
    result = await db.execute(
        select(RewardItem).where(
            RewardItem.id == item_id,
            RewardItem.family_id == family.id,
        )
    )
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到该奖励商品",
        )
    
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)
    
    await db.flush()
    await db.refresh(item)
    
    return _reward_item_response(item, True)


@reward_router.delete("/{item_id}", response_model=dict)
async def delete_reward_item(
    item_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除奖励商品"""
    family = await require_family_owner(db, current_user)
    result = await db.execute(
        select(RewardItem).where(
            RewardItem.id == item_id,
            RewardItem.family_id == family.id,
        )
    )
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到该奖励商品",
        )
    
    await db.delete(item)
    await db.flush()
    
    return {"message": "奖励商品已删除", "success": True}


# ============================================
# 奖励币与兑换路由
# ============================================
coin_router = APIRouter(prefix="/api/children/{child_id}", tags=["奖励币"])


async def _verify_child(child_id: UUID, family_id: UUID, db: AsyncSession) -> Child:
    """验证儿童属于当前家庭"""
    result = await db.execute(
        select(Child).where(Child.id == child_id, Child.family_id == family_id)
    )
    child = result.scalar_one_or_none()
    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到该儿童信息",
        )
    return child


async def _operator_snapshot(db: AsyncSession, current_user: User) -> dict:
    """生成奖励币流水操作者快照"""
    return {
        "operator_user_id": current_user.id,
        "operator_role": await get_current_member_role(db, current_user),
        "operator_nickname": current_user.nickname or current_user.username,
    }


@coin_router.get("/coins", response_model=CoinBalanceResponse)
async def get_coin_balance(
    child_id: UUID,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取儿童奖励币余额及交易流水
    
    支持分页查询交易流水记录。
    """
    family = await get_current_family(db, current_user)
    if not family:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先创建或加入家庭",
        )
    child = await _verify_child(child_id, family.id, db)
    
    # 查询原始流水后再按奖惩明细拆分，保证“主动收轮滑鞋 +3”这类单条奖励能独立展示。
    result = await db.execute(
        select(CoinTransaction)
        .where(CoinTransaction.child_id == child_id)
        .order_by(CoinTransaction.created_at.desc())
    )
    transactions = result.scalars().all()

    performance_ids = [
        t.related_performance_id for t in transactions if t.related_performance_id
    ]
    reward_record_map = {}
    performance_date_map = {}
    if performance_ids:
        # 加载 performance 的 record_date 用于归属日期显示
        perf_result = await db.execute(
            select(PerformanceRecord.id, PerformanceRecord.record_date)
            .where(PerformanceRecord.id.in_(performance_ids))
        )
        for perf_id, rec_date in perf_result.all():
            performance_date_map[perf_id] = rec_date

        reward_result = await db.execute(
            select(RewardRecord)
            .where(RewardRecord.performance_id.in_(performance_ids))
            .order_by(RewardRecord.created_at.desc())
        )
        for reward_record in reward_result.scalars().all():
            key = (reward_record.performance_id, reward_record.type)
            reward_record_map.setdefault(key, []).append(reward_record)

    transaction_items = []
    for t in transactions:
        record_type = "reward" if t.type == "earn" else "punishment"
        reward_records = reward_record_map.get((t.related_performance_id, record_type), [])

        if t.type in ("earn", "deduct") and reward_records:
            # 余额必须按真实发生顺序累加，最终展示排序在下方统一处理
            ordered_reward_records = sorted(reward_records, key=lambda record: record.created_at)
            total_coins = sum(r.coins for r in reward_records)
            running_balance = (
                t.balance_after - total_coins
                if t.type == "earn"
                else t.balance_after + total_coins
            )

            for reward_record in ordered_reward_records:
                amount = reward_record.coins if t.type == "earn" else -reward_record.coins
                running_balance = running_balance + amount
                transaction_items.append(CoinTransactionResponse(
                    id=reward_record.id,
                    type=t.type,
                    amount=amount,
                    balance_after=max(0, running_balance),
                    description=reward_record.description,
                    record_date=performance_date_map.get(t.related_performance_id),
                    operator_role=t.operator_role,
                    operator_nickname=t.operator_nickname,
                    created_at=reward_record.created_at,
                ))
            continue

        transaction_items.append(CoinTransactionResponse.model_validate(t))

    transaction_items.sort(key=lambda item: item.created_at, reverse=True)
    total = len(transaction_items)
    offset = (page - 1) * page_size
    page_items = transaction_items[offset:offset + page_size]
    
    return CoinBalanceResponse(
        child_id=child.id,
        child_name=child.name,
        balance=child.coin_balance,
        transactions=page_items,
        total_transactions=total,
    )


@coin_router.post("/redeem", response_model=RedemptionResponse, status_code=status.HTTP_201_CREATED)
async def redeem_reward(
    child_id: UUID,
    request: RedeemRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    兑换奖励
    
    使用奖励币兑换指定奖励商品。
    余额不足时会返回错误。
    """
    family = await get_current_family(db, current_user)
    if not family:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先创建或加入家庭",
        )
    child = await _verify_child(child_id, family.id, db)
    
    # 查找奖励商品
    result = await db.execute(
        select(RewardItem).where(
            RewardItem.id == request.reward_item_id,
            RewardItem.family_id == family.id,
            RewardItem.is_active == True,
        )
    )
    reward_item = result.scalar_one_or_none()
    
    if not reward_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到该奖励商品或已下架",
        )
    
    # 检查余额
    if child.coin_balance < reward_item.coin_cost:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"奖励币余额不足，当前 {child.coin_balance}，需要 {reward_item.coin_cost}",
        )
    
    # 扣除余额
    child.coin_balance -= reward_item.coin_cost
    
    # 创建兑换记录
    redemption = RedemptionRecord(
        child_id=child_id,
        reward_item_id=reward_item.id,
        reward_name=reward_item.name,
        coins_spent=reward_item.coin_cost,
        remaining_balance=child.coin_balance,
    )
    db.add(redemption)
    
    # 创建交易流水
    transaction = CoinTransaction(
        child_id=child_id,
        type="redeem",
        amount=-reward_item.coin_cost,
        balance_after=child.coin_balance,
        description=f"兑换奖励：{reward_item.name}",
        related_reward_item_id=reward_item.id,
        **await _operator_snapshot(db, current_user),
    )
    db.add(transaction)
    
    await db.flush()
    await db.refresh(redemption)
    
    return RedemptionResponse.model_validate(redemption)


@coin_router.get("/redemptions", response_model=RedemptionListResponse)
async def list_redemptions(
    child_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取兑换记录列表"""
    family = await get_current_family(db, current_user)
    if not family:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先创建或加入家庭",
        )
    await _verify_child(child_id, family.id, db)
    
    count_result = await db.execute(
        select(func.count()).select_from(RedemptionRecord).where(
            RedemptionRecord.child_id == child_id
        )
    )
    total = count_result.scalar()
    
    offset = (page - 1) * page_size
    result = await db.execute(
        select(RedemptionRecord)
        .where(RedemptionRecord.child_id == child_id)
        .order_by(RedemptionRecord.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    records = result.scalars().all()
    
    return RedemptionListResponse(
        records=[RedemptionResponse.model_validate(r) for r in records],
        total=total,
    )
