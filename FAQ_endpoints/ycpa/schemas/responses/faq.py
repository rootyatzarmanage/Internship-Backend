from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class FaqPublicResponse(BaseModel):
    id: UUID
    question: str
    answer: str
    display_order: int

    model_config = {"from_attributes": True}


class FaqResponse(BaseModel):
    id: UUID
    question: str
    answer: str
    display_order: int
    is_active: bool
    created_by: UUID | None = None
    updated_by: UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FaqListResponse(BaseModel):
    items: list[FaqResponse]
    total: int
    page: int
    per_page: int
