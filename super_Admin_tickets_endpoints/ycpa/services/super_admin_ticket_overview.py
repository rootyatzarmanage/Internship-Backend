import logging
from calendar import month_abbr
from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from ycpa.models.ticket_support import CLOSED, ESCALATION, NEEDS_SA, ON_GOING, OPEN, RESOLVED
from ycpa.repositories.super_admin_ticket_overview import SuperAdminTicketOverviewRepository
from ycpa.repositories.super_admin_ticket_settings import SuperAdminTicketSettingsRepository
from ycpa.schemas.requests.super_admin_ticket_overview import OverviewQuery
from ycpa.schemas.responses.super_admin_ticket_overview import (
    AttentionItem,
    LevelSeries,
    OverviewStats,
    ResolvedByLevel,
    StatusSlice,
    TicketOverviewResponse,
)
from ycpa.services.base import BaseService
from ycpa.services.super_admin_ticket_list import STATUS_LABEL, now_utc, sla_info

logger = logging.getLogger(__name__)
STATUS_ORDER = (OPEN, ON_GOING, ESCALATION, NEEDS_SA, RESOLVED, CLOSED)


class SuperAdminTicketOverviewService(BaseService):
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.repo = SuperAdminTicketOverviewRepository(session)
        self.cfg = SuperAdminTicketSettingsRepository(session)

    async def get_overview(self, params: OverviewQuery) -> TicketOverviewResponse:
        now = now_utc()
        counts = await self.repo.status_counts()
        total = sum(counts.values())
        done = counts.get(RESOLVED, 0) + counts.get(CLOSED, 0)
        escalated = counts.get(ESCALATION, 0) + counts.get(NEEDS_SA, 0)
        stats = OverviewStats(
            total=total,
            today=await self.repo.created_since(now - timedelta(days=1)),
            awaiting_assignment=counts.get(OPEN, 0),
            escalation_queue=escalated,
            resolved_closed=done,
            resolution_rate=(done * 100 + total // 2) // total if total else 0,
            sla_breached=await self.repo.breached_count(now),
            nav_count=counts.get(OPEN, 0) + escalated,
        )
        attention = []
        for row in await self.repo.needs_attention(now, params.attention_limit):
            text, state = sla_info(row.status, row.due_at, now)
            attention.append(AttentionItem(
                id=row.id, ticket_id=row.ticket_id, subject=row.subject,
                status=row.status, status_label=STATUS_LABEL[row.status],
                due_at=row.due_at, sla_text=text, sla_state=state,
            ))
        return TicketOverviewResponse(
            stats=stats,
            status_breakdown=[
                StatusSlice(status=status, label=STATUS_LABEL[status], count=counts.get(status, 0))
                for status in STATUS_ORDER
            ],
            resolved_by_level=await self._resolved_by_level(params.months, now),
            needs_attention=attention,
        )

    async def _resolved_by_level(self, months: int, now) -> ResolvedByLevel:
        first = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        keys = []
        year, month = first.year, first.month
        for _ in range(months):
            keys.append((year, month))
            year, month = (year - 1, 12) if month == 1 else (year, month - 1)
        keys.reverse()
        since = first.replace(year=keys[0][0], month=keys[0][1])
        grid = {}
        for month, level, count in await self.repo.resolved_by_level(since):
            grid[(level, (month.year, month.month))] = count
        levels = await self.cfg.levels()
        series = [(level.id, f"Level {level.id}") for level, _ in levels] + [(0, "Super Admin")]
        return ResolvedByLevel(
            months=[month_abbr[month] for _, month in keys],
            series=[
                LevelSeries(
                    level_id=level_id, label=label,
                    counts=[grid.get((level_id, key), 0) for key in keys],
                )
                for level_id, label in series
            ],
        )
