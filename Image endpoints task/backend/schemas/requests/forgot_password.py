from pydantic import BaseModel, EmailStr, field_validator

class ForgotPasswordRequest(BaseModel):
    email : EmailStr

    @field_validator("email")
    @classmethod
    def email_format(cls , v:EmailStr):
        v = v.strip().lower()
        if not v:
            raise ValueError("Email should not be empty")
        return v

class ResetPasswordRequest(BaseModel):
    reset_token: str
    new_password: str

    @field_validator("reset_token")
    @classmethod
    def reset_token_format(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Reset token should not be empty")
        return v

    @field_validator("new_password")
    @classmethod
    def new_password_format(cls,v:str)-> str:
        v = v.strip()
        if not v:
            raise ValueError("Password cannot be empty")
        if len(v) < 8:
            raise ValueError("Password must be greater than 8")
        return v