"""
API 端点 - 家庭管理
"""
from uuid import UUID

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
    FamilyUpdateRequest,
)
from api.schemas.user import MessageResponse
from api.services.family import (
    assign_unused_family_role,
    create_family_for_user,
    ensure_selected_family,
    get_member_family,
)
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


# 家庭创建者修改当前选中家庭的名称
@router.put("/current", response_model=FamilyResponse)
async def update_current_family(
    request: FamilyUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """家庭创建者修改当前家庭名称"""
    family = await ensure_selected_family(db, current_user)
    if not family:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先创建或加入家庭",
        )
    if family.owner_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有家庭创建者可以修改家庭名称",
        )

    family_name = request.name.strip()
    if not family_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="家庭名称不能为空",
        )

    # 只修改当前家庭名称，家庭编号和成员关系都保持不变
    family.name = family_name
    await db.flush()
    await db.refresh(family)
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
    current_member = member.scalar_one_or_none()
    if current_member is None:
        # 加入家庭时分配一个未使用角色，保证同一家庭成员角色不重复
        role = await assign_unused_family_role(db, family.id)
        db.add(FamilyMember(family_id=family.id, user_id=current_user.id, role=role))
    elif current_member.role is None:
        # 兼容旧数据：已加入但未设置角色时，也补一个未使用角色
        current_member.role = await assign_unused_family_role(db, family.id)

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


@router.delete("/{family_id}/membership", response_model=MessageResponse)
async def leave_family(
    family_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """退出已加入的家庭，家庭创建者不能退出自己的家庭"""
    family_result = await db.execute(select(Family).where(Family.id == family_id))
    family = family_result.scalar_one_or_none()
    if not family:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到该家庭",
        )
    if family.owner_user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="家庭创建者不能退出自己的家庭",
        )

    member_result = await db.execute(
        select(FamilyMember).where(
            FamilyMember.family_id == family.id,
            FamilyMember.user_id == current_user.id,
        )
    )
    member = member_result.scalar_one_or_none()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未加入该家庭",
        )

    # 只删除当前用户的成员关系，不影响家庭本身和其他成员的数据
    await db.delete(member)

    if current_user.current_family_id == family.id:
        # 退出当前家庭后，自动切换到还加入的第一个家庭；没有剩余家庭则置空
        next_family_result = await db.execute(
            select(Family)
            .join(FamilyMember, FamilyMember.family_id == Family.id)
            .where(
                FamilyMember.user_id == current_user.id,
                Family.id != family.id,
            )
            .order_by(Family.created_at.asc())
        )
        next_family = next_family_result.scalars().first()
        current_user.current_family_id = next_family.id if next_family else None

    await db.flush()
    return MessageResponse(message="已退出家庭")
