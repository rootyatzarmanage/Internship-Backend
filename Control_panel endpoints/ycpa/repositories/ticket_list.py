from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import noload

from ycpa.models.tickets import Ticket
from ycpa.models.user import User
from ycpa.repositories.base import BaseRepository


class TicketListRepository(BaseRepository[Ticket]):
    def __init__(self, session: AsyncSession):
        super().__init__(Ticket, session)

    async def stats(self) -> tuple[int, int]:
        q = select(func.count(Ticket.id), func.count(Ticket.id).filter(Ticket.status == "solved")).where(Ticket.deleted_at.is_(None))
        total, solved = (await self.session.execute(q)).one()
        return total, solved

    async def paginate(self, status: str, search: str | None, category: str | None,
                       sort_by: str, order: str, page: int, per_page: int) -> tuple[list[Ticket], int]:
        conds = [Ticket.deleted_at.is_(None)]
        if status == "solved":
            conds.append(Ticket.status == "solved")
        elif status == "pending":
            conds.append(Ticket.status != "solved")
        if category:
            conds.append(Ticket.category == category)
        if search:
            like = f"%{search.strip().lstrip('#')}%"
            conds.append(or_(
                Ticket.subject.ilike(like), cast(Ticket.ticket_no, String).ilike(like),
                User.email.ilike(like), User.full_name.ilike(like),
            ))

        total = (await self.session.execute(
            select(func.count(Ticket.id)).select_from(Ticket).join(User, User.id == Ticket.user_id).where(*conds)
        )).scalar() or 0

        col = User.full_name if sort_by == "requested_by" else Ticket.created_at
        stmt = (
            select(Ticket).join(User, User.id == Ticket.user_id).where(*conds)
            .options(noload(Ticket.projects), noload(Ticket.attachments), noload(Ticket.replies))
            .order_by(col.asc() if order == "asc" else col.desc(), Ticket.id)
            .offset((page - 1) * per_page).limit(per_page)
        )
        return list((await self.session.execute(stmt)).scalars().all()), total
