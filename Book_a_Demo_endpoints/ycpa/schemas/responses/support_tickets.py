from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, field_validator


class AttachmentResponse(BaseModel):
    id: UUID
    reply_id: UUID | None = None
    file_name: str
    file_url: str
    content_type: str | None = None
    size_bytes: int
    model_config = {"from_attributes": True}


class ProjectCardResponse(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    thumbnail_url: str | None = None
    product_type: str  
    workspace_id: UUID
    workspace_name: str | None = None
    created_at: datetime


class TicketProjectResponse(BaseModel):
    project_id: UUID
    product_type: str
    project_name: str
    workspace_name: str | None = None
    thumbnail_url: str | None = None
    model_config = {"from_attributes": True}


class TicketResponse(BaseModel):
    id: UUID
    ticket_no: int
    category: str
    subject: str
    message: str
    status: str
    projects: list[TicketProjectResponse] = []
    attachments: list[AttachmentResponse] = []
    created_at: datetime
    model_config = {"from_attributes": True}

    @field_validator("attachments", mode="before")
    @classmethod
    def _ticket_files_only(cls, v):
        return [a for a in v if getattr(a, "reply_id", None) is None]


class MyTicketsResponse(BaseModel):
    items: list[TicketResponse]
    total: int
    page: int
    per_page: int
