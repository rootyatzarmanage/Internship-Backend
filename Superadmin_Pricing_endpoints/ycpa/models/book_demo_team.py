import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ycpa.core.database.base import Base

LEVEL = "level"
MEMBER = "member"


def utcnow():
    return datetime.now(timezone.utc)


class BookDemoTeam(Base):
    __tablename__ = "book_demo_team"
    __table_args__ = (
        CheckConstraint("kind in ('level', 'member')", name="ck_book_demo_team_kind"),
        CheckConstraint(
            "(kind = 'level' and parent_id is null) or "
            "(kind = 'member' and parent_id is not null and email is not null and role is not null)",
            name="ck_book_demo_team_shape"),
        Index("uq_book_demo_team_level_name", text("lower(name)"), unique=True, postgresql_where=text("kind = 'level'")),
        Index("uq_book_demo_team_member_email", text("lower(email)"), unique=True, postgresql_where=text("kind = 'member'")),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    kind: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)            
    email: Mapped[str | None] = mapped_column(Text, nullable=True)                
    role: Mapped[str | None] = mapped_column(Text, nullable=True)               
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("book_demo_team.id", ondelete="RESTRICT"), nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
