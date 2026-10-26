from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ycpa.models.tickets import Ticket, TicketAttachment, TicketReply
from ycpa.repositories.base import BaseRepository


class TicketReplyRepository(BaseRepository[Ticket]):
    """get_by_id() (base) returns the ticket with user, projects, attachments, replies(+author, +attachments)."""

    def __init__(self, session: AsyncSession):
        super().__init__(Ticket, session)

    async def neighbours(self, t: Ticket) -> tuple[int, int, UUID | None, UUID | None]:
        live = Ticket.deleted_at.is_(None)
        total = (await self.session.execute(select(func.count(Ticket.id)).where(live))).scalar() or 0
        newer = (await self.session.execute(select(func.count(Ticket.id)).where(live, Ticket.created_at > t.created_at))).scalar() or 0
        prev_id = (await self.session.execute(
            select(Ticket.id).where(live, Ticket.created_at > t.created_at).order_by(Ticket.created_at.asc()).limit(1))).scalar()
        next_id = (await self.session.execute(
            select(Ticket.id).where(live, Ticket.created_at < t.created_at).order_by(Ticket.created_at.desc()).limit(1))).scalar()
        return newer + 1, total, prev_id, next_id

    async def add_reply(self, reply: TicketReply, attachments: list[TicketAttachment]) -> TicketReply:
        self.session.add(reply)
        await self.session.flush()  # reply row must exist before attachments reference it
        self.session.add_all(attachments)
        await self.session.flush()
        return reply
