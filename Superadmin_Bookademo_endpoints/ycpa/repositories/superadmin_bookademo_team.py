from collections import Counter
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from ycpa.core.exceptions import DatabaseException
from ycpa.models.book_demo_team import LEVEL, MEMBER, BookDemoTeam
from ycpa.models.enquiry import BookDemo
from ycpa.repositories.base import BaseRepository


def _live_bookings():
    return (BookDemo.deleted_at.is_(None), BookDemo.status != "cancelled")


class SuperadminBookDemoLevelRepository(BaseRepository[BookDemoTeam]):
    def __init__(self, session: AsyncSession):
        super().__init__(BookDemoTeam, session)

    async def list_all(self) -> list[BookDemoTeam]:
        stmt = select(BookDemoTeam).where(BookDemoTeam.kind == LEVEL).order_by(BookDemoTeam.created_at, BookDemoTeam.id)
        try:
            return list((await self.session.execute(stmt)).scalars().all())
        except DBAPIError as e:
            raise DatabaseException("Failed to load team levels") from e

    async def get_level(self, level_id: UUID) -> BookDemoTeam | None:
        stmt = select(BookDemoTeam).where(BookDemoTeam.id == level_id, BookDemoTeam.kind == LEVEL)
        try:
            return (await self.session.execute(stmt)).scalars().first()
        except DBAPIError as e:
            raise DatabaseException("Failed to load the level") from e

    async def count_levels(self) -> int:
        stmt = select(func.count(BookDemoTeam.id)).where(BookDemoTeam.kind == LEVEL)
        try:
            return (await self.session.execute(stmt)).scalar() or 0
        except DBAPIError as e:
            raise DatabaseException("Failed to count levels") from e

    async def find_by_name(self, name: str, exclude_id: UUID | None = None) -> BookDemoTeam | None:
        stmt = select(BookDemoTeam).where(BookDemoTeam.kind == LEVEL, func.lower(BookDemoTeam.name) == name.lower())
        if exclude_id:
            stmt = stmt.where(BookDemoTeam.id != exclude_id)
        try:
            return (await self.session.execute(stmt)).scalars().first()
        except DBAPIError as e:
            raise DatabaseException("Failed to check the level name") from e

    async def member_count(self, level_id: UUID) -> int:
        stmt = select(func.count(BookDemoTeam.id)).where(BookDemoTeam.kind == MEMBER, BookDemoTeam.parent_id == level_id)
        try:
            return (await self.session.execute(stmt)).scalar() or 0
        except DBAPIError as e:
            raise DatabaseException("Failed to count level members") from e


class SuperadminBookDemoMemberRepository(BaseRepository[BookDemoTeam]):
    def __init__(self, session: AsyncSession):
        super().__init__(BookDemoTeam, session)

    async def list_all(self) -> list[BookDemoTeam]:
        stmt = select(BookDemoTeam).where(BookDemoTeam.kind == MEMBER).order_by(BookDemoTeam.created_at, BookDemoTeam.id)
        try:
            return list((await self.session.execute(stmt)).scalars().all())
        except DBAPIError as e:
            raise DatabaseException("Failed to load team members") from e

    async def get_member(self, member_id: UUID) -> BookDemoTeam | None:
        stmt = select(BookDemoTeam).where(BookDemoTeam.id == member_id, BookDemoTeam.kind == MEMBER)
        try:
            return (await self.session.execute(stmt)).scalars().first()
        except DBAPIError as e:
            raise DatabaseException("Failed to load the team member") from e

    async def get_many(self, ids: list[UUID]) -> list[BookDemoTeam]:
        if not ids:
            return []
        stmt = select(BookDemoTeam).where(BookDemoTeam.kind == MEMBER, BookDemoTeam.id.in_(ids))
        try:
            return list((await self.session.execute(stmt)).scalars().all())
        except DBAPIError as e:
            raise DatabaseException("Failed to load team members") from e

    async def count_members(self) -> int:
        stmt = select(func.count(BookDemoTeam.id)).where(BookDemoTeam.kind == MEMBER)
        try:
            return (await self.session.execute(stmt)).scalar() or 0
        except DBAPIError as e:
            raise DatabaseException("Failed to count team members") from e

    async def find_by_email(self, email: str, exclude_id: UUID | None = None) -> BookDemoTeam | None:
        stmt = select(BookDemoTeam).where(BookDemoTeam.kind == MEMBER, func.lower(BookDemoTeam.email) == email.lower())
        if exclude_id:
            stmt = stmt.where(BookDemoTeam.id != exclude_id)
        try:
            return (await self.session.execute(stmt)).scalars().first()
        except DBAPIError as e:
            raise DatabaseException("Failed to check the member email") from e

    async def workload(self) -> tuple[dict[UUID, int], dict[UUID, int]]:
        """(bookings per member, distinct bookings per level) over non-cancelled bookings."""
        arrays_stmt = select(BookDemo.assigned_member_ids).where(
            *_live_bookings(), func.cardinality(BookDemo.assigned_member_ids) > 0)
        level_stmt = select(BookDemoTeam.id, BookDemoTeam.parent_id).where(BookDemoTeam.kind == MEMBER)
        try:
            arrays = (await self.session.execute(arrays_stmt)).scalars().all()
            level_of = {r[0]: r[1] for r in (await self.session.execute(level_stmt)).all()}
        except DBAPIError as e:
            raise DatabaseException("Failed to load team workload") from e
        by_member: Counter = Counter()
        by_level: Counter = Counter()
        for ids in arrays:
            unique = set(ids)
            by_member.update(unique)
            by_level.update({level_of[i] for i in unique if i in level_of})
        return dict(by_member), dict(by_level)

    async def coverage(self, now: datetime) -> dict[str, int]:
        has_team = func.cardinality(BookDemo.assigned_member_ids) > 0
        n = func.count(BookDemo.id)
        stmt = select(n.filter(has_team), n.filter(~has_team, BookDemo.preferred_at >= now)).where(*_live_bookings())
        try:
            assigned, needs = (await self.session.execute(stmt)).one()
        except DBAPIError as e:
            raise DatabaseException("Failed to load assignment coverage") from e
        return {"assigned": assigned, "needs_assignment": needs}


class SuperadminBookDemoAssignmentRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def lock_booking(self, booking_id: UUID) -> BookDemo | None:
        stmt = select(BookDemo).where(BookDemo.id == booking_id, BookDemo.deleted_at.is_(None)).with_for_update()
        try:
            return (await self.session.execute(stmt)).scalars().first()
        except DBAPIError as e:
            raise DatabaseException("Failed to load the booking") from e

    async def get_booking(self, booking_id: UUID) -> BookDemo | None:
        stmt = select(BookDemo).where(BookDemo.id == booking_id, BookDemo.deleted_at.is_(None))
        try:
            return (await self.session.execute(stmt)).scalars().first()
        except DBAPIError as e:
            raise DatabaseException("Failed to load the booking") from e

    async def members_in_order(self, ids: list[UUID]) -> list[tuple[BookDemoTeam, BookDemoTeam]]:
        if not ids:
            return []
        level = aliased(BookDemoTeam)
        stmt = (select(BookDemoTeam, level)
                .join(level, level.id == BookDemoTeam.parent_id)
                .where(BookDemoTeam.kind == MEMBER, BookDemoTeam.id.in_(ids)))
        try:
            found = {r[0].id: (r[0], r[1]) for r in (await self.session.execute(stmt)).all()}
        except DBAPIError as e:
            raise DatabaseException("Failed to load the assigned team") from e
        return [found[i] for i in ids if i in found]
