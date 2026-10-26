import re

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


def make_slug(section: str, name: str) -> str:
    clean = lambda s: re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-")
    return f"{clean(section)}/{clean(name)}"   # "Mail & Settings","Manage Error Mail" -> Mail-Settings/Manage-Error-Mail


class MailValue(BaseModel):
    email: EmailStr | None = None
    cc: list[EmailStr] = Field(default_factory=list)


class ControlPanelCreateRequest(BaseModel):
    section: str | None = None
    slug: str | None = None
    name: str = Field(..., min_length=1)
    fieldtype: int = Field(..., ge=1, le=6)
    name_prefix: str | None = None
    value: str | None = None
    value_json: MailValue | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Name cannot be empty")
        return value

    @model_validator(mode="after")
    def resolve_slug(self):
        if not self.slug:
            if not self.section:
                raise ValueError("Either slug or section is required")
            self.slug = make_slug(self.section, self.name)
        self.slug = self.slug.strip("/")
        return self


class ControlPanelUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    fieldtype: int | None = Field(default=None, ge=1, le=6)
    name_prefix: str | None = None
    value: str | None = None
    value_json: MailValue | None = None


class ControlPanelBulkRequest(BaseModel):
    items: list[ControlPanelCreateRequest] = Field(..., min_length=1)
