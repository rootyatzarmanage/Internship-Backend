import uuid

from fastapi import APIRouter

from backend.core.auth.dependencies import CurrentUser
from backend.core.database.dependencies import DatabaseSession
from backend.core.schemas.responses import SuccessResponse
from backend.schemas.requests.project import (
    CreateProjectRequest,
    UpdateProjectRequest,
)
from backend.schemas.response.project import ProjectResponse
from backend.services.project import ProjectService


project_router = APIRouter(
    prefix="/workspaces/{workspace_id}/projects",
    tags=["Project"]
)


@project_router.post(
    "",
    response_model=SuccessResponse[ProjectResponse],
    status_code=201
)
async def create_project(
    workspace_id: uuid.UUID,
    body: CreateProjectRequest,
    session: DatabaseSession,
    current_user: CurrentUser,
) -> SuccessResponse[ProjectResponse]:

    service = ProjectService(session)

    data = await service.create(
        workspace_id,
        body,
        current_user.id
    )

    return SuccessResponse(
        success=True,
        message="Project created successfully",
        data=data
    )


@project_router.get(
    "",
    response_model=SuccessResponse[list[ProjectResponse]]
)
async def get_projects(
    workspace_id: uuid.UUID,
    session: DatabaseSession,
    current_user: CurrentUser,
) -> SuccessResponse[list[ProjectResponse]]:

    service = ProjectService(session)

    data = await service.get_all(
        workspace_id,
        current_user.id
    )

    return SuccessResponse(
        success=True,
        message="Projects fetched successfully",
        data=data
    )


@project_router.get(
    "/{project_id}",
    response_model=SuccessResponse[ProjectResponse]
)
async def get_project(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    session: DatabaseSession,
    current_user: CurrentUser,
) -> SuccessResponse[ProjectResponse]:

    service = ProjectService(session)

    data = await service.get_one(
        project_id,
        workspace_id,
        current_user.id
    )

    return SuccessResponse(
        success=True,
        message="Project fetched successfully",
        data=data
    )


@project_router.put(
    "/{project_id}",
    response_model=SuccessResponse[ProjectResponse]
)
async def update_project(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    body: UpdateProjectRequest,
    session: DatabaseSession,
    current_user: CurrentUser,
) -> SuccessResponse[ProjectResponse]:

    service = ProjectService(session)

    data = await service.update(
        project_id,
        workspace_id,
        body,
        current_user.id
    )

    return SuccessResponse(
        success=True,
        message="Project updated successfully",
        data=data
    )


@project_router.delete(
    "/{project_id}",
    response_model=SuccessResponse[dict]
)
async def delete_project(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    session: DatabaseSession,
    current_user: CurrentUser,
) -> SuccessResponse[dict]:

    service = ProjectService(session)

    await service.delete(
        project_id,
        workspace_id,
        current_user.id
    )

    return SuccessResponse(
        success=True,
        message="Project deleted successfully",
        data={}
    )