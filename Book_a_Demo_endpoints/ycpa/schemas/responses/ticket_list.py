from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class RequesterResponse(BaseModel):
    id: UUID
    full_name: str
    email: str
    avatar_url: str | None = None
    model_config = {"from_attributes": True}


class TicketListItem(BaseModel):
    id: UUID
    ticket_no: int
    requested_by: RequesterResponse
    category: str
    subject: str
    status: str
    created_at: datetime


class TicketStatsResponse(BaseModel):
    total: int
    pending: int
    solved: int


class TicketListResponse(BaseModel):
    items: list[TicketListItem]
    total: int
    page: int
    per_page: int
    pages: int
