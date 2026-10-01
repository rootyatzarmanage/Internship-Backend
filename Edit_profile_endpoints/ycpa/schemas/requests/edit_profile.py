import re

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)


class EditProfileRequest(BaseModel):

    model_config = ConfigDict(extra="forbid")

    first_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    last_name: str | None = Field(
        default=None,
        max_length=155,
    )

    email: EmailStr | None = Field(
        default=None,
        max_length=255,
    )

    country_code: str | None = Field(
        default=None,
        max_length=5,
    )

    phone: str | None = Field(
        default=None,
        max_length=15,
    )

    country: str | None = Field(
        default=None,
        max_length=100,
    )

    state: str | None = Field(
        default=None,
        max_length=100,
    )

    district: str | None = Field(
        default=None,
        max_length=100,
    )

    pincode: str | None = Field(
        default=None,
        max_length=10,
    )
    delete: int | None = Field(
        default=None,
        ge=0,
        le=1
    )

    @field_validator("*", mode="before")
    @classmethod
    def strip_fields(cls, value):

        if isinstance(value, str):
            return " ".join(value.strip().split())

        return value

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value):

        if isinstance(value, str):
            return value.strip().lower()

        return value

    @field_validator("country_code", mode="before")
    @classmethod
    def validate_country_code(cls, value):

        if value is None:
            return value

        value = str(value).strip()

        if value.isdigit():
            value = f"+{value}"

        if not re.fullmatch(r"\+\d{1,4}", value):
            raise ValueError("Invalid country code")

        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value):

        if value is not None and not re.fullmatch(
            r"\d{7,15}",
            value,
        ):
            raise ValueError("Invalid mobile number")

        return value

    @field_validator("pincode")
    @classmethod
    def validate_pincode(cls, value):

        if value is not None and not re.fullmatch(
            r"\d{4,10}",
            value,
        ):
            raise ValueError("Invalid pincode format")

        return value