from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, field_validator


class EditProfileResponse(BaseModel):
    user_id: UUID
    first_name: str
    last_name: str
    email: EmailStr
    country_code: str
    phone: str | None = None
    country: str | None = None
    state: str | None = None
    district: str | None = None
    pincode: str | None = None
    delete: int 
    deleted_at: datetime | None = None
    updated_at: datetime

    model_config = {"from_attributes": True}

    @field_validator(
        "first_name",
        "last_name",
        "country_code",
    )
    @classmethod
    def validate_required_strings(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Field cannot be empty")

        return value

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip().lower()
        return value

    @field_validator(
        "phone",
        "country",
        "state",
        "district",
        "pincode",
    )
    @classmethod
    def validate_optional_strings(
        cls,
        value: str | None,
    ) -> str | None:

        if value is not None:
            value = value.strip()

            if not value:
                return None

        return value

    @classmethod
    def from_orm_model(cls, user) -> "EditProfileResponse":
        return cls.model_validate(user)