import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from ycpa.core.database.base import Base


def utcnow():
    return datetime.now(timezone.utc)


class IfcImport(Base):
    __tablename__ = "ifc_imports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cde_file_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cde_files.id"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(Text, default="pending", nullable=False)
    celery_task_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    progress_percent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    current_step: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    glb_s3_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    thumbnail_s3_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    ifc_schema_version: Mapped[str | None] = mapped_column(Text, nullable=True)
    element_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    discipline: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    def __repr__(self):
        return f"<IfcImport id={self.id} status={self.status}>"


class IfcElement(Base):
    __tablename__ = "ifc_elements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    import_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ifc_imports.id"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    global_id: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    ifc_type: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    element_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    discipline: Mapped[str | None] = mapped_column(Text, nullable=True)
    storey_global_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    storey_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    building_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    property_sets: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    quantity_sets: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    bbox_min_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    bbox_min_y: Mapped[float | None] = mapped_column(Float, nullable=True)
    bbox_min_z: Mapped[float | None] = mapped_column(Float, nullable=True)
    bbox_max_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    bbox_max_y: Mapped[float | None] = mapped_column(Float, nullable=True)
    bbox_max_z: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    def __repr__(self):
        return f"<IfcElement id={self.id} global_id={self.global_id} ifc_type={self.ifc_type}>"