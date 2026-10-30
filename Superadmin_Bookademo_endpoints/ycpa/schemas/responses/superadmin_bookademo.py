import datetime as dt
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

DayStatus = Literal["available", "busy", "unavailable"]
SlotState = Literal["booked", "free", "closed"]
TeamState = Literal["assigned", "unassigned", "not_applicable"]


class BookDemoKpiResponse(BaseModel):
    total: int                  
    new: int                      
    upcoming: int               
    cancelled: int               


class InvitePreferenceResponse(BaseModel):
    requested: int                
    not_requested: int            
    requested_percent: int


class ActivityDayResponse(BaseModel):
    date: dt.date                 
    new: int
    cancelled: int


class SuperadminBookDemoOverviewResponse(BaseModel):
    timezone: str
    as_of: dt.datetime
    kpis: BookDemoKpiResponse
    invite_preference: InvitePreferenceResponse
    activity: list[ActivityDayResponse]


class CalendarDayResponse(BaseModel):
    date: dt.date
    status: DayStatus
    booked: int                  
    open_slots: int               
    total_slots: int              


class SuperadminBookDemoCalendarResponse(BaseModel):
    year: int
    month: int
    timezone: str
    slots_per_day: int
    min_notice_hours: int
    max_advance_days: int
    as_of: dt.datetime
    days: list[CalendarDayResponse]


class SlotBookingResponse(BaseModel):
    id: UUID
    book_demo_id: str | None = None
    name: str
    company: str | None = None


class SlotItemResponse(BaseModel):
    starts_at: dt.datetime        
    time: str                     
    state: SlotState            
    outside_window: bool          
    booking: SlotBookingResponse | None = None


class SuperadminBookDemoSlotsResponse(BaseModel):
    date: dt.date
    timezone: str
    title: str                   
    booked: int
    open: int
    slots: list[SlotItemResponse]


class AssignedTeamSummaryResponse(BaseModel):
    state: TeamState                    
    primary_member_id: UUID | None = None
    primary_name: str | None = None
    primary_is_active: bool | None = None
    level_name: str | None = None         
    supporting_count: int = 0


class SuperadminBookDemoListItem(BaseModel):
    id: UUID
    book_demo_id: str | None = None
    name: str
    email: str
    company: str | None = None
    phone_code: str | None = None
    phone: str | None = None
    country: str | None = None
    preferred_at: dt.datetime | None = None
    demo_date: str | None = None         
    demo_time: str | None = None        
    visitor_timezone: str | None = None
    status: str
    opt: int
    invite: str                        
    created_at: dt.datetime
    booked_on: str                      
    assigned_team: AssignedTeamSummaryResponse


class SuperadminBookDemoListResponse(BaseModel):
    items: list[SuperadminBookDemoListItem]
    total: int
    page: int
    per_page: int
    pages: int
    first_item: int                       
    last_item: int


class SuperadminBookDemoDetailResponse(BaseModel):
    id: UUID
    book_demo_id: str | None = None
    name: str
    email: str
    company: str | None = None
    phone_code: str | None = None
    phone: str | None = None
    country: str | None = None
    status: str
    opt: int
    invite: str
    description: str | None = None
    message: str | None = None
    preferred_at: dt.datetime | None = None
    business_timezone: str
    business_date: str | None = None
    business_time: str | None = None
    visitor_timezone: str | None = None
    visitor_local_date: str | None = None
    visitor_local_time: str | None = None
    created_at: dt.datetime
    updated_at: dt.datetime
    deleted_at: dt.datetime | None = None
