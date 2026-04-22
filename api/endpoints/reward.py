"""
API 端点 - 奖励商城 & 奖励币 & 兑换管理
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db
from api.models.child import Child
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
from api.utils.deps import get_current_user

# ============================================
# 奖励商城路由
# ============================================
reward_router = APIRouter(prefix="/api/reward-items", tags=["奖励商城"])


@reward_router.get("", response_model=RewardItemListResponse)
async def list_reward_items(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户配置的所有奖励商品"""
    result = await db.execute(
        select(RewardItem)
        .where(RewardItem.user_id == current_user.id)
        .order_by(RewardItem.sort_order.asc(), RewardItem.created_at.asc())
    )
    items = result.scalars().all()
    
    return RewardItemListResponse(
        items=[RewardItemResponse.model_validate(item) for item in items],
        total=len(items),
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
    item = RewardItem(
        user_id=current_user.id,
        name=request.name,
        description=request.description,
        coin_cost=request.coin_cost,
        icon=request.icon,
        sort_order=request.sort_order,
    )
    db.add(item)
    await db.flush()
    await db.refresh(item)
    
    return RewardItemResponse.model_validate(item)


@reward_router.put("/{item_id}", response_model=RewardItemResponse)
async def update_reward_item(
    item_id: UUID,
    request: RewardItemUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新奖励商品"""
    result = await db.execute(
        select(RewardItem).where(
            RewardItem.id == item_id,
            RewardItem.user_id == current_user.id,
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
    
    return RewardItemResponse.model_validate(item)


@reward_router.delete("/{item_id}", response_model=dict)
async def delete_reward_item(
    item_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除奖励商品"""
    result = await db.execute(
        select(RewardItem).where(
            RewardItem.id == item_id,
            RewardItem.user_id == current_user.id,
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


async def _verify_child(child_id: UUID, user_id: UUID, db: AsyncSession) -> Child:
    """验证儿童归属"""
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
    child = await _verify_child(child_id, current_user.id, db)
    
    # 查询总数
    count_result = await db.execute(
        select(func.count()).select_from(CoinTransaction).where(
            CoinTransaction.child_id == child_id
        )
    )
    total = count_result.scalar()
    
    # 查询流水
    offset = (page - 1) * page_size
    result = await db.execute(
        select(CoinTransaction)
        .where(CoinTransaction.child_id == child_id)
        .order_by(CoinTransaction.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    transactions = result.scalars().all()
    
    return CoinBalanceResponse(
        child_id=child.id,
        child_name=child.name,
        balance=child.coin_balance,
        transactions=[
            CoinTransactionResponse.model_validate(t) for t in transactions
        ],
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
    child = await _verify_child(child_id, current_user.id, db)
    
    # 查找奖励商品
    result = await db.execute(
        select(RewardItem).where(
            RewardItem.id == request.reward_item_id,
            RewardItem.user_id == current_user.id,
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
    await _verify_child(child_id, current_user.id, db)
    
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
