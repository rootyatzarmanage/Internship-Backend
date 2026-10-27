import re
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


def _clean(v):
    return " ".join(v.split()) if isinstance(v, str) else v


class BookDemoRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    phone_code: str = Field(min_length=1, max_length=6, description="e.g. +91")
    phone: str = Field(min_length=4, max_length=20, description="number without the code")
    company: str = Field(min_length=1, max_length=255)
    country: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=2000, description="Anything we should know (optional)")
    opt: int = Field(default=1, description="1 = send calendar invite (default), 0 = do not")
    starts_at: datetime = Field(description="Slot start exactly as returned by GET /book-a-demo/slots")
    timezone: str = Field(min_length=1, max_length=64, description="Visitor IANA timezone, e.g. Asia/Kolkata")

    _clean_text = field_validator("full_name", "company", "country", "phone_code", "phone", "timezone", mode="before")(_clean)

    @field_validator("phone_code")
    @classmethod
    def _code(cls, v: str) -> str:
        v = v if v.startswith("+") else "+" + v
        if not re.fullmatch(r"\+\d{1,4}", v):
            raise ValueError("Enter a valid phone code, e.g. +91")
        return v

    @field_validator("phone")
    @classmethod
    def _phone(cls, v: str) -> str:
        if not re.fullmatch(r"[0-9\s\-]+", v) or not 4 <= len(re.sub(r"\D", "", v)) <= 15:
            raise ValueError("Enter a valid phone number, e.g. 98765 43210")
        return v

    @field_validator("description", mode="before")
    @classmethod
    def _desc(cls, v):
        v = v.strip() if isinstance(v, str) else v
        return v or None

    @field_validator("opt", mode="before")
    @classmethod
    def _opt(cls, v):
        v = int(v) if isinstance(v, (bool, str)) else v
        if v not in (0, 1):
            raise ValueError("opt must be 0 or 1")
        return v

    @field_validator("starts_at")
    @classmethod
    def _aware(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("starts_at must include a timezone offset (e.g. 2026-10-28T04:30:00Z)")
        return v
