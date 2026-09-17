import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.core.database.base import Base


def utcnow():
    return datetime.now(timezone.utc)


class Employee(Base):

    __tablename__ = "employees"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    employee_code: Mapped[str] = mapped_column(
        Text, nullable=False, unique=True, index=True
    )
    full_name: Mapped[str] = mapped_column(Text, nullable=False)
    date_of_birth: Mapped[str] = mapped_column(Text, default="", nullable=False)
    gender: Mapped[str] = mapped_column(Text, default="", nullable=False)
    blood_group: Mapped[str] = mapped_column(Text, default="", nullable=False)
    email: Mapped[str] = mapped_column(Text, default="", nullable=False)
    phone_number: Mapped[str] = mapped_column(Text, default="", nullable=False)
    emergency_contact_name: Mapped[str] = mapped_column(Text, default="", nullable=False)
    emergency_contact_phone: Mapped[str] = mapped_column(Text, default="", nullable=False)
    address_line1: Mapped[str] = mapped_column(Text, default="", nullable=False)
    address_line2: Mapped[str] = mapped_column(Text, default="", nullable=False)
    city: Mapped[str] = mapped_column(Text, default="", nullable=False)
    state: Mapped[str] = mapped_column(Text, default="", nullable=False)
    pincode: Mapped[str] = mapped_column(Text, default="", nullable=False)
    country: Mapped[str] = mapped_column(Text, default="", nullable=False)
    designation: Mapped[str] = mapped_column(Text, default="", nullable=False)
    department: Mapped[str] = mapped_column(Text, default="", nullable=False)
    employment_type: Mapped[str] = mapped_column(Text, default="", nullable=False)
    date_of_joining: Mapped[str] = mapped_column(Text, default="", nullable=False)
    reporting_manager: Mapped[str] = mapped_column(Text, default="", nullable=False)
    site_assigned: Mapped[str] = mapped_column(Text, default="", nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    salary_type: Mapped[str] = mapped_column(Text, default="", nullable=False)
    base_salary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    bank_name: Mapped[str] = mapped_column(Text, default="", nullable=False)
    account_number: Mapped[str] = mapped_column(Text, default="", nullable=False)
    ifsc_code: Mapped[str] = mapped_column(Text, default="", nullable=False)
    aadhaar_number: Mapped[str] = mapped_column(Text, default="", nullable=False)
    pan_number: Mapped[str] = mapped_column(Text, default="", nullable=False)
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
        return f"<Employee id={self.id} code={self.employee_code} name={self.full_name}>"