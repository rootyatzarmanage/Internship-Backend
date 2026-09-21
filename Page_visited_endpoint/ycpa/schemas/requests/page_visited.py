from pydantic import BaseModel, Field, field_validator

class PageVisitedRequest(BaseModel):
    page_name: str = Field(..., min_length=1, max_length=255)
    page_url: str = Field(..., min_length=1, max_length=2048)
    previous_page: str | None = Field(None, min_length=1, max_length=2048)
    duration_seconds: int | None = Field(None, ge=0)

    @field_validator("page_name", "page_url", "previous_page", "duration_seconds", mode="before")
    @classmethod
    def strip_and_validate_fields(cls, v, info):
        if v is None:
            return None
        if isinstance(v, str):
            v = v.strip()
        if info.field_name == "page_name" and not v:
            raise ValueError("Page name cannot be empty")
        if info.field_name in ("page_url", "previous_page") and not v:
            raise ValueError("Page URL cannot be empty")
        return v