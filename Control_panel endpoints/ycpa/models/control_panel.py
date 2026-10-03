import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime,Integer,Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ycpa.core.database.base import Base


def utcnow():
    return datetime.now(timezone.utc)


class ControlPanel(Base):

    __tablename__ = "ControlPanel"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text,nullable=False)
    name_prefix: Mapped[str | None] = mapped_column(Text,nullable=True)
    fieldtype: Mapped[int] = mapped_column(Integer,nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=utcnow,nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=utcnow,onupdate=utcnow,nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True),nullable=True)

    def __repr__(self):
        return f"<ControlPanel id={self.id} name={self.name}>"