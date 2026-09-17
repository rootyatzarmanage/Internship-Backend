import uuid
import enum 
from datetime import datetime,timezone
from sqlalchemy import String, DateTime,ForeignKey
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped,mapped_column
from backend.core.database.base import Base

def utc_now():
    return datetime.now(timezone.utc)

class FileCategory(str,enum.Enum):
    wip = "wip",
    shared = "shared"
    published = "published"
    archived = "archived"

class File(Base):
    __tablename__ = "files"

    id : Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    name : Mapped[str] = mapped_column(
        String[255],
        nullable= False
    )
    category : Mapped[FileCategory] = mapped_column(
        SAEnum(
            FileCategory,
            name = "file_category"
        ),
        nullable=False
    )
    type : Mapped[str] = mapped_column(
        String[50],
        nullable=False
    )
    user_id : Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable= False,
        index = True
    )
    object_key : Mapped[str] = mapped_column(
        String[500],
        nullable=False,
        unique=True
    )
    created_at : Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False
    )
    updated_at : Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False
    )
    deleted_at : Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )