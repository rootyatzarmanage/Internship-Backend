import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from ycpa.core.database.base import Base


def utcnow():
    return datetime.now(timezone.utc)


class ControlPanel(Base):
    __tablename__ = "ControlPanel"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(Text, unique=True, index=True, nullable=False) 
    name: Mapped[str] = mapped_column(Text, nullable=False)
    name_prefix: Mapped[str | None] = mapped_column(Text, nullable=True)  
    value: Mapped[str | None] = mapped_column(Text, nullable=True)        
    value_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True) 
    # 1 image | 2 text | 3 rich_text | 4 id_configuration | 5 mail | 6 number
    fieldtype: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<ControlPanel slug={self.slug}>"


class IdCounter(Base):
    __tablename__ = "id_counters"

    slug: Mapped[str] = mapped_column(Text, primary_key=True)
    last_number: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
