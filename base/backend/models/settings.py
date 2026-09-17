import uuid

from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from backend.core.database import Base  # ⚠️ confirm this matches your actual import


class ProfileSettings(Base):
    __tablename__ = "profile_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)

    name = Column(String(255), nullable=False)
    email_id = Column(String(255), nullable=False)
    profile_image = Column(String, nullable=True)
    contact_number = Column(String(15), nullable=False)
    contact_address = Column(String, nullable=False)
    country = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    district = Column(String(100), nullable=False)
    pincode = Column(String(10), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())  # ⚠️ needs matching relationship on User model
