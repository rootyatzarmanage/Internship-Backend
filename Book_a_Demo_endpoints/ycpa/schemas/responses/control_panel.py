import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ControlPanelImageUploadResponse(BaseModel):
    control_panel_id: uuid.UUID
    slug: str
    image_id: uuid.UUID
    url: str


class ControlPanelResponse(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    name_prefix: str | None = None
    value: str | None = None
    value_json: dict | None = None
    fieldtype: int
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
