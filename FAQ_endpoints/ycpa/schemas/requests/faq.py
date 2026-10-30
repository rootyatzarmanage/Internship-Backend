from pydantic import BaseModel, Field, field_validator


def _clean(v):
    if isinstance(v, str):
        return " ".join(v.strip().split())
    return v


class FaqCreateRequest(BaseModel):
    question:      str  = Field(..., min_length=5, max_length=500)
    answer:        str  = Field(..., min_length=1, max_length=5000)
    display_order: int | None = Field(None, ge=0, description="Leave empty to add at the end")
    is_active:     bool = True

    @field_validator("question", mode="before")
    @classmethod
    def clean_question(cls, v):
        return _clean(v)

    @field_validator("answer", mode="before")
    @classmethod
    def strip_answer(cls, v):
        return v.strip() if isinstance(v, str) else v


class FaqUpdateRequest(BaseModel):
    question:      str  = Field(..., min_length=5, max_length=500)
    answer:        str  = Field(..., min_length=1, max_length=5000)
    display_order: int | None  = Field(None, ge=0, description="Leave empty to keep the current order")
    is_active:     bool | None = Field(None, description="Leave empty to keep the current status")

    @field_validator("question", mode="before")
    @classmethod
    def clean_question(cls, v):
        return _clean(v)

    @field_validator("answer", mode="before")
    @classmethod
    def strip_answer(cls, v):
        return v.strip() if isinstance(v, str) else v
