import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

class ControlPanelResponse(BaseModel):
    id: uuid.UUID
    name: str
    name_prefix: str | None = None
    fieldtype: int
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)