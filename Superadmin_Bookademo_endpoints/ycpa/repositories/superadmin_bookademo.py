from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from ycpa.core.exceptions import DatabaseException
from ycpa.models.enquiry import BookDemo
from ycpa.repositories.base import BaseRepository


@dataclass
class BookDemoFilters:
    """Table filters already converted to UTC (the service owns timezone logic)."""
    now: datetime
    view: str = "all"
    search: str | None = None
    start_utc: datetime | None = None   # inclusive
    end_utc: datetime | None = None     # exclusive
    country: str | None = None
    status: str | None = None
    invite: int | None = None


def _active():
    """A booking that occupies a slot (not archived, not cancelled)."""
    return (BookDemo.deleted_at.is_(None), BookDemo.status != "cancelled")


def _conditions(f: BookDemoFilters) -> list:
    conds = [BookDemo.deleted_at.is_(None)]
    if f.view == "upcoming":
        conds += [BookDemo.status != "cancelled", BookDemo.preferred_at >= f.now]
    elif f.view == "cancelled":
        conds.append(BookDemo.status == "cancelled")
    if f.status:
        conds.append(BookDemo.status == f.status)
    if f.invite is not None:
        conds.append(BookDemo.opt == f.invite)
    if f.country:
        conds.append(func.lower(BookDemo.country) == f.country.lower())
    if f.start_utc:
        conds.append(BookDemo.preferred_at >= f.start_utc)
    if f.end_utc:
        conds.append(BookDemo.preferred_at < f.end_utc)
    if f.search:
        term = f.search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        like = f"%{term}%"
        conds.append(or_(
            BookDemo.book_demo_id.ilike(like, escape="\\"),
            BookDemo.name.ilike(like, escape="\\"),
            BookDemo.email.ilike(like, escape="\\"),
            BookDemo.company.ilike(like, escape="\\"),
            BookDemo.country.ilike(like, escape="\\"),
            func.concat(BookDemo.phone_code, " ", BookDemo.phone).ilike(like, escape="\\"),
        ))
    return conds


def _order(order: str):
    col = BookDemo.preferred_at
    return (col.asc() if order == "asc" else col.desc()).nulls_last(), BookDemo.id


class SuperadminBookDemoRepository(BaseRepository[BookDemo]):
    def __init__(self, session: AsyncSession):
        super().__init__(BookDemo, session)

    # ── Overview ─────────────────────────────────────────────────────────────
    async def summary(self, now: datetime) -> dict[str, int]:
        """KPI cards + Calendar Invite Preference, in one query."""
        n = func.count(BookDemo.id)
        stmt = select(
            n,
            n.filter(BookDemo.status == "new"),
            n.filter(BookDemo.status == "cancelled"),
            n.filter(BookDemo.status != "cancelled", BookDemo.preferred_at >= now),
            n.filter(BookDemo.opt == 1),
            n.filter(BookDemo.opt == 0),
        ).where(BookDemo.deleted_at.is_(None))
        try:
            total, new, cancelled, upcoming, requested, not_requested = (await self.session.execute(stmt)).one()
        except DBAPIError as e:
            raise DatabaseException("Failed to load Book a Demo summary") from e
        return {"total": total, "new": new, "cancelled": cancelled, "upcoming": upcoming,
                "requested": requested, "not_requested": not_requested}

    async def status_by_start(self, start: datetime, end: datetime) -> list[tuple[datetime, str]]:
        """(preferred_at, status) for every booking with start <= preferred_at < end — feeds the activity chart."""
        stmt = select(BookDemo.preferred_at, BookDemo.status).where(
            BookDemo.deleted_at.is_(None), BookDemo.preferred_at >= start, BookDemo.preferred_at < end)
        try:
            return [(r[0].astimezone(timezone.utc), r[1]) for r in (await self.session.execute(stmt)).all()]
        except DBAPIError as e:
            raise DatabaseException("Failed to load Book a Demo activity") from e

    # ── Calendar / slots ─────────────────────────────────────────────────────
    async def active_by_start(self, start: datetime, end: datetime) -> dict[datetime, BookDemo]:
        """Slot-occupying bookings keyed by their UTC start, for start <= preferred_at < end."""
        stmt = select(BookDemo).where(*_active(), BookDemo.preferred_at >= start, BookDemo.preferred_at < end)
        try:
            rows = (await self.session.execute(stmt)).scalars().all()
        except DBAPIError as e:
            raise DatabaseException("Failed to load Book a Demo calendar") from e
        return {r.preferred_at.astimezone(timezone.utc): r for r in rows}

    # ── List / export ────────────────────────────────────────────────────────
    async def paginate(self, f: BookDemoFilters, order: str, page: int, per_page: int) -> tuple[list[BookDemo], int]:
        conds = _conditions(f)
        try:
            total = (await self.session.execute(select(func.count(BookDemo.id)).where(*conds))).scalar() or 0
            stmt = select(BookDemo).where(*conds).order_by(*_order(order)).offset((page - 1) * per_page).limit(per_page)
            return list((await self.session.execute(stmt)).scalars().all()), total
        except DBAPIError as e:
            raise DatabaseException("Failed to load Book a Demo list") from e

    async def fetch_all(self, f: BookDemoFilters, order: str, limit: int) -> list[BookDemo]:
        stmt = select(BookDemo).where(*_conditions(f)).order_by(*_order(order)).limit(limit)
        try:
            return list((await self.session.execute(stmt)).scalars().all())
        except DBAPIError as e:
            raise DatabaseException("Failed to export Book a Demo records") from e

    async def countries(self) -> list[str]:
        stmt = (select(BookDemo.country).where(BookDemo.deleted_at.is_(None), BookDemo.country.is_not(None), BookDemo.country != "")
                .distinct().order_by(BookDemo.country))
        try:
            return [r[0] for r in (await self.session.execute(stmt)).all()]
        except DBAPIError as e:
            raise DatabaseException("Failed to load countries") from e
