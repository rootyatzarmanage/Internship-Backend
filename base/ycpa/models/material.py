import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ycpa.core.database.base import Base


def utcnow():
    return datetime.now(timezone.utc)


class Material(Base):
    __tablename__ = "materials"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    material_code: Mapped[str] = mapped_column(Text, nullable=False, unique=True, index=True)
    material_name: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(Text, default="", nullable=False)
    grade: Mapped[str] = mapped_column(Text, default="", nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    unit_of_measurement: Mapped[str] = mapped_column(Text, default="", nullable=False)
    current_stock: Mapped[str] = mapped_column(Text, default="", nullable=False)
    minimum_stock: Mapped[str] = mapped_column(Text, default="", nullable=False)
    reorder_level: Mapped[str] = mapped_column(Text, default="", nullable=False)
    supplier_name: Mapped[str] = mapped_column(Text, default="", nullable=False)
    supplier_contact: Mapped[str] = mapped_column(Text, default="", nullable=False)
    lead_time_days: Mapped[str] = mapped_column(Text, default="", nullable=False)
    storage_location: Mapped[str] = mapped_column(Text, default="", nullable=False)
    storage_condition: Mapped[str] = mapped_column(Text, default="", nullable=False)
    batch_number: Mapped[str] = mapped_column(Text, default="", nullable=False)
    expiry_date: Mapped[str] = mapped_column(Text, default="", nullable=False)
    purchase_rate: Mapped[str] = mapped_column(Text, default="", nullable=False)
    total_value: Mapped[str] = mapped_column(Text, default="", nullable=False)
    hsn_code: Mapped[str] = mapped_column(Text, default="", nullable=False)
    gst_rate: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )
