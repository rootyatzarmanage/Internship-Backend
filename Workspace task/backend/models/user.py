import uuid
from datetime import datetime,timezone
from sqlalchemy import String, Boolean,  DateTime,Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped,mapped_column
from backend.core.database.base import Base

def utcnow():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"
    id : Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default = uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String[255],
        nullable=False,
        unique=True,
        index = True
    )
    password_hash : Mapped[str] = mapped_column(
        String[255],
        nullable=False
    )
    full_name : Mapped[str] = mapped_column(
        String[100],
        nullable=False
    )
    is_active : Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False
    )
    created_at : Mapped[datetime] = mapped_column(
        DateTime(timezone = True),
        default= utcnow,
        nullable=False
    )
    updated_at : Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default = utcnow,
        onupdate= utcnow,
        nullable= False
    )
    deleted_at : Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable= True
    )
