from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ContactSubmitResponse(BaseModel):
    contact_id: str | None = None
    model_config = {"from_attributes": True}


class ContactResponse(BaseModel):
    id: UUID
    contact_id: str | None = None
    first_name: str
    last_name: str | None = None
    email: str
    phone_country_code: str | None = None
    phone: str | None = None
    interested_in: str | None = None
    message: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ContactListResponse(BaseModel):
    items: list[ContactResponse]
    total: int
    page: int
    per_page: int