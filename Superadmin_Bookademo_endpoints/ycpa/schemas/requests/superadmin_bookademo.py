from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from ycpa.core.exceptions import ValidationException

BookDemoView = Literal["all", "upcoming", "cancelled"]
BookDemoStatus = Literal["new", "cancelled"]
SortOrder = Literal["asc", "desc"]

MAX_OVERVIEW_DAYS = 92


def _check_range(start_date: date | None, end_date: date | None) -> None:
    if start_date and end_date and start_date > end_date:
        raise ValidationException(
            "End date must be on or after start date",
            details={"start_date": str(start_date), "end_date": str(end_date)},
        )


class SuperadminBookDemoOverviewQuery(BaseModel):
    start_date: date | None = None
    end_date: date | None = None

    @model_validator(mode="after")
    def validate_date_range(self) -> "SuperadminBookDemoOverviewQuery":
        _check_range(self.start_date, self.end_date)
        if self.start_date and self.end_date:
            if (self.end_date - self.start_date).days >= MAX_OVERVIEW_DAYS:
                raise ValidationException(f"Date range cannot exceed {MAX_OVERVIEW_DAYS} days")
        return self


class SuperadminBookDemoCalendarQuery(BaseModel):
    year: int | None = Field(None, ge=2020, le=2100)
    month: int | None = Field(None, ge=1, le=12)


class SuperadminBookDemoSlotsQuery(BaseModel):
    slot_date: date


class SuperadminBookDemoListQuery(BaseModel):
    view: BookDemoView = "all"
    search: str | None = Field(None, max_length=100)
    start_date: date | None = None
    end_date: date | None = None
    country: str | None = Field(None, max_length=100)
    status: BookDemoStatus | None = None
    invite: int | None = Field(None, ge=0, le=1)
    order: SortOrder = "asc"
    page: int = Field(1, ge=1)
    per_page: int = Field(6, ge=1, le=100)

    @field_validator("search", "country", mode="after")
    @classmethod
    def strip_filters(cls, value: str | None) -> str | None:
        return value.strip() or None if value is not None else None

    @model_validator(mode="after")
    def validate_date_range(self) -> "SuperadminBookDemoListQuery":
        _check_range(self.start_date, self.end_date)
        return self
