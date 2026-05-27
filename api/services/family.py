"""
家庭服务：封装家庭创建、当前家庭和权限判断
"""
import random
import string
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.family import Family, FamilyMember
from api.models.user import User


CODE_CHARS = string.ascii_uppercase + string.digits


async def generate_family_code(db: AsyncSession) -> str:
    """生成 6 位家庭编号，并确保数据库内唯一"""
    for _ in range(20):
        code = "".join(random.choice(CODE_CHARS) for _ in range(6))
        result = await db.execute(select(Family).where(Family.code == code))
        if result.scalar_one_or_none() is None:
            return code
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="家庭编号生成失败，请重试",
    )


async def create_family_for_user(db: AsyncSession, user: User, name: str | None = None) -> Family:
    """为用户创建家庭，一个用户只能创建一个自己的家庭"""
    existing = await db.execute(select(Family).where(Family.owner_user_id == user.id))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="一个用户只能创建一个家庭",
        )

    family_name = name or f"{user.nickname or user.username}的家庭"
    family = Family(
        name=family_name,
        code=await generate_family_code(db),
        owner_user_id=user.id,
    )
    db.add(family)
    await db.flush()

    # 创建家庭时只有创建者一个成员，保留默认角色；加入家庭的成员不默认分配角色
    db.add(FamilyMember(family_id=family.id, user_id=user.id, role="妈妈"))
    user.current_family_id = family.id
    await db.flush()
    await db.refresh(family)
    return family


async def ensure_selected_family(db: AsyncSession, user: User) -> Family | None:
    """确保已有家庭时选中一个家庭；没有家庭时不自动创建"""
    if user.current_family_id:
        family = await get_member_family(db, user, user.current_family_id)
        if family:
            return family

    result = await db.execute(
        select(Family)
        .join(FamilyMember, FamilyMember.family_id == Family.id)
        .where(FamilyMember.user_id == user.id)
        .order_by(Family.created_at.asc())
    )
    family = result.scalars().first()
    if family:
        user.current_family_id = family.id
        await db.flush()
        return family

    user.current_family_id = None
    await db.flush()
    return None


async def get_member_family(db: AsyncSession, user: User, family_id: UUID | None) -> Family | None:
    """查询用户已加入的指定家庭"""
    if not family_id:
        return None
    result = await db.execute(
        select(Family)
        .join(FamilyMember, FamilyMember.family_id == Family.id)
        .where(Family.id == family_id, FamilyMember.user_id == user.id)
    )
    return result.scalar_one_or_none()


async def get_current_family_member(db: AsyncSession, user: User) -> FamilyMember | None:
    """获取用户在当前家庭中的成员关系，角色从这里读取"""
    family = await get_current_family(db, user)
    if not family:
        return None
    result = await db.execute(
        select(FamilyMember).where(
            FamilyMember.family_id == family.id,
            FamilyMember.user_id == user.id,
        )
    )
    return result.scalar_one_or_none()


async def get_current_member_role(db: AsyncSession, user: User) -> str | None:
    """获取用户在当前家庭中的角色"""
    member = await get_current_family_member(db, user)
    return member.role if member else None


async def get_current_family(db: AsyncSession, user: User) -> Family | None:
    """获取当前选中家庭；用户未创建或加入家庭时返回 None"""
    return await ensure_selected_family(db, user)


async def require_family_owner(db: AsyncSession, user: User) -> Family:
    """要求当前用户是当前家庭创建者"""
    family = await get_current_family(db, user)
    if not family:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先创建或加入家庭",
        )
    if family.owner_user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有家庭创建者可以维护儿童和奖励商品",
        )
    return family
