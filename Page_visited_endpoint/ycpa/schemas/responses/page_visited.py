import uuid
from datetime import datetime

from pydantic import BaseModel, computed_field

class PageVisitedResponse(BaseModel):
    id: uuid.UUID
    page_name: str
    page_url: str
    previous_page: str | None
    user_id: uuid.UUID | None
    ip_address: str | None
    country_name: str | None
    region: str | None
    city: str | None
    pincode: str | None
    device_type: str | None
    operating_system: str | None
    browser: str | None
    time_zone: str | None
    duration_seconds: int | None
    deleted_at: datetime | None
    deleted_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
    created_by: uuid.UUID | None
    updated_by: uuid.UUID | None
    model_config = {"from_attributes": True}

    @computed_field
    @property
    def is_authenticated(self) -> int:
        return 1 if self.user_id is not None else 0

class PageVisitedFilterResponse(BaseModel):
    items: list[PageVisitedResponse]
    countries: list[str]
    pages: list[str]

class PageVisitedFilterOptionsResponse(BaseModel):
    countries: list[str]
    pages: list[str]