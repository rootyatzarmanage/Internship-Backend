from pydantic import BaseModel, Field


class OverviewQuery(BaseModel):
    months: int = Field(6, ge=1, le=12)          
    attention_limit: int = Field(6, ge=1, le=20)  
