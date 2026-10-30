from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from ycpa.core.exceptions import ValidationException

MAX_ASSIGNED_MEMBERS = 50


def _clean(value: str | None) -> str | None:
    return value.strip() if value is not None else None


class SuperadminBookDemoTeamQuery(BaseModel):
    search: str | None = Field(None, max_length=100)

    @field_validator("search", mode="after")
    @classmethod
    def strip_search(cls, value: str | None) -> str | None:
        return value.strip() or None if value is not None else None


class SuperadminBookDemoLevelRequest(BaseModel):
    name: str = Field(..., max_length=45)
    description: str | None = Field(None, max_length=160)

    @field_validator("name", "description", mode="after")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        return _clean(value)

    @field_validator("name", mode="after")
    @classmethod
    def require_name(cls, value: str) -> str:
        if not value:
            raise ValidationException("Enter a level name.")
        return value


class SuperadminBookDemoMemberRequest(BaseModel):
    name: str = Field(..., max_length=70)
    email: EmailStr
    role: str = Field(..., max_length=70)
    level_id: UUID
    is_active: bool = True

    @field_validator("name", "role", mode="after")
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValidationException("Enter a name, work email, role and valid level.")
        return value

    @field_validator("email", mode="after")
    @classmethod
    def lower_email(cls, value: str) -> str:
        value = value.strip().lower()
        if len(value) > 120:
            raise ValidationException("Work email cannot exceed 120 characters.")
        return value


class SuperadminBookDemoAssignmentRequest(BaseModel):
    member_ids: list[UUID] = Field(default_factory=list, max_length=MAX_ASSIGNED_MEMBERS)
    primary_id: UUID | None = None
    note: str | None = Field(None, max_length=280)

    @field_validator("note", mode="after")
    @classmethod
    def strip_note(cls, value: str | None) -> str | None:
        return value.strip() or None if value is not None else None

    @model_validator(mode="after")
    def validate_team(self) -> "SuperadminBookDemoAssignmentRequest":
        if len(set(self.member_ids)) != len(self.member_ids):
            raise ValidationException("A team member can only be selected once.")
        if self.member_ids and self.primary_id not in self.member_ids:
            raise ValidationException("Choose one primary contact from the selected team.")
        if not self.member_ids and self.primary_id is not None:
            raise ValidationException("A primary contact needs at least one selected team member.")
        return self
