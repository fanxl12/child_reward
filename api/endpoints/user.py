"""
API 端点 - 用户管理（注册/登录/个人信息）
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db
from api.models.user import User
from api.schemas.user import (
    UserRegisterRequest,
    UserLoginRequest,
    WechatLoginRequest,
    UserUpdateRequest,
    ChangePasswordRequest,
    SetPasswordRequest,
    UserResponse,
    TokenResponse,
    MessageResponse,
)
from api.utils.auth import get_password_hash, verify_password, create_access_token
from api.utils.deps import get_current_user
from api.services.wechat import wechat_service

router = APIRouter(prefix="/api/auth", tags=["用户认证"])
user_router = APIRouter(prefix="/api/users", tags=["用户管理"])


# ============================================
# 认证接口
# ============================================

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    用户注册
    
    - **username**: 用户名（3-50字符，唯一）
    - **password**: 密码（6位以上）
    - **phone**: 手机号码（可选）
    - **nickname**: 昵称（可选）
    """
    # 检查用户名是否已存在
    existing = await db.execute(
        select(User).where(User.username == request.username)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已被注册",
        )
    
    # 检查手机号是否已存在
    if request.phone:
        existing_phone = await db.execute(
            select(User).where(User.phone == request.phone)
        )
        if existing_phone.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该手机号已被注册",
            )
    
    # 创建用户
    user = User(
        username=request.username,
        password_hash=get_password_hash(request.password),
        password_initialized=True,
        phone=request.phone,
        nickname=request.nickname or request.username,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    
    # 生成令牌
    access_token = create_access_token(user.id)
    
    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: UserLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    用户登录
    
    - **username**: 用户名
    - **password**: 密码
    """
    # 查找用户
    result = await db.execute(
        select(User).where(User.username == request.username)
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )
    
    # 生成令牌
    access_token = create_access_token(user.id)
    
    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/wechat-login", response_model=TokenResponse)
async def wechat_login(
    request: WechatLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    微信小程序登录
    
    - **code**: 微信登录临时凭证
    
    流程：
    1. 使用 code 换取 openid
    2. 根据 openid 查找或创建用户
    3. 返回 JWT Token
    """
    # 调用微信 API 获取 openid
    session_data = await wechat_service.code2session(request.code)
    
    if not session_data or not session_data.get("openid"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="微信登录失败，请重试",
        )
    
    openid = session_data["openid"]
    
    # 查找是否已有该微信用户
    result = await db.execute(
        select(User).where(User.wechat_openid == openid)
    )
    user = result.scalar_one_or_none()
    
    # 如果用户不存在，创建新用户
    if not user:
        user = User(
            username=f"wx_{openid[:8]}",  # 使用 openid 前8位作为用户名
            password_hash=get_password_hash(openid),  # 使用 openid 作为密码
            password_initialized=False,
            nickname="微信用户",
            wechat_openid=openid,
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)
    
    # 生成令牌
    access_token = create_access_token(user.id)
    
    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user),
    )


# ============================================
# 用户信息接口
# ============================================

@user_router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """获取当前登录用户信息"""
    return UserResponse.model_validate(current_user)


@user_router.put("/me", response_model=UserResponse)
async def update_me(
    request: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    更新当前用户信息
    
    - **username**: 用户名（3-50 字符，全局唯一）
    - **nickname**: 昵称
    - **avatar_url**: 头像地址
    - **phone**: 手机号码
    """
    update_data = request.model_dump(exclude_unset=True)
    
    # 检查用户名唯一性
    if "username" in update_data and update_data["username"] is not None:
        new_username = update_data["username"].strip()
        if len(new_username) < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名至少 3 个字符",
            )
        if new_username != current_user.username:
            existing = await db.execute(
                select(User).where(
                    User.username == new_username,
                    User.id != current_user.id,
                )
            )
            if existing.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="用户名已被占用",
                )
        update_data["username"] = new_username
    
    # 检查手机号唯一性
    if "phone" in update_data and update_data["phone"]:
        existing = await db.execute(
            select(User).where(
                User.phone == update_data["phone"],
                User.id != current_user.id,
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该手机号已被其他用户使用",
            )
    
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    await db.flush()
    await db.refresh(current_user)
    
    return UserResponse.model_validate(current_user)


@user_router.post("/change-password", response_model=MessageResponse)
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """修改密码"""
    if not current_user.password_initialized:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前账号尚未设置密码，请先设置密码",
        )

    if not verify_password(request.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="原密码不正确",
        )
    
    current_user.password_hash = get_password_hash(request.new_password)
    await db.flush()
    
    return MessageResponse(message="密码修改成功")


@user_router.post("/set-password", response_model=MessageResponse)
async def set_password(
    request: SetPasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """微信账号首次设置密码（无需原密码）"""
    if current_user.password_initialized:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前账号已设置密码，请使用修改密码功能",
        )

    current_user.password_hash = get_password_hash(request.new_password)
    current_user.password_initialized = True
    await db.flush()

    return MessageResponse(message="密码设置成功")
