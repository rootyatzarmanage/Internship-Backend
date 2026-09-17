import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.core.database.base import Base


def utcnow():
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)



class CdeFolder(TimestampMixin, Base):

    __tablename__ = "cde_folders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_type: Mapped[str] = mapped_column(Text, nullable=False)          # pim | aim
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)  # project_id
    name: Mapped[str] = mapped_column(Text, nullable=False)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cde_folders.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        Text, default="wip", nullable=False,
    )
    discipline_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pim_scope_disciplines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    def __repr__(self):
        return f"<CdeFolder id={self.id} name={self.name} status={self.status}>"



class CdeFile(TimestampMixin, Base):

    __tablename__ = "cde_files"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_type: Mapped[str] = mapped_column(Text, nullable=False)          # pim | aim
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)  # project_id
    uploaded_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    folder_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cde_folders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    filename: Mapped[str] = mapped_column(Text, nullable=False)
   
    original_filename: Mapped[str] = mapped_column(Text, nullable=False)
    s3_key: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    mime_type: Mapped[str] = mapped_column(Text, nullable=False)
    file_extension: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(Text, default="wip", nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    parent_file_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("cde_files.id"), nullable=True)
    discipline: Mapped[str | None] = mapped_column(Text, nullable=True)
    document_number: Mapped[str | None] = mapped_column(Text, nullable=True)
    label: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    shared_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    shared_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    @property
    def parent_id(self) -> uuid.UUID | None:
        return self.parent_file_id

    def __repr__(self):
        return f"<CdeFile id={self.id} filename={self.filename} status={self.status}>"



class CdeFileShare(TimestampMixin, Base):

    __tablename__ = "cde_file_shares"

    __table_args__ = (
        UniqueConstraint("file_id", "shared_with", name="uq_cde_file_shares_file_user"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cde_files.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    shared_with: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    shared_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    can_edit: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    token: Mapped[str] = mapped_column(Text, unique=True, nullable=False, index=True)
    status: Mapped[str] = mapped_column(Text, default="pending", nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    shared_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    def __repr__(self):
        return f"<CdeFileShare file_id={self.file_id} shared_with={self.shared_with} status={self.status}>"



class CdePendingFileShare(Base):

    __tablename__ = "cde_pending_file_shares"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cde_files.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    email: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    can_edit: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    shared_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    shared_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    attached_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    attached_to: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    def __repr__(self):
        return f"<CdePendingFileShare file_id={self.file_id} email={self.email}>"



class CdeFolderShare(TimestampMixin, Base):

    __tablename__ = "cde_folder_shares"

    __table_args__ = (
        UniqueConstraint("folder_id", "shared_with", name="uq_cde_folder_shares_folder_user"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    folder_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cde_folders.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    shared_with: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    shared_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    can_edit: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    token: Mapped[str] = mapped_column(Text, unique=True, nullable=False, index=True)
    status: Mapped[str] = mapped_column(Text, default="pending", nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    shared_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    def __repr__(self):
        return f"<CdeFolderShare folder_id={self.folder_id} shared_with={self.shared_with} status={self.status}>"



class CdePendingFolderShare(Base):

    __tablename__ = "cde_pending_folder_shares"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    folder_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cde_folders.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    email: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    can_edit: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    shared_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    shared_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    attached_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    attached_to: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    def __repr__(self):
        return f"<CdePendingFolderShare folder_id={self.folder_id} email={self.email}>"


class CdeGroup(TimestampMixin, Base):

    __tablename__ = "cde_groups"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_type: Mapped[str] = mapped_column(Text, nullable=False)          # pim | aim
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)  # project_id
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_ids: Mapped[list] = mapped_column(JSON, default=list, nullable=False)  # list of CDE file UUIDs
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    def __repr__(self):
        return f"<CdeGroup id={self.id} name={self.name}>"

    class CdeNamingCode(TimestampMixin, Base):
        """Master lookup table for each segment of the ISO19650-style document number
        e.g. category='discipline', code='S', label='Structural Engineering'"""

        __tablename__ = "cde_naming_codes"

        __table_args__ = (
            UniqueConstraint("owner_id", "category", "code", name="uq_cde_naming_code"),
        )

        id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)  # project_id
        category: Mapped[str] = mapped_column(Text, nullable=False, index=True)
        # category values: functional_breakdown | spatial_breakdown | form |
        #                  discipline | number | status_code | revision
        code: Mapped[str] = mapped_column(Text, nullable=False)  # "ST", "ZZ", "M3", "S", "0401", "S1", "P29"
        label: Mapped[str] = mapped_column(Text, nullable=False)  # "Structural", "All Levels/Locations"
        order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
        deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
        deleted_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

        def __repr__(self):
            return f"<CdeNamingCode {self.category}:{self.code}>"