from pydantic import BaseModel, EmailStr, field_validator


class RegisterRequest(BaseModel):
    email : EmailStr
    password : str
    full_name : str

    @field_validator("email")
    @classmethod
    def email_format(cls, v: EmailStr) -> EmailStr:
        v = v.strip().lower()
        if not v:
            raise ValueError("Email cannot be empty")
        return v
    def password_format(cls, v:str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Password cannot be empty")
        if len(v) < 8:
            raise ValueError("Password must be greater than 8")
    def full_name_format(cls, v:str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Full name must not be empty")

