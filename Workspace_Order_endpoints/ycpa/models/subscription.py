import uuid
from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ycpa.core.database.base import Base


def utcnow():
    return datetime.now(timezone.utc)


class PimSubscription(Base):
    __tablename__ = "pim_subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    plan: Mapped[str] = mapped_column(Text, default="free", nullable=False)
    status: Mapped[str] = mapped_column(Text, default="active", nullable=False)
    max_pim_workspaces: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    max_projects_per_pim_workspace: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    max_members_per_workspace: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    max_members_per_project: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    can_use_4d: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_use_5d: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_use_clash_detection: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_export_bcf: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    can_use_api: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    stripe_customer_id: Mapped[str | None] = mapped_column(Text, unique=True, nullable=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(Text, unique=True, nullable=True)
    stripe_price_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    billing_period: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_manually_overridden: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    override_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    overridden_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    overridden_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    def __repr__(self):
        return f"<PimSubscription user_id={self.user_id} plan={self.plan}>"


class AimSubscription(Base):
    __tablename__ = "aim_subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    plan: Mapped[str] = mapped_column(Text, default="free", nullable=False)
    status: Mapped[str] = mapped_column(Text, default="active", nullable=False)
    max_aim_workspaces: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    max_projects_per_aim_workspace: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    max_members_per_workspace: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    max_members_per_project: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    can_use_ai: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_use_api: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_use_maintenance: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    can_use_facility: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    stripe_customer_id: Mapped[str | None] = mapped_column(Text, unique=True, nullable=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(Text, unique=True, nullable=True)
    stripe_price_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    billing_period: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_manually_overridden: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    override_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    overridden_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    overridden_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    def __repr__(self):
        return f"<AimSubscription user_id={self.user_id} plan={self.plan}>"


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_type: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price_monthly: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    price_yearly: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    stripe_price_id_monthly: Mapped[str | None] = mapped_column(Text, nullable=True)
    stripe_price_id_yearly: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Limits
    max_workspaces: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    max_projects_per_workspace: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    max_members_per_workspace: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    max_members_per_project: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    max_storage_bytes: Mapped[int] = mapped_column(BigInteger, default=5368709120, nullable=False)  # 5GB

    # PIM feature flags
    can_use_4d: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_use_5d: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_use_clash_detection: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_export_bcf: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # AIM feature flags
    can_use_ai: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_use_maintenance: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    can_use_facility: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Common
    can_use_api: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # default free plan
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    def __repr__(self):
        return f"<SubscriptionPlan product_type={self.product_type} name={self.name}>"
