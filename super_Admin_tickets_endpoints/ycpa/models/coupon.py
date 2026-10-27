import uuid
from datetime import datetime, timezone
import enum

from sqlalchemy import String, Integer, Numeric, DateTime, Enum as SAEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ycpa.core.database.base import Base


def utcnow():
    return datetime.now(timezone.utc)


class DiscountType(str, enum.Enum):
    percentage = "percentage"
    flat = "flat"


class CouponStatus(str, enum.Enum):
    draft = "draft"
    active = "active"
    expired = "expired"
    disabled = "disabled"
    archived = "archived"


class Coupon(Base):
    __tablename__ = "coupons"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    discount_type: Mapped[DiscountType] = mapped_column(
        SAEnum(DiscountType, name="coupon_discount_type"), nullable=False
    )
    value: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    max_uses: Mapped[int | None] = mapped_column(Integer, nullable=True)
    used_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[CouponStatus] = mapped_column(
        SAEnum(CouponStatus, name="coupon_status"), default=CouponStatus.draft, nullable=False
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)