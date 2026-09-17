from pydantic import BaseModel , EmailStr ,field_validator

class LoginRequest(BaseModel):
    email : EmailStr
    password : str

    @field_validator("email")
    @classmethod
    def email_format(cls , v:EmailStr) -> EmailStr:
        v = str(v).strip().lower()
        if not v:
            return ValueError("Email cannot be empty")
        return v

    @field_validator("password")
    @classmethod
    def password_format(cls,v:str) -> str:
        v = v.strip()
        if not v:
            return ValueError("Password cannot be empty")
        if len(v) < 8:
            return ValueError("Password must be atleast 8 characters")
        return v