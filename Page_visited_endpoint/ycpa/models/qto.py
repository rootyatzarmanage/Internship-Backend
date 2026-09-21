import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ycpa.core.database.base import Base


def utcnow():
    return datetime.now(timezone.utc)


class QtoCustomItem(Base):

    __tablename__ = "qto_custom_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    owner_type: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(Text, nullable=False)
    family: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    net_surface_area: Mapped[float | None] = mapped_column(Float, nullable=True)
    outer_surface_area: Mapped[float | None] = mapped_column(Float, nullable=True)
    net_volume: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    def __repr__(self):
        return f"<QtoCustomItem id={self.id} family={self.family} name={self.name} count={self.count}>"
