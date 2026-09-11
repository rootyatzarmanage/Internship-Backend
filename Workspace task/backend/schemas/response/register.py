from uuid import UUID
from pydantic import BaseModel, ConfigDict, field_validator, EmailStr

class RegisterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id : UUID
    email : EmailStr
    full_name : str
    is_active : int

    @field_validator("email")
    @classmethod
    def email_format(cls, v: EmailStr) -> EmailStr:
        v = v.strip().lower()
        if not v:
            raise ValueError("Email can't be empty")
        return v

    @field_validator("full_name")
    @classmethod
    def full_name_format(cls, v:str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Full_name cannot be empty")

    @field_validator("is_active")
    @classmethod
    def is_active(cls, v:int)-> int:
        if v not in (0,1):
            raise ValueError("is_active should be either 0 or 1")