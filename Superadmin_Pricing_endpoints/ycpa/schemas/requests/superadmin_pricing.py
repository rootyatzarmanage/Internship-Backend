from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


def _clean(v):
    return " ".join(v.strip().split()) if isinstance(v, str) else v


class PricingTabRequest(BaseModel):
    id:     str = Field(..., min_length=1, max_length=40)
    label:  str = Field(..., min_length=1, max_length=100)
    period: str = Field("", max_length=50)
    badge:  str = Field("", max_length=50)

    _strip = field_validator("label", "period", "badge", mode="before")(_clean)


class PricingFeatureRequest(BaseModel):
    id:   str = Field(..., min_length=1, max_length=40)
    text: str = Field(..., min_length=1, max_length=255)

    _strip = field_validator("text", mode="before")(_clean)


class PricingPriceRequest(BaseModel):
    p: str = Field("", max_length=30)
    n: str = Field("", max_length=255)

    _strip = field_validator("p", "n", mode="before")(_clean)


class PricingPlanRequest(BaseModel):
    id:      str = Field(..., min_length=1, max_length=40)
    name:    str = Field(..., min_length=1, max_length=100)
    desc:    str = Field("", max_length=500)
    tier:    str = Field("", max_length=50)
    btn:     str = Field("", max_length=100)
    period:  str = Field("", max_length=50)
    current: bool = False
    popular: bool = False
    prices:  dict[str, PricingPriceRequest] = Field(default_factory=dict)
    feat:    dict[str, bool] = Field(default_factory=dict)

    _strip = field_validator("name", "desc", "tier", "btn", "period", mode="before")(_clean)


class SaveSuperadminPricingRequest(BaseModel):
    cur:      str = Field("₹", min_length=1, max_length=10)
    cur_code: str = Field("INR", pattern=r"^[A-Za-z]{3}$", description="ISO 4217 code of the prices, e.g. INR")
    active:  str | None = Field(None, max_length=40)
    theme:    Literal["dark", "light"] = "dark"
    tabs:     list[PricingTabRequest] = Field(..., min_length=1, max_length=12)
    features: list[PricingFeatureRequest] = Field(default_factory=list, max_length=100)
    plans:    list[PricingPlanRequest] = Field(..., min_length=1, max_length=12)

    _strip = field_validator("cur", mode="before")(_clean)

    @field_validator("cur_code", mode="after")
    @classmethod
    def upper_code(cls, v: str) -> str:
        return v.upper()

    @model_validator(mode="after")
    def check_ids(self):
        for label, items in (("tabs", self.tabs), ("features", self.features), ("plans", self.plans)):
            ids = [i.id for i in items]
            if len(ids) != len(set(ids)):
                raise ValueError(f"Duplicate id found in {label}")
        if self.active not in {t.id for t in self.tabs}:
            self.active = self.tabs[0].id
        return self
