from typing import Literal

from fastapi import Form
from pydantic import BaseModel, Field, ValidationError

from ycpa.core.exceptions import ValidationException

TicketStatus = Literal["pending", "in_progress", "solved", "on_hold"]


class CreateReplyRequest(BaseModel):
    message: str = Field(min_length=1)
    status: TicketStatus | None = None  # staff only; radio under the reply box


class UpdateTicketStatusRequest(BaseModel):
    status: TicketStatus


def create_reply_form(message: str = Form(...), status: str | None = Form(None)) -> CreateReplyRequest:
    try:
        return CreateReplyRequest(message=message.strip(), status=status or None)
    except ValidationError as e:
        raise ValidationException("Invalid reply", details=str(e))
