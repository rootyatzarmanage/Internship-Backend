import uuid
from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from ycpa.core.database.base import Base


def utcnow():
    return datetime.now(timezone.utc)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    action: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(Text, nullable=False)
    resource_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    workspace_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    project_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(
        Text, nullable=False, default="success",
        comment="success | failure | error"
    )

    changed_from: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True,
        comment="Previous state before the action"
    )
    changed_to: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True,
        comment="New state after the action"
    )

    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False, index=True
    )

    def __repr__(self):
        return f"<AuditLog id={self.id} action={self.action} status={self.status}>"



class AuditAction:
    USER_REGISTERED       = "USER_REGISTERED"
    USER_LOGIN            = "USER_LOGIN"
    USER_LOGIN_FAILED     = "USER_LOGIN_FAILED"
    USER_LOGOUT           = "USER_LOGOUT"
    USER_PASSWORD_CHANGED = "USER_PASSWORD_CHANGED"
    USER_PROFILE_UPDATED  = "USER_PROFILE_UPDATED"
    USER_DEACTIVATED      = "USER_DEACTIVATED"
    USER_REACTIVATED      = "USER_REACTIVATED"
    USER_DELETED          = "USER_DELETED"
    WORKSPACE_CREATED     = "WORKSPACE_CREATED"
    WORKSPACE_UPDATED     = "WORKSPACE_UPDATED"
    WORKSPACE_DELETED     = "WORKSPACE_DELETED"
    PROJECT_CREATED       = "PROJECT_CREATED"
    PROJECT_UPDATED       = "PROJECT_UPDATED"
    PROJECT_DELETED       = "PROJECT_DELETED"
    PROJECT_ARCHIVED      = "PROJECT_ARCHIVED"
    MEMBER_INVITED        = "MEMBER_INVITED"
    MEMBER_JOINED         = "MEMBER_JOINED"
    MEMBER_REMOVED        = "MEMBER_REMOVED"
    MEMBER_ROLE_CHANGED   = "MEMBER_ROLE_CHANGED"
    FILE_UPLOADED         = "FILE_UPLOADED"
    FILE_DELETED          = "FILE_DELETED"
    FILE_STATUS_CHANGED   = "FILE_STATUS_CHANGED"
    FILE_VERSION_CREATED  = "FILE_VERSION_CREATED"
    SUBSCRIPTION_UPGRADED    = "SUBSCRIPTION_UPGRADED"
    SUBSCRIPTION_DOWNGRADED  = "SUBSCRIPTION_DOWNGRADED"
    SUBSCRIPTION_CANCELLED   = "SUBSCRIPTION_CANCELLED"
    SUBSCRIPTION_OVERRIDE    = "SUBSCRIPTION_OVERRIDE"

