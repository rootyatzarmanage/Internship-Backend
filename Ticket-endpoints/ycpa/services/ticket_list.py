import math

from sqlalchemy.ext.asyncio import AsyncSession

from ycpa.models.user import User
from ycpa.repositories.ticket_list import TicketListRepository
from ycpa.schemas.requests.ticket_list import TicketListQuery
from ycpa.schemas.responses.ticket_list import RequesterResponse, TicketListItem, TicketListResponse, TicketStatsResponse
from ycpa.services.base import BaseService


class TicketListService(BaseService):
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.repo = TicketListRepository(session)

    async def stats(self, user: User) -> TicketStatsResponse:
        total, solved = await self.repo.stats(user.id)
        return TicketStatsResponse(total=total, solved=solved, pending=total - solved)

    async def list_tickets(self, user: User, q: TicketListQuery) -> TicketListResponse:
        rows, total = await self.repo.paginate(user.id, q.status, q.search, q.category, q.sort_by, q.order, q.page, q.per_page)
        items = [
            TicketListItem(
                id=t.id, ticket_no=t.ticket_no, requested_by=RequesterResponse.model_validate(t.user),
                category=t.category, subject=t.subject, status=t.status, created_at=t.created_at,
            ) for t in rows
        ]
        return TicketListResponse(items=items, total=total, page=q.page, per_page=q.per_page,
                                  pages=max(1, math.ceil(total / q.per_page)))
