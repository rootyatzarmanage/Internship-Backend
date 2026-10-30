from uuid import UUID

from fastapi import APIRouter, Query, Request, status

from ycpa.core.auth.dependencies import SuperAdminUser
from ycpa.core.database.dependencies import DatabaseSession
from ycpa.core.schemas.responses import SuccessResponse
from ycpa.schemas.requests.superadmin_bookademo_team import (
    SuperadminBookDemoAssignmentRequest,
    SuperadminBookDemoLevelRequest,
    SuperadminBookDemoMemberRequest,
    SuperadminBookDemoTeamQuery,
)
from ycpa.schemas.responses.superadmin_bookademo_team import (
    SuperadminBookDemoAssignmentResponse,
    SuperadminBookDemoTeamResponse,
    TeamLevelResponse,
    TeamMemberResponse,
    TeamStatsResponse,
)
from ycpa.services.superadmin_bookademo_team import SuperadminBookDemoTeamService

router = APIRouter(prefix="/superadmin/book-a-demo", tags=["Superadmin Book a Demo Team"])


def _client(request: Request) -> tuple[str | None, str | None]:
    """(ip, user-agent) for the audit trail."""
    return request.client.host if request.client else None, request.headers.get("user-agent")


@router.get(
    "/team",
    response_model=SuccessResponse[SuperadminBookDemoTeamResponse],
    status_code=status.HTTP_200_OK,
    summary="Team & Levels: stat cards and every level with its members (also feeds the assignment dialog)",
)
async def team_overview(
    session: DatabaseSession,
    current_user: SuperAdminUser,
    search: str | None = Query(None, max_length=100, description="level name/focus area, member name, email or role"),
) -> SuccessResponse[SuperadminBookDemoTeamResponse]:
    service = SuperadminBookDemoTeamService(session)
    query = SuperadminBookDemoTeamQuery(search=search)
    result = await service.overview(query)
    return SuccessResponse(success=True, data=result)


@router.get(
    "/team/summary",
    response_model=SuccessResponse[TeamStatsResponse],
    status_code=status.HTTP_200_OK,
    summary="Team stat cards and assignment coverage (Overview strip: upcoming demos that need a team)",
)
async def team_summary(
    session: DatabaseSession,
    current_user: SuperAdminUser,
) -> SuccessResponse[TeamStatsResponse]:
    service = SuperadminBookDemoTeamService(session)
    result = await service.summary()
    return SuccessResponse(success=True, data=result)


@router.post(
    "/team/levels",
    response_model=SuccessResponse[TeamLevelResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Add level",
)
async def create_level(
    request: Request,
    body: SuperadminBookDemoLevelRequest,
    session: DatabaseSession,
    current_user: SuperAdminUser,
) -> SuccessResponse[TeamLevelResponse]:
    service = SuperadminBookDemoTeamService(session)
    ip, user_agent = _client(request)
    result = await service.create_level(body, current_user, ip=ip, user_agent=user_agent)
    return SuccessResponse(success=True, message="Team level saved.", data=result)


@router.put(
    "/team/levels/{level_id}",
    response_model=SuccessResponse[TeamLevelResponse],
    status_code=status.HTTP_200_OK,
    summary="Edit level",
)
async def update_level(
    request: Request,
    level_id: UUID,
    body: SuperadminBookDemoLevelRequest,
    session: DatabaseSession,
    current_user: SuperAdminUser,
) -> SuccessResponse[TeamLevelResponse]:
    service = SuperadminBookDemoTeamService(session)
    ip, user_agent = _client(request)
    result = await service.update_level(level_id, body, current_user, ip=ip, user_agent=user_agent)
    return SuccessResponse(success=True, message="Team level saved.", data=result)


@router.delete(
    "/team/levels/{level_id}",
    response_model=SuccessResponse[None],
    status_code=status.HTTP_200_OK,
    summary="Delete an empty level (at least one level must remain)",
)
async def delete_level(
    request: Request,
    level_id: UUID,
    session: DatabaseSession,
    current_user: SuperAdminUser,
) -> SuccessResponse[None]:
    service = SuperadminBookDemoTeamService(session)
    ip, user_agent = _client(request)
    await service.delete_level(level_id, current_user, ip=ip, user_agent=user_agent)
    return SuccessResponse(success=True, message="Empty level deleted.")


@router.post(
    "/team/members",
    response_model=SuccessResponse[TeamMemberResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Add team member",
)
async def create_member(
    request: Request,
    body: SuperadminBookDemoMemberRequest,
    session: DatabaseSession,
    current_user: SuperAdminUser,
) -> SuccessResponse[TeamMemberResponse]:
    service = SuperadminBookDemoTeamService(session)
    ip, user_agent = _client(request)
    result = await service.create_member(body, current_user, ip=ip, user_agent=user_agent)
    return SuccessResponse(success=True, message="Team member saved.", data=result)


@router.put(
    "/team/members/{member_id}",
    response_model=SuccessResponse[TeamMemberResponse],
    status_code=status.HTTP_200_OK,
    summary="Edit team member (rename, move level, activate / deactivate)",
)
async def update_member(
    request: Request,
    member_id: UUID,
    body: SuperadminBookDemoMemberRequest,
    session: DatabaseSession,
    current_user: SuperAdminUser,
) -> SuccessResponse[TeamMemberResponse]:
    service = SuperadminBookDemoTeamService(session)
    ip, user_agent = _client(request)
    result = await service.update_member(member_id, body, current_user, ip=ip, user_agent=user_agent)
    return SuccessResponse(success=True, message="Team member saved.", data=result)


@router.get(
    "/bookings/{booking_id}/assignment",
    response_model=SuccessResponse[SuperadminBookDemoAssignmentResponse],
    status_code=status.HTTP_200_OK,
    summary="Assigned internal team, handoff note and assignment history of one booking",
)
async def get_assignment(
    booking_id: UUID,
    session: DatabaseSession,
    current_user: SuperAdminUser,
) -> SuccessResponse[SuperadminBookDemoAssignmentResponse]:
    service = SuperadminBookDemoTeamService(session)
    result = await service.get_assignment(booking_id)
    return SuccessResponse(success=True, data=result)


@router.post(
    "/bookings/{booking_id}/assignment",
    response_model=SuccessResponse[SuperadminBookDemoAssignmentResponse],
    status_code=status.HTTP_200_OK,
    summary="Save assignment: replaces the booking's team, primary contact and note (empty member_ids removes it)",
)
async def save_assignment(
    request: Request,
    booking_id: UUID,
    body: SuperadminBookDemoAssignmentRequest,
    session: DatabaseSession,
    current_user: SuperAdminUser,
) -> SuccessResponse[SuperadminBookDemoAssignmentResponse]:
    service = SuperadminBookDemoTeamService(session)
    ip, user_agent = _client(request)
    result, changed = await service.save_assignment(booking_id, body, current_user, ip=ip, user_agent=user_agent)
    if not changed:
        message = "Assignment is already up to date."
    else:
        message = "Assignment saved." if result.assigned else "Assignment removed."
    return SuccessResponse(success=True, message=message, data=result)
