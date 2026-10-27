import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ycpa.core.database.base import Base


def utcnow():
    return datetime.now(timezone.utc)


class SchedulingTask(Base):

    __tablename__ = "scheduling_tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    owner_type: Mapped[str] = mapped_column(Text, nullable=False)
    task_id: Mapped[str] = mapped_column(Text, nullable=False)
    level: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(Text, nullable=False, default="")
    label: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(Text, nullable=False)
    start_date: Mapped[str] = mapped_column(Text, nullable=False)
    end_date: Mapped[str] = mapped_column(Text, nullable=False)
    duration: Mapped[dict | None] = mapped_column(JSON, default=None, nullable=True)
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)
    color: Mapped[str] = mapped_column(Text, nullable=False)
    parent_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    predecessors: Mapped[str | None] = mapped_column(Text, nullable=True, default="")
    predecessors_lag: Mapped[str | None] = mapped_column(Text, nullable=True, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    def __repr__(self):
        return f"<SchedulingTask id={self.id} task_id={self.task_id} label={self.label}>"


class SchedulingTaskElementLink(Base):

    __tablename__ = "scheduling_task_element_links"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    task_id: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    element_global_id: Mapped[str] = mapped_column(Text, nullable=False)
    file_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    def __repr__(self):
        return f"<SchedulingTaskElementLink id={self.id} project_id={self.project_id} task_id={self.task_id} element_global_id={self.element_global_id}>"
