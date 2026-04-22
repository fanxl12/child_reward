"""
SQLAlchemy 模型 - 表现记录表 & 奖惩明细
"""
import uuid
from datetime import date, datetime
from sqlalchemy import String, Integer, Text, Date, DateTime, ForeignKey, UniqueConstraint, func, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.database import Base


class PerformanceRecord(Base):
    __tablename__ = "performance_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    child_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("children.id", ondelete="CASCADE"), nullable=False
    )
    record_date: Mapped[date] = mapped_column(Date, nullable=False)
    overall_rating: Mapped[str] = mapped_column(String(10), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    coins_earned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    coins_deducted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint("child_id", "record_date", name="uq_child_date"),
        CheckConstraint("overall_rating IN ('good', 'bad')", name="check_rating_valid"),
        CheckConstraint("coins_earned >= 0", name="check_coins_earned_positive"),
        CheckConstraint("coins_deducted >= 0", name="check_coins_deducted_positive"),
    )

    # 关联关系
    child: Mapped["Child"] = relationship("Child", back_populates="performance_records")
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by])
    reward_records: Mapped[list["RewardRecord"]] = relationship(
        "RewardRecord", back_populates="performance", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<PerformanceRecord {self.record_date} {self.overall_rating}>"


class RewardRecord(Base):
    __tablename__ = "reward_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    performance_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("performance_records.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[str] = mapped_column(String(10), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    coins: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint("type IN ('reward', 'punishment')", name="check_record_type_valid"),
        CheckConstraint("coins > 0", name="check_record_coins_positive"),
    )

    # 关联关系
    performance: Mapped["PerformanceRecord"] = relationship(
        "PerformanceRecord", back_populates="reward_records"
    )

    def __repr__(self) -> str:
        return f"<RewardRecord {self.type} {self.coins}>"


# 避免循环导入
from api.models.child import Child  # noqa: E402, F401
from api.models.user import User  # noqa: E402, F401
