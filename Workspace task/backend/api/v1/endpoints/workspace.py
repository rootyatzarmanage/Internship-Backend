import uuid

from fastapi import APIRouter

from backend.core.auth.dependencies import CurrentUser
from backend.core.database.dependencies import DatabaseSession
from backend.core.schemas.responses import SuccessResponse
from backend.schemas.requests.workspace import (
    CreateWorkspaceRequest,
    UpdateWorkspaceRequest,
)
from backend.schemas.response.workspace import WorkspaceResponse
from backend.services.workspace import WorkspaceService


workspace_router = APIRouter(
    prefix="/workspaces",
    tags=["Workspace"]
)


@workspace_router.post(
    "",
    response_model=SuccessResponse[WorkspaceResponse],
    status_code=201
)
async def create_workspace(
    body: CreateWorkspaceRequest,
    session: DatabaseSession,
    current_user: CurrentUser,
) -> SuccessResponse[WorkspaceResponse]:

    service = WorkspaceService(session)

    data = await service.create(
        body,
        current_user.id
    )

    return SuccessResponse(
        success=True,
        message="Workspace created successfully",
        data=data
    )


@workspace_router.get(
    "",
    response_model=SuccessResponse[list[WorkspaceResponse]]
)
async def get_workspaces(
    session: DatabaseSession,
    current_user: CurrentUser,
) -> SuccessResponse[list[WorkspaceResponse]]:

    service = WorkspaceService(session)

    data = await service.get_all(
        current_user.id
    )

    return SuccessResponse(
        success=True,
        message="Workspaces fetched successfully",
        data=data
    )


@workspace_router.get(
    "/{workspace_id}",
    response_model=SuccessResponse[WorkspaceResponse]
)
async def get_workspace(
    workspace_id: uuid.UUID,
    session: DatabaseSession,
    current_user: CurrentUser,
) -> SuccessResponse[WorkspaceResponse]:

    service = WorkspaceService(session)

    data = await service.get_one(
        workspace_id,
        current_user.id
    )

    return SuccessResponse(
        success=True,
        message="Workspace fetched successfully",
        data=data
    )


@workspace_router.put(
    "/{workspace_id}",
    response_model=SuccessResponse[WorkspaceResponse]
)
async def update_workspace(
    workspace_id: uuid.UUID,
    body: UpdateWorkspaceRequest,
    session: DatabaseSession,
    current_user: CurrentUser,
) -> SuccessResponse[WorkspaceResponse]:

    service = WorkspaceService(session)

    data = await service.update(
        workspace_id,
        body,
        current_user.id
    )

    return SuccessResponse(
        success=True,
        message="Workspace updated successfully",
        data=data
    )


@workspace_router.delete(
    "/{workspace_id}",
    response_model=SuccessResponse[dict]
)
async def delete_workspace(
    workspace_id: uuid.UUID,
    session: DatabaseSession,
    current_user: CurrentUser,
) -> SuccessResponse[dict]:

    service = WorkspaceService(session)

    await service.delete(
        workspace_id,
        current_user.id
    )

    return SuccessResponse(
        success=True,
        message="Workspace deleted successfully",
        data={}
    )