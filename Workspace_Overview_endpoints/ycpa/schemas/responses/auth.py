from datetime import datetime
from uuid import UUID
 
from pydantic import BaseModel
 
 
class UserProfileResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    company_name: str | None = None
    job_title: str | None = None
    phone: str | None = None
    avatar_url: str | None = None
    timezone: str
    platform_role: str
    platform_permissions: list[str] = []
    is_active: bool
    is_onboarded: bool
    is_default_onboarding: bool = False
    email_verified: bool
    created_at: datetime
 
    model_config = {"from_attributes": True}
 
 
class LoginResponse(BaseModel):
    user: UserProfileResponse
    is_new_user: bool
 
 
class MeResponse(BaseModel):
    user: UserProfileResponse