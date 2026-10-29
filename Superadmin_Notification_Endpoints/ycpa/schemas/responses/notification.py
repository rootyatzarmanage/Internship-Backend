from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, computed_field

from ycpa.models.notification import NotificationCategory


class NotificationCategoryResponse(BaseModel):
    id: UUID
    key: str
    name: str


class NotificationResponse(BaseModel):
    id: UUID
    notification_type: str
    category_id: UUID
    platform_id: UUID | None = None
    message: str
    user_id: UUID
    created_by: UUID | None = None
    resource_id: UUID | None = None
    is_read: bool
    read_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @computed_field
    @property
    def category_name(self) -> str | None:
        return NotificationCategory.name_of(self.category_id)


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    total: int
    page: int
    per_page: int
    total_pages: int
    unread_count: int


class UnreadCountResponse(BaseModel):
    unread_count: int
    by_category: dict[str, int]


class MarkAllReadResponse(BaseModel):
    updated: int


class CreateNotificationResponse(BaseModel):
    created: int
