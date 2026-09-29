from __future__ import annotations

import uuid
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession
from ycpa.repositories.rbac import RBACRepository


WorkspaceType = Literal["pim", "aim"]
WorkspaceRole = Literal["owner", "admin", "member"]

ROLE_WEIGHT: dict[str, int] = {
    "owner": 3,
    "admin": 2,
    "member": 1,
}

VALID_WORKSPACE_TYPES = {"pim", "aim"}
VALID_WORKSPACE_ROLES = {"owner", "admin", "member"}


class RBACService:

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = RBACRepository(session)

    @staticmethod
    def _validate_workspace_type(
        workspace_type: str,
    ) -> None:
        if workspace_type not in VALID_WORKSPACE_TYPES:
            raise ValueError(
                f"Invalid workspace_type: {workspace_type}. "
                "Allowed values are 'pim' and 'aim'."
            )

    async def get_workspace_role(
        self,
        user_id: uuid.UUID,
        workspace_id: uuid.UUID,
        workspace_type: WorkspaceType,
    ) -> WorkspaceRole | None:

        self._validate_workspace_type(workspace_type)

        return await self.repository.get_workspace_role(
            user_id=user_id,
            workspace_id=workspace_id,
            workspace_type=workspace_type,
        )

    @staticmethod
    def workspace_role_meets(
        actual: WorkspaceRole | None,
        required: WorkspaceRole,
    ) -> bool:

        if actual is None:
            return False

        if actual not in VALID_WORKSPACE_ROLES:
            raise ValueError(f"Invalid actual role: {actual}")

        if required not in VALID_WORKSPACE_ROLES:
            raise ValueError(f"Invalid required role: {required}")

        return ROLE_WEIGHT[actual] >= ROLE_WEIGHT[required]

    async def get_project_permission(
        self,
        user_id: uuid.UUID,
        project_id: uuid.UUID,
        workspace_type: WorkspaceType,
        module: str,
        action: str,
    ) -> bool:

        self._validate_workspace_type(workspace_type)

        return await self.repository.get_project_permission(
            user_id=user_id,
            project_id=project_id,
            workspace_type=workspace_type,
            module=module,
            action=action,
        )

    async def get_project_submodule_permission(
        self,
        user_id: uuid.UUID,
        project_id: uuid.UUID,
        workspace_type: WorkspaceType,
        module: str,
        submodule: str,
        action: str,
    ) -> bool:

        self._validate_workspace_type(workspace_type)

        return await self.repository.get_project_submodule_permission(
            user_id=user_id,
            project_id=project_id,
            workspace_type=workspace_type,
            module=module,
            submodule=submodule,
            action=action,
        )

    async def get_all_project_permissions(
        self,
        user_id: uuid.UUID,
        project_id: uuid.UUID,
        workspace_type: WorkspaceType,
    ) -> dict:

        self._validate_workspace_type(workspace_type)

        return await self.repository.get_all_project_permissions(
            user_id=user_id,
            project_id=project_id,
            workspace_type=workspace_type,
        )

    async def workspace_exists(
        self,
        workspace_id: uuid.UUID,
        workspace_type: WorkspaceType,
    ) -> bool:

        self._validate_workspace_type(workspace_type)

        return await self.repository.workspace_exists(
            workspace_id=workspace_id,
            workspace_type=workspace_type,
        )

    async def project_exists(
        self,
        project_id: uuid.UUID,
        workspace_type: WorkspaceType,
    ) -> bool:

        self._validate_workspace_type(workspace_type)

        return await self.repository.project_exists(
            project_id=project_id,
            workspace_type=workspace_type,
        )

    async def get_workspace_role_for_project(
        self,
        user_id: uuid.UUID,
        project_id: uuid.UUID,
        workspace_type: WorkspaceType,
    ) -> str | None:

        self._validate_workspace_type(workspace_type)

        return await self.repository.get_workspace_role_for_project(
            user_id=user_id,
            project_id=project_id,
            workspace_type=workspace_type,
        )