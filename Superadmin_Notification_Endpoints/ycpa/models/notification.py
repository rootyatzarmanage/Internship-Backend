import uuid
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, SmallInteger, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ycpa.core.database.base import Base


def utcnow():
    return datetime.now(timezone.utc)


class NotificationCategory:

    REGISTERED = uuid.UUID("464b29ed-f482-4351-af5d-a50a9eee1dfd")
    WORKSPACE  = uuid.UUID("295caccb-3361-4e6f-8633-7b80c2d7d81c")
    PROJECT    = uuid.UUID("5369ccd9-d6cd-4020-8a0e-fdc677841500")
    PAYMENT    = uuid.UUID("f0d8995d-5d0b-4411-8c0c-87f2ad7ebe4c")

    ALL = [
        {"id": REGISTERED, "key": "registered", "name": "Registered Notification"},
        {"id": WORKSPACE,  "key": "workspace",  "name": "Workspace create Notification"},
        {"id": PROJECT,    "key": "project",    "name": "Project create Notification"},
        {"id": PAYMENT,    "key": "payment",    "name": "Payment Notification"},
    ]

    @classmethod
    def get(cls, category_id: uuid.UUID | None) -> dict | None:
        return next((c for c in cls.ALL if c["id"] == category_id), None)

    @classmethod
    def is_valid(cls, category_id: uuid.UUID | None) -> bool:
        return cls.get(category_id) is not None

    @classmethod
    def name_of(cls, category_id: uuid.UUID | None) -> str | None:
        category = cls.get(category_id)
        return category["name"] if category else None


class NotificationType:
    USER_REGISTERED   = "USER_REGISTERED"
    WORKSPACE_CREATED = "WORKSPACE_CREATED"
    PROJECT_CREATED   = "PROJECT_CREATED"
    PAYMENT_RECEIVED  = "PAYMENT_RECEIVED"
    PAYMENT_FAILED    = "PAYMENT_FAILED"

    CATEGORY = {
        USER_REGISTERED:   NotificationCategory.REGISTERED,
        WORKSPACE_CREATED: NotificationCategory.WORKSPACE,
        PROJECT_CREATED:   NotificationCategory.PROJECT,
        PAYMENT_RECEIVED:  NotificationCategory.PAYMENT,
        PAYMENT_FAILED:    NotificationCategory.PAYMENT,
    }


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        CheckConstraint("is_read IN (0, 1)", name="ck_notifications_is_read"),
        Index("ix_notifications_user_unread", "user_id", "is_read"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # what happened
    notification_type: Mapped[str] = mapped_column(Text, nullable=False)
    category_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    platform_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    # who receives it / who caused it
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    resource_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    # read state (0 = unread, 1 = read)
    is_read: Mapped[int] = mapped_column(SmallInteger, default=0, server_default="0", nullable=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # audit
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    def __repr__(self):
        return f"<Notification id={self.id} type={self.notification_type} user_id={self.user_id}>"
