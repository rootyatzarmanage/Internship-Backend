from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from ycpa.core.database.dependencies import DatabaseSession
from ycpa.core.auth.dependencies import CurrentUser

from ycpa.schemas.requests.audit_demo import WorkspaceCreateRequest, ProjectCreateRequest
from ycpa.schemas.responses.audit_demo import WorkspaceCreateResponse, ProjectCreateResponse, ActivityLogsResponse


from ycpa.services.audit_demo import AuditDemoService


router = APIRouter(
    prefix="/audit-demo",
    tags=["Audit Demo"],
)


@router.post(
    "/workspaces",
    response_model=WorkspaceCreateResponse,
)
async def create_demo_workspace(
    request: WorkspaceCreateRequest,
    session: DatabaseSession,
    current_user: CurrentUser,
):
    service = AuditDemoService(session)

    workspace = await service.create_workspace(
        request=request,
        current_user=current_user,
    )

    return {
        "message": "Workspace created successfully",
        "workspace_id": workspace.id,
        "name": workspace.name,
    }


@router.post(
    "/projects",
    response_model=ProjectCreateResponse,
)
async def create_demo_project(
    request: ProjectCreateRequest,
    session: DatabaseSession,
    current_user: CurrentUser,
):
    service = AuditDemoService(session)

    project = await service.create_project(
        request=request,
        current_user=current_user,
    )

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Workspace not found",
        )

    return {
        "message": "Project created successfully",
        "project_id": project.id,
        "workspace_id": project.workspace_id,
        "name": project.name,
    }


@router.get(
    "/activity-logs",
    response_model=ActivityLogsResponse,
)
async def get_demo_activity_logs(
    session: DatabaseSession,
    current_user: CurrentUser,
    workspace_id: UUID | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    service = AuditDemoService(session)

    return await service.get_activity_logs(
        current_user=current_user,
        workspace_id=workspace_id,
        limit=limit,
        offset=offset,
    )