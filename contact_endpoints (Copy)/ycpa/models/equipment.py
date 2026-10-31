import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ycpa.core.database.base import Base


def utcnow():
    return datetime.now(timezone.utc)


class Equipment(Base):
    __tablename__ = "equipment"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    equipment_code: Mapped[str] = mapped_column(Text, nullable=False, unique=True, index=True)
    equipment_name: Mapped[str] = mapped_column(Text, nullable=False)
    equipment_type: Mapped[str] = mapped_column(Text, default="", nullable=False)
    category: Mapped[str] = mapped_column(Text, default="", nullable=False)
    brand: Mapped[str] = mapped_column(Text, default="", nullable=False)
    make: Mapped[str] = mapped_column(Text, default="", nullable=False)
    model: Mapped[str] = mapped_column(Text, default="", nullable=False)
    model_number: Mapped[str] = mapped_column(Text, default="", nullable=False)
    serial_number: Mapped[str] = mapped_column(Text, default="", nullable=False)
    year_of_manufacture: Mapped[str] = mapped_column(Text, default="", nullable=False)
    ownership_type: Mapped[str] = mapped_column(Text, default="", nullable=False)
    vendor: Mapped[str] = mapped_column(Text, default="", nullable=False)
    weight: Mapped[str] = mapped_column(Text, default="", nullable=False)
    capacity: Mapped[str] = mapped_column(Text, default="", nullable=False)
    power_rating: Mapped[str] = mapped_column(Text, default="", nullable=False)
    current_site: Mapped[str] = mapped_column(Text, default="", nullable=False)
    assigned_project: Mapped[str] = mapped_column(Text, default="", nullable=False)
    assigned_site_location: Mapped[str] = mapped_column(Text, default="", nullable=False)
    assigned_to: Mapped[str] = mapped_column(Text, default="", nullable=False)
    operator_assigned: Mapped[str] = mapped_column(Text, default="", nullable=False)
    status: Mapped[str] = mapped_column(Text, default="Active", nullable=False)
    current_status: Mapped[str] = mapped_column(Text, default="", nullable=False)
    purchase_date: Mapped[str] = mapped_column(Text, default="", nullable=False)
    purchase_cost: Mapped[str] = mapped_column(Text, default="", nullable=False)
    rental_end_date: Mapped[str] = mapped_column(Text, default="", nullable=False)
    warranty_expiry: Mapped[str] = mapped_column(Text, default="", nullable=False)
    warranty_expiry_date: Mapped[str] = mapped_column(Text, default="", nullable=False)
    last_maintenance: Mapped[str] = mapped_column(Text, default="", nullable=False)
    last_maintenance_date: Mapped[str] = mapped_column(Text, default="", nullable=False)
    next_maintenance: Mapped[str] = mapped_column(Text, default="", nullable=False)
    next_maintenance_due: Mapped[str] = mapped_column(Text, default="", nullable=False)
    maintenance_interval: Mapped[str] = mapped_column(Text, default="", nullable=False)
    maintenance_log: Mapped[str] = mapped_column(Text, default="", nullable=False)
    depreciation_rate: Mapped[str] = mapped_column(Text, default="", nullable=False)
    current_value: Mapped[str] = mapped_column(Text, default="", nullable=False)
    insurance_provider: Mapped[str] = mapped_column(Text, default="", nullable=False)
    insurance_expiry: Mapped[str] = mapped_column(Text, default="", nullable=False)
    insurance_expiry_date: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )
