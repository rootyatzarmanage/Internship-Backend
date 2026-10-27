import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ycpa.core.database.base import Base


def utcnow():
    return datetime.now(timezone.utc)


class UserPlatformPermission(Base):
    __tablename__ = "user_platform_permissions"
    __table_args__ = (
        UniqueConstraint("user_id", "permission_slug", name="uq_user_platform_permission"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    permission_slug: Mapped[str] = mapped_column(Text, nullable=False)
    granted_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    def __repr__(self):
        return f"<UserPlatformPermission user_id={self.user_id} slug={self.permission_slug}>"


PLATFORM_PERMISSIONS = [
    {"slug": "home_access", "name": "Home", "description": "Access to Home in sidebar"},
    {"slug": "workspace_access", "name": "Workspace", "description": "Access to Workspace in sidebar"},
    {"slug": "settings_access", "name": "Settings", "description": "Access to Settings in sidebar"},
    {"slug": "help_docs_access", "name": "Help & Docs", "description": "Access to Help & Docs in sidebar"},
]
