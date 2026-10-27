from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ycpa.models.enquiry import BookDemo
from ycpa.repositories.base import BaseRepository

_LOCK_NAMESPACE = 0x44454D4F  # "DEMO" - keeps our advisory locks apart from any others


def _active(*conds):
    return (BookDemo.deleted_at.is_(None), BookDemo.status != "cancelled", *conds)


class BookDemoRepository(BaseRepository[BookDemo]):
    def __init__(self, session: AsyncSession):
        super().__init__(BookDemo, session)

    async def count_by_slot(self, start: datetime, end: datetime) -> dict[datetime, int]:
        """Active bookings per slot start for start <= preferred_at < end."""
        stmt = (
            select(BookDemo.preferred_at, func.count(BookDemo.id))
            .where(*_active(BookDemo.preferred_at >= start, BookDemo.preferred_at < end))
            .group_by(BookDemo.preferred_at)
        )
        return {row[0].astimezone(timezone.utc): row[1] for row in (await self.session.execute(stmt)).all()}

    async def count_slot(self, starts_at: datetime) -> int:
        stmt = select(func.count(BookDemo.id)).where(*_active(BookDemo.preferred_at == starts_at))
        return (await self.session.execute(stmt)).scalar() or 0

    async def email_booked_slot(self, email: str, starts_at: datetime) -> bool:
        stmt = select(BookDemo.id).where(*_active(BookDemo.preferred_at == starts_at, func.lower(BookDemo.email) == email.lower())).limit(1)
        return (await self.session.execute(stmt)).first() is not None

    async def lock_slot(self, starts_at: datetime) -> None:
        """Serialise concurrent bookings of the same slot until this transaction ends."""
        key = (_LOCK_NAMESPACE << 32) | int(starts_at.timestamp())
        await self.session.execute(select(func.pg_advisory_xact_lock(key)))
