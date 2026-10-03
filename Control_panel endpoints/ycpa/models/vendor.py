import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ycpa.core.database.base import Base


def utcnow():
    return datetime.now(timezone.utc)


class Vendor(Base):

    __tablename__ = "vendors"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    vendor_code: Mapped[str] = mapped_column(Text, nullable=False, unique=True, index=True)
    vendor_name: Mapped[str] = mapped_column(Text, nullable=False)
    display_name: Mapped[str] = mapped_column(Text, default="", nullable=False)
    vendor_type: Mapped[str] = mapped_column(Text, default="", nullable=False)
    registration_number: Mapped[str] = mapped_column(Text, default="", nullable=False)
    primary_contact_name: Mapped[str] = mapped_column(Text, default="", nullable=False)
    email: Mapped[str] = mapped_column(Text, default="", nullable=False)
    phone_number: Mapped[str] = mapped_column(Text, default="", nullable=False)
    alternate_phone: Mapped[str] = mapped_column(Text, default="", nullable=False)
    website: Mapped[str] = mapped_column(Text, default="", nullable=False)
    address_line1: Mapped[str] = mapped_column(Text, default="", nullable=False)
    address_line2: Mapped[str] = mapped_column(Text, default="", nullable=False)
    city: Mapped[str] = mapped_column(Text, default="", nullable=False)
    state: Mapped[str] = mapped_column(Text, default="", nullable=False)
    country: Mapped[str] = mapped_column(Text, default="", nullable=False)
    pincode: Mapped[str] = mapped_column(Text, default="", nullable=False)
    bank_name: Mapped[str] = mapped_column(Text, default="", nullable=False)
    account_number: Mapped[str] = mapped_column(Text, default="", nullable=False)
    ifsc_code: Mapped[str] = mapped_column(Text, default="", nullable=False)
    payment_terms: Mapped[str] = mapped_column(Text, default="", nullable=False)
    category: Mapped[str] = mapped_column(Text, default="", nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    rating: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    def __repr__(self):
        return f"<Vendor id={self.id} code={self.vendor_code} name={self.vendor_name}>"