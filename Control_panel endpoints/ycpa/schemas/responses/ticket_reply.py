from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from ycpa.schemas.responses.support_tickets import AttachmentResponse, TicketProjectResponse


class MessageResponse(BaseModel):
    id: UUID
    author_id: UUID
    author_name: str
    author_email: str
    author_avatar: str | None = None
    author_role: str  # customer | support
    message: str
    attachments: list[AttachmentResponse] = []
    created_at: datetime


class TicketDetailsResponse(BaseModel):  # right-hand "Ticket Details" card
    id: UUID
    ticket_no: int
    customer: str
    email: str
    category: str
    status: str
    created_at: datetime


class TicketThreadResponse(BaseModel):
    ticket: TicketDetailsResponse
    subject: str
    projects: list[TicketProjectResponse] = []
    messages: list[MessageResponse]
    position: int  # "4 of 120"
    total: int
    prev_id: UUID | None = None
    next_id: UUID | None = None
