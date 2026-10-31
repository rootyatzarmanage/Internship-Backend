import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ycpa.core.database.base import Base


def utcnow():
    return datetime.now(timezone.utc)


class WorkPackage(Base):
    __tablename__ = "work_packages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    owner_type: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    milestone_ids: Mapped[list | None] = mapped_column(
        JSON, default=None, nullable=True
    )
    team_ids: Mapped[list | None] = mapped_column(JSON, default=None, nullable=True)
    member_ids: Mapped[list | None] = mapped_column(JSON, default=None, nullable=True)
    statuses: Mapped[list | None] = mapped_column(JSON, default=None, nullable=True)
    folder_ids: Mapped[list | None] = mapped_column(JSON, default=None, nullable=True)
    tags: Mapped[list | None] = mapped_column(JSON, default=None, nullable=True)
    start_date: Mapped[str | None] = mapped_column(Text, nullable=True)
    end_date: Mapped[str | None] = mapped_column(Text, nullable=True)
    visibility: Mapped[dict | None] = mapped_column(JSON, default=None, nullable=True)
    # Snapshot of the scope grid, captured when the package is created.
    tasks: Mapped[list | None] = mapped_column(JSON, default=None, nullable=True)
    milestones: Mapped[list | None] = mapped_column(JSON, default=None, nullable=True)
    # CDE file id of the IFC model opened in this work package.
    ifc_file_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    def __repr__(self):
        return f"<WorkPackage id={self.id} name={self.name} archived={self.archived}>"
