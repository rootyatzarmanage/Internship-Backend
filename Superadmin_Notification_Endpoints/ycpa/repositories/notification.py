import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from ycpa.core.exceptions import DatabaseException
from ycpa.models.notification import Notification
from ycpa.models.user import User
from ycpa.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class NotificationRepository(BaseRepository[Notification]):

    def __init__(self, session: AsyncSession):
        super().__init__(Notification, session)

    @staticmethod
    def _filters(
        user_id: UUID,
        category_id: Optional[UUID] = None,
        is_read: Optional[int] = None,
        search: Optional[str] = None,
    ) -> list:
        conditions = [Notification.user_id == user_id, Notification.deleted_at.is_(None)]
        if category_id is not None:
            conditions.append(Notification.category_id == category_id)
        if is_read is not None:
            conditions.append(Notification.is_read == is_read)
        if search:
            conditions.append(Notification.message.ilike(f"%{search}%"))
        return conditions

    async def get_super_admin_ids(self) -> list[UUID]:
        try:
            result = await self.session.execute(
                select(User.id).where(
                    User.platform_role == "super_admin",
                    User.is_active.is_(True),
                    User.deleted_at.is_(None),
                )
            )
            return list(result.scalars().all())
        except DBAPIError as e:
            logger.error("DB error fetching super admins", extra={"error": str(e)}, exc_info=True)
            raise DatabaseException("Failed to fetch super admins")

    async def get_for_user(self, notification_id: UUID, user_id: UUID) -> Notification | None:
        try:
            result = await self.session.execute(
                select(Notification).where(
                    Notification.id == notification_id,
                    Notification.user_id == user_id,
                    Notification.deleted_at.is_(None),
                )
            )
            return result.scalar_one_or_none()
        except DBAPIError as e:
            logger.error("DB error fetching notification", extra={"id": str(notification_id), "error": str(e)}, exc_info=True)
            raise DatabaseException("Failed to fetch notification")

    async def list_for_user(
        self,
        user_id: UUID,
        *,
        category_id: Optional[UUID] = None,
        is_read: Optional[int] = None,
        search: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> list[Notification]:
        try:
            result = await self.session.execute(
                select(Notification)
                .where(*self._filters(user_id, category_id, is_read, search))
                .order_by(Notification.created_at.desc(), Notification.id)
                .limit(limit)
                .offset(offset)
            )
            return list(result.scalars().all())
        except DBAPIError as e:
            logger.error("DB error listing notifications", extra={"user_id": str(user_id), "error": str(e)}, exc_info=True)
            raise DatabaseException("Failed to fetch notifications")

    async def count_for_user(
        self,
        user_id: UUID,
        *,
        category_id: Optional[UUID] = None,
        is_read: Optional[int] = None,
        search: Optional[str] = None,
    ) -> int:
        try:
            result = await self.session.execute(
                select(func.count()).select_from(Notification)
                .where(*self._filters(user_id, category_id, is_read, search))
            )
            return result.scalar() or 0
        except DBAPIError as e:
            logger.error("DB error counting notifications", extra={"user_id": str(user_id), "error": str(e)}, exc_info=True)
            raise DatabaseException("Failed to count notifications")

    async def unread_counts(self, user_id: UUID) -> dict[UUID, int]:
        try:
            result = await self.session.execute(
                select(Notification.category_id, func.count())
                .where(*self._filters(user_id, is_read=0))
                .group_by(Notification.category_id)
            )
            return {category_id: count for category_id, count in result.all()}
        except DBAPIError as e:
            logger.error("DB error counting unread notifications", extra={"user_id": str(user_id), "error": str(e)}, exc_info=True)
            raise DatabaseException("Failed to count unread notifications")

    async def mark_read(self, notification_id: UUID, updated_by: UUID) -> Notification | None:
        return await self.update_by_id(notification_id, {
            "is_read":    1,
            "read_at":    datetime.now(timezone.utc),
            "updated_by": updated_by,
        })

    async def mark_all_read(self, user_id: UUID, category_id: Optional[UUID] = None) -> int:
        try:
            now = datetime.now(timezone.utc)
            result = await self.session.execute(
                update(Notification)
                .where(*self._filters(user_id, category_id, is_read=0))
                .values(is_read=1, read_at=now, updated_at=now, updated_by=user_id)
                .execution_options(synchronize_session=False)
            )
            await self.session.flush()
            return result.rowcount or 0
        except DBAPIError as e:
            logger.error("DB error marking notifications read", extra={"user_id": str(user_id), "error": str(e)}, exc_info=True)
            raise DatabaseException("Failed to mark notifications as read")
