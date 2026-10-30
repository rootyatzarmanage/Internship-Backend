import datetime as dt
from uuid import UUID

from pydantic import BaseModel


class TeamMemberResponse(BaseModel):
    id: UUID
    name: str
    email: str
    role: str
    level_id: UUID
    level_name: str
    is_active: bool
    assigned_bookings: int        
    created_at: dt.datetime
    updated_at: dt.datetime


class TeamLevelResponse(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    member_count: int            
    active_member_count: int     
    booking_count: int            
    members: list[TeamMemberResponse]
    created_at: dt.datetime
    updated_at: dt.datetime


class TeamStatsResponse(BaseModel):
    members: int                 
    active_members: int
    inactive_members: int
    levels: int                   
    assigned_bookings: int        
    needs_assignment: int         


class SuperadminBookDemoTeamResponse(BaseModel):
    stats: TeamStatsResponse
    levels: list[TeamLevelResponse]


class AssignmentMemberResponse(BaseModel):
    member_id: UUID
    name: str
    email: str
    role: str
    level_id: UUID
    level_name: str
    is_active: bool
    is_primary: bool


class AssignmentHistoryResponse(BaseModel):
    id: UUID
    at: dt.datetime
    summary: str                 
    note: str | None = None
    actor_id: UUID | None = None
    actor_name: str | None = None


class SuperadminBookDemoAssignmentResponse(BaseModel):
    booking_id: UUID
    book_demo_id: str | None = None
    can_assign: bool              
    assigned: bool
    primary_member_id: UUID | None = None
    members: list[AssignmentMemberResponse]  
    note: str | None = None
    history: list[AssignmentHistoryResponse] 
    updated_at: dt.datetime | None = None
