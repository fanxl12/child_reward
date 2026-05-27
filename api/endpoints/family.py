"""
API 端点 - 家庭管理
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db
from api.models.family import Family, FamilyMember
from api.models.user import User
from api.schemas.family import (
    FamilyCreateRequest,
    FamilyJoinRequest,
    FamilyListResponse,
    FamilyResponse,
    FamilySwitchRequest,
)
from api.schemas.user import MessageResponse
from api.services.family import create_family_for_user, ensure_selected_family, get_member_family
from api.utils.deps import get_current_user

router = APIRouter(prefix="/api/families", tags=["家庭管理"])


async def _family_response(db: AsyncSession, family: Family, user: User) -> FamilyResponse:
    """把家庭模型转换成带权限标记的响应"""
    member_result = await db.execute(
        select(FamilyMember).where(
            FamilyMember.family_id == family.id,
            FamilyMember.user_id == user.id,
        )
    )
    member = member_result.scalar_one_or_none()
    return FamilyResponse(
        id=family.id,
        name=family.name,
        code=family.code,
        owner_user_id=family.owner_user_id,
        is_owner=family.owner_user_id == user.id,
        role=member.role if member else None,
        created_at=family.created_at,
    )


@router.get("", response_model=FamilyListResponse)
async def list_families(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户加入的家庭列表"""
    await ensure_selected_family(db, current_user)
    result = await db.execute(
        select(Family)
        .join(FamilyMember, FamilyMember.family_id == Family.id)
        .where(FamilyMember.user_id == current_user.id)
        .order_by(Family.created_at.asc())
    )
    families = result.scalars().all()
    family_items = []
    for family in families:
        family_items.append(await _family_response(db, family, current_user))

    return FamilyListResponse(
        families=family_items,
        current_family_id=current_user.current_family_id,
        total=len(families),
    )


@router.post("", response_model=FamilyResponse, status_code=status.HTTP_201_CREATED)
async def create_family(
    request: FamilyCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建家庭；每个用户只能创建一个自己的家庭"""
    family = await create_family_for_user(db, current_user, request.name)
    return await _family_response(db, family, current_user)


@router.post("/join", response_model=FamilyResponse)
async def join_family(
    request: FamilyJoinRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """通过家庭编号加入家庭"""
    code = request.code.strip().upper()
    result = await db.execute(select(Family).where(Family.code == code))
    family = result.scalar_one_or_none()
    if not family:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到该家庭编号",
        )

    member = await db.execute(
        select(FamilyMember).where(
            FamilyMember.family_id == family.id,
            FamilyMember.user_id == current_user.id,
        )
    )
    if member.scalar_one_or_none() is None:
        db.add(FamilyMember(family_id=family.id, user_id=current_user.id))

    current_user.current_family_id = family.id
    await db.flush()
    return await _family_response(db, family, current_user)


@router.post("/switch", response_model=MessageResponse)
async def switch_family(
    request: FamilySwitchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """切换我的当前家庭"""
    family = await get_member_family(db, current_user, request.family_id)
    if not family:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未加入该家庭",
        )

    current_user.current_family_id = family.id
    await db.flush()
    return MessageResponse(message="家庭切换成功")
