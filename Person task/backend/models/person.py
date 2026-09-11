import uuid
from datetime import datetime,timezone
from sqlalchemy import String, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped,mapped_column

from backend.core.database.base import Base

def utcnow():
    return datetime.now(timezone.utc)

class Person(Base):
    __tablename__ = "persons"
    id : Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key = True,
        default = uuid.uuid4
    )
    name : Mapped[str] = mapped_column(
        String(50),
        nullable = False,
        index = True
    )
    age : Mapped[int] = mapped_column(
        Integer,
        nullable = False
    )
    created_at : Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default = utcnow,
        nullable = False
    )
    updated_at : Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default = utcnow,
        onupdate = utcnow,
        nullable = False
    )
    deleted_at : Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable = True
    )
