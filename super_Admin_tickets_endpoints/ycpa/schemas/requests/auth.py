import re
 
from pydantic import BaseModel, EmailStr, Field, field_validator
 
 
class LoginRequest(BaseModel):
    id_token:     str = Field(..., description="Cognito ID token")
    access_token: str = Field(..., description="Cognito access token")
 
 
class ForgotPasswordRequest(BaseModel):
    email: EmailStr
 
 
class VerifyOtpRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)
 
 
class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=8, max_length=128)
 
 
class RegisterProfileRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
 
    @field_validator("full_name", mode="before")
    @classmethod
    def clean_full_name(cls, v: str) -> str:
        return " ".join(v.strip().split())
 
 
class UpdateProfileRequest(BaseModel):
    full_name:    str | None = Field(None, min_length=2, max_length=100)
    company_name: str | None = Field(None, max_length=255)
    job_title:    str | None = Field(None, max_length=255)
    phone:        str | None = Field(None, max_length=20)
    timezone:     str | None = Field(None, max_length=100)
 
    @field_validator("full_name", "company_name", "job_title", "phone", mode="before")
    @classmethod
    def strip_fields(cls, v):
        if isinstance(v, str):
            return " ".join(v.strip().split())
        return v
 
    @field_validator("phone", mode="after")
    @classmethod
    def validate_phone(cls, v):
        if v and not re.match(r"^\+?[\d\s\-().]{7,20}$", v):
            raise ValueError("Invalid phone number format")
        return v
 
    @field_validator("timezone", mode="after")
    @classmethod
    def validate_timezone(cls, v):
        if v is None:
            return v
        import zoneinfo
        if v not in zoneinfo.available_timezones():
            raise ValueError(f"Invalid timezone: {v}")
        return v