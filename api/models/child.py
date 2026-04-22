"""
SQLAlchemy 模型 - 儿童信息表
"""
import uuid
from datetime import date, datetime
from sqlalchemy import String, Integer, Date, DateTime, ForeignKey, func, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.database import Base


class Child(Base):
    __tablename__ = "children"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    gender: Mapped[str | None] = mapped_column(String(10), nullable=True)
    birthday: Mapped[date | None] = mapped_column(Date, nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    coin_balance: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint("coin_balance >= 0", name="check_coin_balance_positive"),
        CheckConstraint("gender IN ('male', 'female', 'other')", name="check_gender_valid"),
    )

    # 关联关系
    parent: Mapped["User"] = relationship("User", back_populates="children")
    performance_records: Mapped[list["PerformanceRecord"]] = relationship(
        "PerformanceRecord", back_populates="child", cascade="all, delete-orphan"
    )
    coin_transactions: Mapped[list["CoinTransaction"]] = relationship(
        "CoinTransaction", back_populates="child", cascade="all, delete-orphan"
    )
    redemption_records: Mapped[list["RedemptionRecord"]] = relationship(
        "RedemptionRecord", back_populates="child", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Child {self.name}>"


# 避免循环导入
from api.models.user import User  # noqa: E402, F401
from api.models.performance import PerformanceRecord  # noqa: E402, F401
from api.models.reward import CoinTransaction, RedemptionRecord  # noqa: E402, F401
