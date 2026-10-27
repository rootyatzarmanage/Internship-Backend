import json
from typing import Literal
from uuid import UUID

from fastapi import Form
from pydantic import BaseModel, Field

from ycpa.core.exceptions import ValidationException

TicketCategory = Literal["sales", "billing", "support", "trust_and_safety", "migrations", "cancellations"]


class TicketProjectIn(BaseModel):
    project_id: UUID
    product_type: Literal["pim", "aim"]


class CreateTicketRequest(BaseModel):
    category: TicketCategory
    subject: str = Field(min_length=3, max_length=255)
    message: str = Field(min_length=5)
    projects: list[TicketProjectIn] = Field(default_factory=list, max_length=10)


def create_ticket_form(
    category: str = Form(...),
    subject: str = Form(...),
    message: str = Form(...),
    projects: str = Form("[]", description='JSON: [{"project_id":"<uuid>","product_type":"pim"}]'),
) -> CreateTicketRequest:
    try:
        return CreateTicketRequest(category=category, subject=subject.strip(), message=message.strip(), projects=json.loads(projects))
    except ValueError as e: 
        raise ValidationException("Invalid ticket data", details=str(e))
