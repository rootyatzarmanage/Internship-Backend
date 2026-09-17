import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.core.database.base import Base


def utcnow():
    return datetime.now(timezone.utc)


class IfcViewpoint(Base):

    __tablename__ = "ifc_viewpoints"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cde_files.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    guid: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False, default="Untitled")
    data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    snapshot_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    def __repr__(self):
        return f"<IfcViewpoint id={self.id} guid={self.guid} title={self.title}>"


class IfcMeasurement(Base):

    __tablename__ = "ifc_measurements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cde_files.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    def __repr__(self):
        return f"<IfcMeasurement id={self.id} file_id={self.file_id}>"


class IfcMarker(Base):

    __tablename__ = "ifc_markers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cde_files.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    def __repr__(self):
        return f"<IfcMarker id={self.id} file_id={self.file_id}>"


class IfcSelectionGroup(Base):

    __tablename__ = "ifc_selection_groups"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cde_files.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    file_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    color: Mapped[str | None] = mapped_column(Text, nullable=True)
    data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    def __repr__(self):
        return f"<IfcSelectionGroup id={self.id} name={self.name}>"


class IfcMeeting(Base):

    __tablename__ = "ifc_meetings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_type: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    date: Mapped[str] = mapped_column(Text, nullable=False)
    meeting_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    group_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    member_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    custom_members: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="active")
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    def __repr__(self):
        return f"<IfcMeeting id={self.id} name={self.name} code={self.meeting_code}>"


class GsTag(Base):

    __tablename__ = "gs_tags"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cde_files.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    position: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    camera: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    def __repr__(self):
        return f"<GsTag id={self.id} name={self.name}>"
