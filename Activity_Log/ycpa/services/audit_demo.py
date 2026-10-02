from uuid import uuid4, UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ycpa.models.workspace import PimWorkspace, PimProject
from ycpa.models.audit import AuditAction

from ycpa.repositories.audit_demo import AuditDemoRepository
from ycpa.services.base import BaseService

from ycpa.schemas.requests.audit_demo import WorkspaceCreateRequest , ProjectCreateRequest



class AuditDemoService:

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = AuditDemoRepository(session)
        self.audit_service = BaseService(session)

    async def create_workspace(
        self,
        request: WorkspaceCreateRequest,
        current_user,
    ):
        workspace = PimWorkspace(
            id=uuid4(),
            owner_id=current_user.id,
            name=request.name,
            description=request.description,
            is_active=True,
            created_by=current_user.id,
            updated_by=current_user.id,
        )

        await self.repository.create_workspace(workspace)

        await self.audit_service.log_model_activity(
            action=AuditAction.WORKSPACE_CREATED,
            resource_type="workspace",
            resource_id=workspace.id,
            user_id=current_user.id,
            model=workspace,
            fields=[
                "name",
                "description",
                "is_active",
            ],
            workspace_id=workspace.id,
        )

        await self.session.commit()
        await self.session.refresh(workspace)

        return workspace

    async def create_project(
        self,
        request: ProjectCreateRequest,
        current_user,
    ):
        workspace = await self.repository.get_workspace(
            request.workspace_id
        )

        if not workspace or workspace.deleted_at is not None:
            return None

        project = PimProject(
            id=uuid4(),
            workspace_id=workspace.id,
            name=request.name,
            description=request.description,
            status=request.status,
            created_by=current_user.id,
            updated_by=current_user.id,
        )

        await self.repository.create_project(project)

        await self.audit_service.log_model_activity(
            action=AuditAction.PROJECT_CREATED,
            resource_type="project",
            resource_id=project.id,
            user_id=current_user.id,
            model=project,
            fields=[
                "name",
                "description",
                "status",
            ],
            workspace_id=workspace.id,
            project_id=project.id,
        )

        await self.session.commit()
        await self.session.refresh(project)

        return project

    async def get_activity_logs(
        self,
        current_user,
        workspace_id: UUID | None,
        limit: int,
        offset: int,
    ):
        logs, total = await self.repository.get_activity_logs(
            user_id=current_user.id,
            workspace_id=workspace_id,
            limit=limit,
            offset=offset,
        )

        activities = []

        for log in logs:
            description = (
                log.payload.get("description")
                if log.payload else None
            )

            if not description:
                description = str(log.action).replace(
                    "_", " "
                ).title()

            activities.append({
                "id": log.id,
                "user_id": log.user_id,
                "action": str(log.action),
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "workspace_id": log.workspace_id,
                "project_id": log.project_id,
                "description": description,
                "changed_from": log.changed_from,
                "changed_to": log.changed_to,
                "status": log.status,
                "created_at": log.created_at,
            })

        return {
            "total": total,
            "activities": activities,
        }