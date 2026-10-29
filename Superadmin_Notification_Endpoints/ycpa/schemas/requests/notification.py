from uuid import UUID

from fastapi import Query
from pydantic import BaseModel, Field, field_validator

from ycpa.models.notification import NotificationType


class NotificationListRequest:
    """Query params for GET /super-admin/notifications (used with Depends())."""

    def __init__(
        self,
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=100),
        category_id: UUID | None = Query(None, description="One of GET /super-admin/notifications/categories"),
        is_read: int | None = Query(None, ge=0, le=1, description="0 = unread, 1 = read"),
        search: str | None = Query(None, max_length=100, description="Search inside the message"),
    ):
        self.page = page
        self.per_page = per_page
        self.category_id = category_id
        self.is_read = is_read
        self.search = search.strip() if search else None


class NotificationCreateRequest(BaseModel):
    notification_type: str = Field(..., description="USER_REGISTERED | WORKSPACE_CREATED | PROJECT_CREATED | PAYMENT_RECEIVED | PAYMENT_FAILED")
    message: str = Field(..., min_length=1, max_length=500)
    platform_id: UUID | None = None
    resource_id: UUID | None = None

    @field_validator("notification_type")
    @classmethod
    def check_type(cls, v: str) -> str:
        if v not in NotificationType.CATEGORY:
            raise ValueError(f"Invalid notification_type: {v}")
        return v

    @field_validator("message", mode="after")
    @classmethod
    def clean_message(cls, v: str) -> str:
        return " ".join(v.strip().split())
