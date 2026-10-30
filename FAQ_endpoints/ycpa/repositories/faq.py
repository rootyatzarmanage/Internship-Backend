import logging
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from ycpa.core.exceptions import DatabaseException
from ycpa.models.faq import Faq
from ycpa.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class FaqRepository(BaseRepository[Faq]):

    def __init__(self, session: AsyncSession):
        super().__init__(Faq, session)

    @staticmethod
    def _apply_filters(query, is_active: int | None, search: str | None):
        query = query.where(Faq.deleted_at.is_(None))
        if is_active is not None:
            query = query.where(Faq.is_active == is_active)
        if search:
            term = f"%{search.lower().strip()}%"
            query = query.where(
                or_(
                    func.lower(Faq.question).like(term),
                    func.lower(Faq.answer).like(term),
                )
            )
        return query

    async def list_faqs(
        self,
        is_active: int | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Faq]:
        try:
            query = self._apply_filters(select(Faq), is_active, search)
            query = query.order_by(Faq.display_order.asc(), Faq.created_at.asc()).offset(offset).limit(limit)
            result = await self.session.execute(query)
            return list(result.scalars().all())

        except DBAPIError as e:
            logger.error("DB error listing Faq", extra={"error": str(e)}, exc_info=True)
            raise DatabaseException("Failed to fetch Faq records")

    async def count_faqs(self, is_active: int | None = None, search: str | None = None) -> int:
        try:
            query = self._apply_filters(select(func.count()).select_from(Faq), is_active, search)
            result = await self.session.execute(query)
            return result.scalar() or 0

        except DBAPIError as e:
            logger.error("DB error counting Faq", extra={"error": str(e)}, exc_info=True)
            raise DatabaseException("Failed to count Faq records")

    async def get_by_question(self, question: str, exclude_id: UUID | None = None) -> Faq | None:
        try:
            query = select(Faq).where(
                func.lower(Faq.question) == question.lower().strip(),
                Faq.deleted_at.is_(None),
            )
            if exclude_id:
                query = query.where(Faq.id != exclude_id)
            result = await self.session.execute(query.limit(1))
            return result.scalar_one_or_none()

        except DBAPIError as e:
            logger.error("DB error fetching Faq by question", extra={"error": str(e)}, exc_info=True)
            raise DatabaseException("Failed to fetch Faq")

    async def get_next_display_order(self) -> int:
        try:
            result = await self.session.execute(
                select(func.max(Faq.display_order)).where(Faq.deleted_at.is_(None))
            )
            current_max = result.scalar()
            return 1 if current_max is None else current_max + 1

        except DBAPIError as e:
            logger.error("DB error fetching Faq display order", extra={"error": str(e)}, exc_info=True)
            raise DatabaseException("Failed to fetch Faq display order")
