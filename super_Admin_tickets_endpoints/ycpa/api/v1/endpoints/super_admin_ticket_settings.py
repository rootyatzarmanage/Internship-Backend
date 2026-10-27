import logging
from typing import Annotated

from fastapi import APIRouter, Query, status

from ycpa.core.auth.dependencies import SuperAdminUser
from ycpa.core.database.dependencies import DatabaseSession
from ycpa.core.schemas.responses import SuccessResponse
from ycpa.schemas.requests.super_admin_ticket_settings import (
    SettingsCreateRequest,
    SettingsUpdateRequest,
    TeamQuery,
)
from ycpa.schemas.responses.super_admin_ticket_settings import (
    LevelOut,
    MemberOut,
    SettingsRulesResponse,
    TicketSettingsResponse,
)
from ycpa.services.super_admin_ticket_settings import SuperAdminTicketSettingsService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/super-admin/tickets/settings",
    tags=["Super Admin - Ticket Settings"],
)


@router.get(
    "",
    response_model=SuccessResponse[TicketSettingsResponse],
    summary="Read levels, rules, and team; optionally filter by member ID/name/level",
)
async def get_settings(
    current_user: SuperAdminUser,
    session: DatabaseSession,
    params: Annotated[TeamQuery, Query()],
):
    service = SuperAdminTicketSettingsService(session)
    return SuccessResponse(data=await service.get_settings(params))


@router.post(
    "",
    response_model=SuccessResponse[LevelOut | MemberOut],
    status_code=status.HTTP_201_CREATED,
    summary="Create a support level or team member",
)
async def create_setting(
    body: SettingsCreateRequest,
    current_user: SuperAdminUser,
    session: DatabaseSession,
):
    service = SuperAdminTicketSettingsService(session)
    if body.kind == "level":
        data = await service.create_level(body)
    else:
        data = await service.create_member(body)
    return SuccessResponse(message="Support setting created.", data=data)


@router.patch(
    "",
    response_model=SuccessResponse[LevelOut | SettingsRulesResponse],
    summary="Update level SLA or escalation rules",
)
async def update_setting(
    body: SettingsUpdateRequest,
    current_user: SuperAdminUser,
    session: DatabaseSession,
):
    service = SuperAdminTicketSettingsService(session)
    if body.kind == "level":
        data = await service.update_level_sla(body.level_id, body)
    else:
        data = await service.update_rules(body)
    return SuccessResponse(message="Support setting updated.", data=data)
