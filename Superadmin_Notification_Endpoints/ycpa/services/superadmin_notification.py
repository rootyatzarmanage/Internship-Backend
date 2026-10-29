import logging
import math
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ycpa.core.exceptions import BadRequestException, InternalServerException, NotFoundException
from ycpa.models.notification import Notification, NotificationCategory, NotificationType
from ycpa.models.user import User
from ycpa.repositories.notification import NotificationRepository
from ycpa.schemas.requests.notification import NotificationCreateRequest, NotificationListRequest
from ycpa.schemas.responses.notification import (
    CreateNotificationResponse,
    MarkAllReadResponse,
    NotificationCategoryResponse,
    NotificationListResponse,
    NotificationResponse,
    UnreadCountResponse,
)
from ycpa.services.base import BaseService

logger = logging.getLogger(__name__)


class SuperAdminNotificationService(BaseService):

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.repo = NotificationRepository(session)

    @staticmethod
    def _check_category(category_id: Optional[UUID]) -> None:
        if category_id is not None and not NotificationCategory.is_valid(category_id):
            raise BadRequestException("Invalid notification category")

    async def _get_or_404(self, notification_id: UUID, user: User) -> Notification:
        notification = await self.repo.get_for_user(notification_id, user.id)
        if not notification:
            raise NotFoundException("Notification not found", resource="notification")
        return notification


    def list_categories(self) -> list[NotificationCategoryResponse]:
        return [NotificationCategoryResponse(**c) for c in NotificationCategory.ALL]

    async def list_notifications(self, user: User, req: NotificationListRequest) -> NotificationListResponse:
        self._check_category(req.category_id)
        filters = {"category_id": req.category_id, "is_read": req.is_read, "search": req.search}

        items = await self.repo.list_for_user(
            user.id, **filters, limit=req.per_page, offset=(req.page - 1) * req.per_page,
        )
        total = await self.repo.count_for_user(user.id, **filters)
        unread = await self.repo.unread_counts(user.id)

        return NotificationListResponse(
            items=[NotificationResponse.model_validate(n) for n in items],
            total=total,
            page=req.page,
            per_page=req.per_page,
            total_pages=math.ceil(total / req.per_page),
            unread_count=sum(unread.values()),
        )

    async def unread_count(self, user: User) -> UnreadCountResponse:
        unread = await self.repo.unread_counts(user.id)
        return UnreadCountResponse(
            unread_count=sum(unread.values()),
            by_category={c["key"]: unread.get(c["id"], 0) for c in NotificationCategory.ALL},
        )

    async def mark_read(self, user: User, notification_id: UUID) -> NotificationResponse:
        notification = await self._get_or_404(notification_id, user)
        if not notification.is_read:
            notification = await self.repo.mark_read(notification.id, user.id)
            await self.session.commit()
        return NotificationResponse.model_validate(notification)

    async def mark_all_read(self, user: User, category_id: Optional[UUID] = None) -> MarkAllReadResponse:
        self._check_category(category_id)
        updated = await self.repo.mark_all_read(user.id, category_id)
        await self.session.commit()
        return MarkAllReadResponse(updated=updated)

    async def delete(self, user: User, notification_id: UUID) -> None:
        notification = await self._get_or_404(notification_id, user)
        await self.repo.soft_delete(notification.id, deleted_by=user.id)
        await self.session.commit()

    async def create(self, user: User, req: NotificationCreateRequest) -> CreateNotificationResponse:
        created = await self.notify_super_admins(
            req.notification_type,
            req.message,
            platform_id=req.platform_id,
            resource_id=req.resource_id,
            created_by=user.id,
        )
        if created == 0:
            raise InternalServerException("Notification could not be created")
        await self.session.commit()
        return CreateNotificationResponse(created=created)


    async def notify_super_admins(
        self,
        notification_type: str,
        message: str,
        *,
        platform_id: Optional[UUID] = None,
        resource_id: Optional[UUID] = None,
        created_by: Optional[UUID] = None,
    ) -> int:
        """One row per super admin. Never raises and does not commit: call it inside the
        caller's transaction, before the caller's own commit."""
        category_id = NotificationType.CATEGORY.get(notification_type)
        if category_id is None:
            logger.error("Unknown notification type", extra={"type": notification_type})
            return 0
        try:
            async with self.session.begin_nested():
                admin_ids = await self.repo.get_super_admin_ids()
                if not admin_ids:
                    return 0
                await self.repo.bulk_create([
                    Notification(
                        notification_type=notification_type,
                        category_id=category_id,
                        platform_id=platform_id,
                        message=message,
                        user_id=admin_id,
                        created_by=created_by,
                        resource_id=resource_id,
                        is_read=0,
                    )
                    for admin_id in admin_ids
                ])
            return len(admin_ids)
        except Exception:
            logger.exception("Super admin notification failed", extra={"type": notification_type})
            return 0
