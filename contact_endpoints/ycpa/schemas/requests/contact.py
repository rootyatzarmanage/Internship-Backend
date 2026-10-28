import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

INTERESTED_IN_OPTIONS = (
    "Workspaces and Projects",
    "IFC Model Viewer",
    "Library and Portfolio",
    "Quantity Take-off and COBie",
    "Resources and Clients",
    "Other",
)

ContactStatus = Literal["new", "in_progress", "resolved", "closed"]


class ContactCreateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    first_name:         str        = Field(..., min_length=1, max_length=100)
    last_name:          str | None = Field(None, max_length=100)
    email:              EmailStr
    phone_country_code: str | None = Field(None, max_length=6)    
    phone:              str | None = Field(None, max_length=20)   
    interested_in:      str | None = Field(None, max_length=100)
    message:            str        = Field(..., min_length=1, max_length=5000)

    @field_validator("last_name", "phone_country_code", "phone", "interested_in", mode="before")
    @classmethod
    def blank_to_none(cls, v):
        if isinstance(v, str) and not v.strip():
            return None
        return v

    @field_validator("phone_country_code", mode="after")
    @classmethod
    def validate_country_code(cls, v):
        if v is not None and not re.fullmatch(r"\+\d{1,4}", v):
            raise ValueError("Country code must look like +91")
        return v

    @field_validator("phone", mode="after")
    @classmethod
    def validate_phone(cls, v):
        if v is None:
            return v
        digits = re.sub(r"[\s\-()]", "", v)
        if not re.fullmatch(r"\d{6,15}", digits):
            raise ValueError("Enter a valid phone number")
        return digits

    @field_validator("interested_in", mode="after")
    @classmethod
    def validate_interested_in(cls, v):
        if v is not None and v not in INTERESTED_IN_OPTIONS:
            raise ValueError(f"interested_in must be one of: {', '.join(INTERESTED_IN_OPTIONS)}")
        return v


class ContactStatusUpdateRequest(BaseModel):
    status: ContactStatus