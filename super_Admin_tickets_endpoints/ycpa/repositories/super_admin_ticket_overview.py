import logging
from datetime import datetime

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ycpa.models.ticket_support import CLOSED, ESCALATION, NEEDS_SA, OPEN, RESOLVED
from ycpa.models.tickets import Ticket
from ycpa.repositories.base import BaseRepository
from ycpa.repositories.super_admin_ticket_list import DUE, IS_ACTIVE, PRI_RANK, STATUS

logger = logging.getLogger(__name__)


class SuperAdminTicketOverviewRepository(BaseRepository[Ticket]):
    def __init__(self, session: AsyncSession):
        super().__init__(Ticket, session)

    async def status_counts(self) -> dict[str, int]:
        result = await self.session.execute(
            select(STATUS, func.count())
            .where(Ticket.deleted_at.is_(None))
            .group_by(STATUS)
        )
        return {row[0]: row[1] for row in result.all()}

    async def created_since(self, since: datetime) -> int:
        return await self.session.scalar(
            select(func.count())
            .where(Ticket.deleted_at.is_(None), Ticket.created_at >= since)
        ) or 0

    async def breached_count(self, now: datetime) -> int:
        return await self.session.scalar(
            select(func.count()).select_from(Ticket)
            .where(Ticket.deleted_at.is_(None), IS_ACTIVE, DUE < now)
        ) or 0

    async def resolved_by_level(self, since: datetime) -> list[tuple[datetime, int, int]]:
        month = func.date_trunc("month", Ticket.resolved_at)
        result = await self.session.execute(
            select(month, Ticket.resolved_level, func.count())
            .where(
                Ticket.deleted_at.is_(None), Ticket.status.in_([RESOLVED, CLOSED]),
                Ticket.resolved_at >= since, Ticket.resolved_level.is_not(None),
            )
            .group_by(month, Ticket.resolved_level)
        )
        return [(row[0], row[1], row[2]) for row in result.all()]

    async def needs_attention(self, now: datetime, limit: int):
        breached = IS_ACTIVE & (DUE < now)
        rank = case(
            (breached, 0), (STATUS == NEEDS_SA, 1), (STATUS == ESCALATION, 2), else_=3,
        )
        result = await self.session.execute(
            select(
                Ticket.id, Ticket.ticket_id, Ticket.subject,
                STATUS.label("status"), DUE.label("due_at"),
            )
            .where(Ticket.deleted_at.is_(None), STATUS.in_([OPEN, ESCALATION, NEEDS_SA]) | breached)
            .order_by(rank, PRI_RANK.desc(), Ticket.created_at.desc(), Ticket.id)
            .limit(limit)
        )
        return result.all()
