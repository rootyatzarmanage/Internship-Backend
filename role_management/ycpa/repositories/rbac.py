from __future__ import annotations
import uuid

from datetime import datetime, timezone
from typing import Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ycpa.models.rbac import Module, RolePermission, Submodule
from ycpa.models.roles import Role
from ycpa.models.workspace import (
    PimWorkspace,
    PimWorkspaceMember,
    PimProject,
    PimProjectMember,
    AimWorkspace,
    AimWorkspaceMember,
    AimProject,
    AimProjectMember,
)


WorkspaceType = Literal["pim", "aim"]

ALLOWED_ACTIONS = {
    "can_view",
    "can_create",
    "can_edit",
    "can_delete",
    "can_approve",
    "can_share",
}


class RBACRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all_roles(self) -> list[Role]:

        result = await self.session.execute(
            select(Role)
            .where(Role.deleted_at.is_(None))
            .order_by(Role.created_at)
        )

        return list(result.scalars().all())

    async def get_role_by_name(
        self,
        name: str,
        product_type: str,
    ) -> Role | None:

        return await self.session.scalar(
            select(Role).where(
                Role.name == name,
                Role.product_type == product_type,
                Role.deleted_at.is_(None),
            )
        )

    async def get_role_by_id(
        self,
        role_id: uuid.UUID,
    ) -> Role | None:

        return await self.session.scalar(
            select(Role).where(
                Role.id == role_id,
                Role.deleted_at.is_(None),
            )
        )

    async def create_role(
        self,
        name: str,
        product_type: str,
        description: str | None,
        created_by: uuid.UUID,
        workspace_id: uuid.UUID | None = None,
    ) -> Role:

        role = Role(
            id=uuid.uuid4(),
            name=name,
            description=description,
            product_type=product_type,
            is_system=False,
            is_editable=True,
            is_active=True,
            created_by_type="super_admin",
            workspace_id=workspace_id,
            created_by=created_by,
        )

        self.session.add(role)
        await self.session.flush()

        return role

    async def update_role(
        self,
        role: Role,
        name: str | None = None,
        description: str | None = None,
        is_active: bool | None = None,
        updated_by: uuid.UUID | None = None,
    ) -> Role:

        if name is not None:
            role.name = name

        if description is not None:
            role.description = description

        if is_active is not None:
            role.is_active = is_active

        if updated_by is not None:
            role.updated_by = updated_by

        await self.session.flush()

        return role

    async def delete_role(
        self,
        role: Role,
        deleted_by: uuid.UUID,
    ) -> None:

        role.deleted_at = datetime.now(timezone.utc)
        role.deleted_by = deleted_by

        await self.session.flush()

    async def get_all_modules(self) -> list[Module]:

        result = await self.session.execute(
            select(Module)
            .where(Module.is_active.is_(True))
            .order_by(Module.order)
        )

        return list(result.scalars().all())

    async def get_module_by_id(
        self,
        module_id: uuid.UUID,
    ) -> Module | None:

        return await self.session.scalar(
            select(Module).where(
                Module.id == module_id
            )
        )

    async def get_submodules_for_module(
        self,
        module_id: uuid.UUID,
    ) -> list[Submodule]:

        result = await self.session.execute(
            select(Submodule)
            .where(
                Submodule.module_id == module_id,
                Submodule.is_active.is_(True),
            )
            .order_by(Submodule.order)
        )

        return list(result.scalars().all())

    async def get_permissions_for_role(
        self,
        role_id: uuid.UUID,
    ) -> list[RolePermission]:

        result = await self.session.execute(
            select(RolePermission).where(
                RolePermission.role_id == role_id
            )
        )

        return list(result.scalars().all())

    async def get_permission(
        self,
        role_id: uuid.UUID,
        module_id: uuid.UUID,
        submodule_id: uuid.UUID | None,
    ) -> RolePermission | None:

        return await self.session.scalar(
            select(RolePermission).where(
                RolePermission.role_id == role_id,
                RolePermission.module_id == module_id,
                RolePermission.submodule_id == submodule_id,
            )
        )

    async def upsert_permission(
        self,
        role_id: uuid.UUID,
        module_id: uuid.UUID,
        submodule_id: uuid.UUID | None,
        can_view: bool,
        can_create: bool,
        can_edit: bool,
        can_delete: bool,
        can_approve: bool,
        can_share: bool,
        updated_by: uuid.UUID,
    ) -> RolePermission:

        existing = await self.get_permission(
            role_id,
            module_id,
            submodule_id,
        )

        if existing:
            existing.can_view = can_view
            existing.can_create = can_create
            existing.can_edit = can_edit
            existing.can_delete = can_delete
            existing.can_approve = can_approve
            existing.can_share = can_share
            existing.updated_by = updated_by

            await self.session.flush()

            return existing

        permission = RolePermission(
            id=uuid.uuid4(),
            role_id=role_id,
            module_id=module_id,
            submodule_id=submodule_id,
            can_view=can_view,
            can_create=can_create,
            can_edit=can_edit,
            can_delete=can_delete,
            can_approve=can_approve,
            can_share=can_share,
            created_by=updated_by,
        )

        self.session.add(permission)
        await self.session.flush()

        return permission

    async def delete_permissions_for_role(
        self,
        role_id: uuid.UUID,
    ) -> None:

        permissions = await self.get_permissions_for_role(role_id)

        for permission in permissions:
            await self.session.delete(permission)

        await self.session.flush()

    async def get_workspace_role(
        self,
        user_id: uuid.UUID,
        workspace_id: uuid.UUID,
        workspace_type: WorkspaceType,
    ) -> str | None:

        if workspace_type == "pim":

            workspace_model = PimWorkspace
            member_model = PimWorkspaceMember
            project_model = PimProject
            project_member_model = PimProjectMember

        elif workspace_type == "aim":

            workspace_model = AimWorkspace
            member_model = AimWorkspaceMember
            project_model = AimProject
            project_member_model = AimProjectMember

        else:
            raise ValueError("Invalid workspace_type")

        workspace = await self.session.scalar(
            select(workspace_model).where(
                workspace_model.id == workspace_id,
                workspace_model.owner_id == user_id,
                workspace_model.deleted_at.is_(None),
                workspace_model.is_active.is_(True),
            )
        )

        if workspace:
            return "owner"

        member = await self.session.scalar(
            select(member_model).where(
                member_model.workspace_id == workspace_id,
                member_model.user_id == user_id,
            )
        )

        if member:
            return member.role

        project_membership = await self.session.scalar(
            select(project_member_model)
            .join(
                project_model,
                project_model.id == project_member_model.project_id,
            )
            .where(
                project_model.workspace_id == workspace_id,
                project_model.deleted_at.is_(None),
                project_member_model.user_id == user_id,
            )
        )

        if project_membership:
            return "member"

        return None

    async def workspace_exists(
        self,
        workspace_id: uuid.UUID,
        workspace_type: WorkspaceType,
    ) -> bool:

        if workspace_type == "pim":
            model = PimWorkspace
        elif workspace_type == "aim":
            model = AimWorkspace
        else:
            raise ValueError("Invalid workspace_type")

        result = await self.session.scalar(
            select(model).where(
                model.id == workspace_id,
                model.deleted_at.is_(None),
                model.is_active.is_(True),
            )
        )

        return result is not None

    async def project_exists(
        self,
        project_id: uuid.UUID,
        workspace_type: WorkspaceType,
    ) -> bool:

        if workspace_type == "pim":
            model = PimProject
            other_model = AimProject

        elif workspace_type == "aim":
            model = AimProject
            other_model = PimProject

        else:
            raise ValueError("Invalid workspace_type")

        result = await self.session.scalar(
            select(model).where(
                model.id == project_id,
                model.deleted_at.is_(None),
            )
        )

        if result:
            return True

        result = await self.session.scalar(
            select(other_model).where(
                other_model.id == project_id,
                other_model.deleted_at.is_(None),
            )
        )

        return result is not None

    async def _get_project_member(
        self,
        user_id: uuid.UUID,
        project_id: uuid.UUID,
        workspace_type: WorkspaceType,
        allow_other_product: bool = True,
    ):

        if workspace_type == "pim":
            member_model = PimProjectMember
            other_model = AimProjectMember

        elif workspace_type == "aim":
            member_model = AimProjectMember
            other_model = PimProjectMember

        else:
            raise ValueError("Invalid workspace_type")

        member = await self.session.scalar(
            select(member_model).where(
                member_model.project_id == project_id,
                member_model.user_id == user_id,
            )
        )

        if member or not allow_other_product:
            return member

        return await self.session.scalar(
            select(other_model).where(
                other_model.project_id == project_id,
                other_model.user_id == user_id,
            )
        )

    async def get_project_permission(
        self,
        user_id: uuid.UUID,
        project_id: uuid.UUID,
        workspace_type: WorkspaceType,
        module: str,
        action: str,
    ) -> bool:

        if action not in ALLOWED_ACTIONS:
            return False

        member = await self._get_project_member(
            user_id=user_id,
            project_id=project_id,
            workspace_type=workspace_type,
            allow_other_product=True,
        )

        if not member:
            return False

        if getattr(member, "is_share_only", False):
            return False

        module_row = await self.session.scalar(
            select(Module).where(
                Module.slug == module,
                Module.is_active.is_(True),
            )
        )

        if not module_row:
            return False

        permission = await self.session.scalar(
            select(RolePermission).where(
                RolePermission.role_id == member.role_id,
                RolePermission.module_id == module_row.id,
                RolePermission.submodule_id.is_(None),
            )
        )

        if not permission:
            return False

        return bool(getattr(permission, action, False))

    async def get_project_submodule_permission(
        self,
        user_id: uuid.UUID,
        project_id: uuid.UUID,
        workspace_type: WorkspaceType,
        module: str,
        submodule: str,
        action: str,
    ) -> bool:

        if action not in ALLOWED_ACTIONS:
            return False

        member = await self._get_project_member(
            user_id=user_id,
            project_id=project_id,
            workspace_type=workspace_type,
            allow_other_product=False,
        )

        if not member:
            return False

        if getattr(member, "is_share_only", False):
            return False

        module_row = await self.session.scalar(
            select(Module).where(
                Module.slug == module,
                Module.is_active.is_(True),
            )
        )

        if not module_row:
            return False

        submodule_row = await self.session.scalar(
            select(Submodule).where(
                Submodule.module_id == module_row.id,
                Submodule.slug == submodule,
                Submodule.is_active.is_(True),
            )
        )

        if not submodule_row:
            return False

        permission = await self.session.scalar(
            select(RolePermission).where(
                RolePermission.role_id == member.role_id,
                RolePermission.module_id == module_row.id,
                RolePermission.submodule_id == submodule_row.id,
            )
        )

        if permission:
            return bool(getattr(permission, action, False))

        module_permission = await self.session.scalar(
            select(RolePermission).where(
                RolePermission.role_id == member.role_id,
                RolePermission.module_id == module_row.id,
                RolePermission.submodule_id.is_(None),
            )
        )

        if not module_permission:
            return False

        return bool(getattr(module_permission, action, False))


    async def get_all_project_permissions(
        self,
        user_id: uuid.UUID,
        project_id: uuid.UUID,
        workspace_type: WorkspaceType,
    ) -> dict:

        member = await self._get_project_member(
            user_id=user_id,
            project_id=project_id,
            workspace_type=workspace_type,
            allow_other_product=True,
        )

        if not member:
            return {}

        if getattr(member, "is_share_only", False):
            return {}

        result = await self.session.execute(
            select(RolePermission, Module, Submodule)
            .join(
                Module,
                Module.id == RolePermission.module_id,
            )
            .outerjoin(
                Submodule,
                Submodule.id == RolePermission.submodule_id,
            )
            .where(
                RolePermission.role_id == member.role_id,
                Module.is_active.is_(True),
            )
        )

        permissions = {}

        for permission, module, submodule in result.all():

            if submodule and not submodule.is_active:
                continue

            key = (
                f"{module.slug}/{submodule.slug}"
                if submodule
                else module.slug
            )

            permissions[key] = {
                "can_view": permission.can_view,
                "can_create": permission.can_create,
                "can_edit": permission.can_edit,
                "can_delete": permission.can_delete,
                "can_approve": permission.can_approve,
                "can_share": permission.can_share,
            }

        return permissions


    async def get_workspace_role_for_project(
        self,
        user_id: uuid.UUID,
        project_id: uuid.UUID,
        workspace_type: WorkspaceType,
    ) -> str | None:

        if workspace_type == "pim":

            project_model = PimProject
            workspace_model = PimWorkspace
            member_model = PimWorkspaceMember

            other_project_model = AimProject
            other_workspace_model = AimWorkspace
            other_member_model = AimWorkspaceMember

        elif workspace_type == "aim":

            project_model = AimProject
            workspace_model = AimWorkspace
            member_model = AimWorkspaceMember

            other_project_model = PimProject
            other_workspace_model = PimWorkspace
            other_member_model = PimWorkspaceMember

        else:
            raise ValueError("Invalid workspace_type")

        project = await self.session.scalar(
            select(project_model).where(
                project_model.id == project_id,
                project_model.deleted_at.is_(None),
            )
        )

        if not project:

            project = await self.session.scalar(
                select(other_project_model).where(
                    other_project_model.id == project_id,
                    other_project_model.deleted_at.is_(None),
                )
            )

            if not project:
                return None

            workspace_model = other_workspace_model
            member_model = other_member_model

        workspace = await self.session.scalar(
            select(workspace_model).where(
                workspace_model.id == project.workspace_id,
                workspace_model.deleted_at.is_(None),
                workspace_model.is_active.is_(True),
            )
        )

        if not workspace:
            return None

        if workspace.owner_id == user_id:
            return "owner"

        member = await self.session.scalar(
            select(member_model).where(
                member_model.workspace_id == workspace.id,
                member_model.user_id == user_id,
            )
        )
        return member.role if member else None