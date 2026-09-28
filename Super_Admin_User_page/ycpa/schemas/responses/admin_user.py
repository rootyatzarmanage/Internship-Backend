from datetime import datetime
from pydantic import BaseModel


class UserMetricResponse(BaseModel):
    value: int
    percentage_change: float

class AdminUserItem(BaseModel):
    user_id: str
    name: str
    email: str
    phone_number: str | None
    workspace_count: int
    projects: int
    status: str
    verified: bool
    last_login: datetime | None
    registered: datetime

class AdminUserListResponse(BaseModel):
    items: list[AdminUserItem]
    total: int
    page: int
    limit: int

class VerifiedStatusItem(BaseModel):
    month: str
    verified: int
    not_verified: int


class VerifiedStatusResponse(BaseModel):
    year: int
    items: list[VerifiedStatusItem]

class UserStatusItem(BaseModel):
    status: str
    count: int


class UserStatusResponse(BaseModel):
    statuses: list[UserStatusItem]