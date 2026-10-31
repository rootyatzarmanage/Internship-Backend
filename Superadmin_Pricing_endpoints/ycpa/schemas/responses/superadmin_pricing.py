from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PricingTabResponse(BaseModel):
    id:     str
    label:  str
    period: str = ""
    badge:  str = ""


class PricingFeatureResponse(BaseModel):
    id:   str
    text: str


class PricingPriceResponse(BaseModel):
    p: str = ""
    n: str = ""


class PricingPlanResponse(BaseModel):
    id:      str
    name:    str
    desc:    str = ""
    tier:    str = ""
    btn:     str = ""
    period:  str = ""
    current: bool = False
    popular: bool = False
    prices:  dict[str, PricingPriceResponse] = {}
    feat:    dict[str, bool] = {}


class SuperadminPricingResponse(BaseModel):
    id:         UUID
    cur:        str = Field(validation_alias="currency")
    cur_code:   str = Field(validation_alias="currency_code")
    active:    str | None = Field(None, validation_alias="active_tab_id")
    theme:      str
    tabs:       list[PricingTabResponse]
    features:   list[PricingFeatureResponse]
    plans:      list[PricingPlanResponse]
    updated_at: datetime
    updated_by: UUID | None = None

    model_config = {"from_attributes": True}


class ConvertedPricingResponse(BaseModel):
    base_currency_code: str
    currency_code:      str
    rate:               float
    rate_date:          str | None = None
    source:             str = "frankfurter"
    plans:              list[PricingPlanResponse]
