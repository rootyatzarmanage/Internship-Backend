import uuid
from datetime import datetime, timezone
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from ycpa.core.exceptions import ForbiddenException, NotFoundException
from ycpa.models.tickets import Ticket, TicketReply
from ycpa.models.user import User
from ycpa.repositories.ticket_reply import TicketReplyRepository
from ycpa.schemas.requests.ticket_reply import CreateReplyRequest, UpdateTicketStatusRequest
from ycpa.schemas.responses.support_tickets import AttachmentResponse, TicketProjectResponse
from ycpa.schemas.responses.ticket_reply import MessageResponse, TicketDetailsResponse, TicketThreadResponse
from ycpa.services.base import BaseService
from ycpa.services.support_tickets import save_attachments

STAFF_ROLES = ("super_admin", "staff")


def _msg(id_, author: User, role: str, text: str, at: datetime, files) -> MessageResponse:
    return MessageResponse(
        id=id_, author_id=author.id, author_name=author.full_name, author_email=author.email,
        author_avatar=author.avatar_url, author_role=role, message=text, created_at=at,
        attachments=[AttachmentResponse.model_validate(a) for a in files],
    )


class TicketReplyService(BaseService):
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.repo = TicketReplyRepository(session)

    async def _get(self, user: User, ticket_id: UUID) -> Ticket:
        t = await self.repo.get_by_id(ticket_id)
        if not t:
            raise NotFoundException("Ticket not found", resource="ticket")
        if t.user_id != user.id and user.platform_role not in STAFF_ROLES:
            raise ForbiddenException("You do not have access to this ticket")
        return t

    async def get_thread(self, user: User, ticket_id: UUID) -> TicketThreadResponse:
        t = await self._get(user, ticket_id)
        position, total, prev_id, next_id = await self.repo.neighbours(t)
        messages = [_msg(t.id, t.user, "customer", t.message, t.created_at, [a for a in t.attachments if a.reply_id is None])]
        messages += [_msg(r.id, r.author, r.author_role, r.message, r.created_at, r.attachments) for r in t.replies]
        return TicketThreadResponse(
            ticket=TicketDetailsResponse(
                id=t.id, ticket_no=t.ticket_no, customer=t.user.full_name, email=t.user.email,
                category=t.category, status=t.status, created_at=t.created_at,
            ),
            subject=t.subject,
            projects=[TicketProjectResponse.model_validate(p) for p in t.projects],
            messages=messages, position=position, total=total, prev_id=prev_id, next_id=next_id,
        )

    async def add_reply(self, user: User, ticket_id: UUID, data: CreateReplyRequest, files: list[UploadFile]) -> MessageResponse:
        t = await self._get(user, ticket_id)
        is_staff = user.platform_role in STAFF_ROLES

        reply = TicketReply(id=uuid.uuid4(), ticket_id=t.id, author_id=user.id,
                            author_role="support" if is_staff else "customer", message=data.message,
                            created_at=datetime.now(timezone.utc))
        attachments = await save_attachments(t.id, files, user.id, reply_id=reply.id)
        await self.repo.add_reply(reply, attachments)

        new_status = t.status
        if is_staff:
            new_status = data.status or ("in_progress" if t.status == "pending" else t.status)
        elif t.status in ("solved", "on_hold"):
            new_status = "pending"  # customer replied -> reopen
        if new_status != t.status:
            await self.repo.update_by_id(t.id, {"status": new_status, "updated_by": user.id})

        await self.log_audit("ticket.reply", "ticket", str(t.id), user.id, payload={"status": new_status})
        await self.session.commit()
        return _msg(reply.id, user, reply.author_role, reply.message, reply.created_at, attachments)

    async def update_status(self, user: User, ticket_id: UUID, data: UpdateTicketStatusRequest) -> TicketDetailsResponse:
        if user.platform_role not in STAFF_ROLES:
            raise ForbiddenException("Only support staff can change ticket status")
        t = await self._get(user, ticket_id)
        old = t.status
        await self.repo.update_by_id(t.id, {"status": data.status, "updated_by": user.id})
        await self.log_audit("ticket.status", "ticket", str(t.id), user.id, changed_from={"status": old}, changed_to={"status": data.status})
        await self.session.commit()
        return TicketDetailsResponse(id=t.id, ticket_no=t.ticket_no, customer=t.user.full_name, email=t.user.email,
                                     category=t.category, status=data.status, created_at=t.created_at)
