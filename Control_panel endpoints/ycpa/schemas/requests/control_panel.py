from pydantic import BaseModel, Field, field_validator

class ControlPanelCreateRequest(BaseModel):
    name : str = Field(...,min_length=1)
    name_prefix : str | None = None
    fieldtype : int = Field(...,ge=1,le=3)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Name cannot be empty")
        return value

class ControlPanelUpdateRequest(BaseModel):
    name : str = Field(default=None, min_length=1)
    name_prefix : str | None = None
    fieldtype : int | None = Field(default=None, ge=1, le=3)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Name cannot be empty")
        return value