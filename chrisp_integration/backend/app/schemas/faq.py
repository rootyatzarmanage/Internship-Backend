from pydantic import BaseModel, Field
from typing import Optional


class FAQCreate(BaseModel):
    question: str = Field(min_length=3, max_length=500)
    answer: str = Field(min_length=1, max_length=5000)
    category: str = "General"


class FAQResponse(FAQCreate):
    id: int
    is_active: bool = True


class FAQUpdate(BaseModel):
    question: Optional[str] = None
    answer: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None


class FAQQuery(BaseModel):
    question: str = Field(min_length=2, max_length=500)


class FAQAnswerResponse(BaseModel):
    matched: bool
    question: Optional[str] = None
    answer: Optional[str] = None
    message: str