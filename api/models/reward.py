"""
SQLAlchemy 模型 - 奖励商城 & 交易流水 & 兑换记录
"""
import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Text, Boolean, DateTime, ForeignKey, func, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.database import Base


class RewardItem(Base):
    __tablename__ = "reward_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    coin_cost: Mapped[int] = mapped_column(Integer, nullable=False)
    icon: Mapped[str] = mapped_column(String(100), default="🎁")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint("coin_cost > 0", name="check_coin_cost_positive"),
    )

    # 关联关系
    owner: Mapped["User"] = relationship("User", back_populates="reward_items")

    def __repr__(self) -> str:
        return f"<RewardItem {self.name} cost={self.coin_cost}>"


class CoinTransaction(Base):
    __tablename__ = "coin_transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    child_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("children.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    related_performance_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("performance_records.id", ondelete="SET NULL"), nullable=True
    )
    related_reward_item_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reward_items.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint("type IN ('earn', 'deduct', 'redeem')", name="check_transaction_type_valid"),
    )

    # 关联关系
    child: Mapped["Child"] = relationship("Child", back_populates="coin_transactions")

    def __repr__(self) -> str:
        return f"<CoinTransaction {self.type} {self.amount}>"


class RedemptionRecord(Base):
    __tablename__ = "redemption_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    child_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("children.id", ondelete="CASCADE"), nullable=False
    )
    reward_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reward_items.id"), nullable=False
    )
    reward_name: Mapped[str] = mapped_column(String(100), nullable=False)
    coins_spent: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint("coins_spent > 0", name="check_coins_spent_positive"),
        CheckConstraint(
            "status IN ('pending', 'approved', 'rejected', 'completed')",
            name="check_redemption_status_valid"
        ),
    )

    # 关联关系
    child: Mapped["Child"] = relationship("Child", back_populates="redemption_records")
    reward_item: Mapped["RewardItem"] = relationship("RewardItem")

    def __repr__(self) -> str:
        return f"<RedemptionRecord {self.reward_name} status={self.status}>"


# 避免循环导入
from api.models.user import User  # noqa: E402, F401
from api.models.child import Child  # noqa: E402, F401
