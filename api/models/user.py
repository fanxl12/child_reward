"""
SQLAlchemy 模型 - 用户表
"""
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Boolean, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.database import Base


class User(Base):
    """用户账户，角色用于家庭内展示奖励币操作者身份"""
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    password_initialized: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    nickname: Mapped[str | None] = mapped_column(String(50), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    wechat_openid: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    role: Mapped[str] = mapped_column(String(10), nullable=False, default="妈妈", server_default="妈妈")
    current_family_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("families.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # 关联关系
    children: Mapped[list["Child"]] = relationship(
        "Child", back_populates="parent", cascade="all, delete-orphan"
    )
    reward_items: Mapped[list["RewardItem"]] = relationship(
        "RewardItem", back_populates="owner", cascade="all, delete-orphan"
    )
    family_memberships: Mapped[list["FamilyMember"]] = relationship(
        "FamilyMember", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User {self.username}>"

    @property
    def has_password(self) -> bool:
        return bool(self.password_initialized)


# 避免循环导入
from api.models.child import Child  # noqa: E402, F401
from api.models.reward import RewardItem  # noqa: E402, F401
from api.models.family import FamilyMember  # noqa: E402, F401
