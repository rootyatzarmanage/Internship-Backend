from pydantic import BaseModel, field_validator


class CreateProjectRequest(BaseModel):
    name: str
    status: int = 1
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Project name cannot be empty")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: int) -> int:
        if v not in (0, 1):
            raise ValueError("Status must be 0 or 1")
        return v


class UpdateProjectRequest(BaseModel):
    name: str
    status: int
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Project name cannot be empty")
        return v
    @field_validator("status")
    @classmethod
    def validate_status(cls, v: int) -> int:
        if v not in (0, 1):
            raise ValueError("Status must be 0 or 1")
        return v