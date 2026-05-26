"""
API 端点 - 儿童信息管理
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db
from api.models.child import Child
from api.models.user import User
from api.schemas.child import (
    ChildCreateRequest,
    ChildUpdateRequest,
    ChildResponse,
    ChildListResponse,
)
from api.services.family import get_current_family, require_family_owner
from api.utils.deps import get_current_user

router = APIRouter(prefix="/api/children", tags=["儿童管理"])


async def _get_child_or_404(
    child_id: UUID, family_id: UUID, db: AsyncSession
) -> Child:
    """获取当前家庭下的儿童信息"""
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


def _child_response(child: Child, can_manage: bool) -> ChildResponse:
    """把儿童模型转换成带管理权限的响应"""
    data = ChildResponse.model_validate(child)
    data.can_manage = can_manage
    return data


@router.get("", response_model=ChildListResponse)
async def list_children(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前家庭的儿童列表"""
    family = await get_current_family(db, current_user)
    if not family:
        return ChildListResponse(children=[], total=0, can_manage=False, has_family=False)
    can_manage = family.owner_user_id == current_user.id
    result = await db.execute(
        select(Child)
        .where(Child.family_id == family.id)
        .order_by(Child.created_at.asc())
    )
    children = result.scalars().all()
    
    return ChildListResponse(
        children=[_child_response(c, can_manage) for c in children],
        total=len(children),
        can_manage=can_manage,
        has_family=True,
    )


@router.post("", response_model=ChildResponse, status_code=status.HTTP_201_CREATED)
async def create_child(
    request: ChildCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    添加儿童信息
    
    - **name**: 姓名（必填）
    - **gender**: 性别 male/female/other（可选）
    - **birthday**: 出生日期（可选）
    - **avatar_url**: 头像地址（可选）
    """
    family = await require_family_owner(db, current_user)
    child = Child(
        user_id=current_user.id,
        family_id=family.id,
        name=request.name,
        gender=request.gender,
        birthday=request.birthday,
        avatar_url=request.avatar_url,
        coin_balance=0,
    )
    db.add(child)
    await db.flush()
    await db.refresh(child)
    
    return ChildResponse.model_validate(child)


@router.get("/{child_id}", response_model=ChildResponse)
async def get_child(
    child_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取指定儿童详细信息"""
    family = await get_current_family(db, current_user)
    if not family:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先创建或加入家庭",
        )
    child = await _get_child_or_404(child_id, family.id, db)
    return _child_response(child, family.owner_user_id == current_user.id)


@router.put("/{child_id}", response_model=ChildResponse)
async def update_child(
    child_id: UUID,
    request: ChildUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    更新儿童信息
    
    - **name**: 姓名
    - **gender**: 性别
    - **birthday**: 出生日期
    - **avatar_url**: 头像地址
    """
    family = await require_family_owner(db, current_user)
    child = await _get_child_or_404(child_id, family.id, db)
    
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(child, field, value)
    
    await db.flush()
    await db.refresh(child)
    
    return _child_response(child, True)


@router.delete("/{child_id}", response_model=dict)
async def delete_child(
    child_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除儿童信息（同时删除关联的所有记录）"""
    family = await require_family_owner(db, current_user)
    child = await _get_child_or_404(child_id, family.id, db)
    
    await db.delete(child)
    await db.flush()
    
    return {"message": "儿童信息已删除", "success": True}
