from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from ycpa.core.auth.dependencies import SuperAdminUser
from ycpa.core.database.dependencies import DatabaseSession

from ycpa.models.platform_permission import (
    PLATFORM_PERMISSIONS,
    UserPlatformPermission,
)
from ycpa.models.user import User

from ycpa.repositories.rbac import RBACRepository
from ycpa.services.rbac import RBACService

from ycpa.schemas.requests.rbac import (
    CreateRoleRequest,
    UpdateRoleRequest,
    UpsertPermissionRequest,
    UpdatePlatformPermissionsRequest,
)

from ycpa.schemas.responses.rbac import (
    RoleResponse,
    ModuleWithSubmodules,
    SubmoduleResponse,
    PermissionResponse,
    PlatformPermissionDefResponse,
    UserPlatformPermResponse,
)


router = APIRouter(
    prefix="/rbac",
    tags=["RBAC"],
)

@router.get(
    "/roles",
    response_model=list[RoleResponse],
)
async def list_roles(
    current_user: SuperAdminUser,
    session: DatabaseSession,
):
    repository = RBACRepository(session)

    return await repository.get_all_roles()

@router.post(
    "/roles",
    response_model=RoleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_role(
    body: CreateRoleRequest,
    current_user: SuperAdminUser,
    session: DatabaseSession,
):
    repository = RBACRepository(session)

    if body.product_type not in ("pim", "aim", "both"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="product_type must be pim, aim, or both",
        )

    existing_role = await repository.get_role_by_name(
        name=body.name,
        product_type=body.product_type,
    )

    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Role '{body.name}' already exists "
                f"for {body.product_type}"
            ),
        )

    role = await repository.create_role(
        name=body.name,
        product_type=body.product_type,
        description=body.description,
        created_by=current_user.id,
        workspace_id=body.workspace_id,
    )

    await session.commit()
    return role

@router.patch(
    "/roles/{role_id}",
    response_model=RoleResponse,
)
async def update_role(
    role_id: uuid.UUID,
    body: UpdateRoleRequest,
    current_user: SuperAdminUser,
    session: DatabaseSession,
):
    repository = RBACRepository(session)

    role = await repository.get_role_by_id(role_id)

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )

    if role.is_system and not role.is_editable:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="System roles cannot be modified",
        )

    if body.name is not None:
        existing_role = await repository.get_role_by_name(
            name=body.name,
            product_type=role.product_type,
        )

        if existing_role and existing_role.id != role_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Role '{body.name}' already exists",
            )

    role = await repository.update_role(
        role=role,
        name=body.name,
        description=body.description,
        is_active=body.is_active,
        updated_by=current_user.id,
    )

    await session.commit()
    return role

@router.delete(
    "/roles/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_role(
    role_id: uuid.UUID,
    current_user: SuperAdminUser,
    session: DatabaseSession,
):
    repository = RBACRepository(session)
    role = await repository.get_role_by_id(role_id)

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )

    if role.is_system:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="System roles cannot be deleted",
        )

    await repository.delete_permissions_for_role(role_id)

    await repository.delete_role(
        role=role,
        deleted_by=current_user.id,
    )

    await session.commit()
    return None

@router.get(
    "/modules",
    response_model=list[ModuleWithSubmodules],
)
async def list_modules(
    current_user: SuperAdminUser,
    session: DatabaseSession,
):
    repository = RBACRepository(session)
    modules = await repository.get_all_modules()

    result = []

    for module in modules:
        submodules = await repository.get_submodules_for_module(
            module.id
        )

        result.append(
            ModuleWithSubmodules(
                id=module.id,
                name=module.name,
                slug=module.slug,
                product_type=module.product_type,
                order=module.order,
                submodules=[
                    SubmoduleResponse.model_validate(submodule)
                    for submodule in submodules
                ],
            )
        )

    return result

@router.get(
    "/roles/{role_id}/permissions",
    response_model=list[PermissionResponse],
)
async def get_role_permissions(
    role_id: uuid.UUID,
    current_user: SuperAdminUser,
    session: DatabaseSession,
):
    repository = RBACRepository(session)

    role = await repository.get_role_by_id(role_id)

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )

    return await repository.get_permissions_for_role(role_id)


@router.put(
    "/roles/{role_id}/permissions",
    response_model=PermissionResponse,
)
async def upsert_permission(
    role_id: uuid.UUID,
    body: UpsertPermissionRequest,
    current_user: SuperAdminUser,
    session: DatabaseSession,
):
    repository = RBACRepository(session)

    role = await repository.get_role_by_id(role_id)

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )

    if role.is_system and not role.is_editable:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This system role's permissions are not editable",
        )

    module = await repository.get_module_by_id(body.module_id)

    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found",
        )

    if body.submodule_id is not None:
        submodule = await session.get(
            __import__(
                "ycpa.models.rbac",
                fromlist=["Submodule"],
            ).Submodule,
            body.submodule_id,
        )

        if not submodule or submodule.module_id != body.module_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Submodule not found for this module",
            )

    permission = await repository.upsert_permission(
        role_id=role_id,
        module_id=body.module_id,
        submodule_id=body.submodule_id,
        can_view=body.can_view,
        can_create=body.can_create,
        can_edit=body.can_edit,
        can_delete=body.can_delete,
        can_approve=body.can_approve,
        can_share=body.can_share,
        updated_by=current_user.id,
    )

    await session.commit()

    return permission

@router.get(
    "/platform-permissions/definitions",
    response_model=list[PlatformPermissionDefResponse],
)
async def list_platform_permission_definitions(
    current_user: SuperAdminUser,
):
    return PLATFORM_PERMISSIONS


@router.get(
    "/platform-permissions",
    response_model=list[UserPlatformPermResponse],
)
async def list_user_platform_permissions(
    current_user: SuperAdminUser,
    session: DatabaseSession,
):
    result = await session.execute(
        select(User).where(
            User.deleted_at.is_(None)
        )
    )

    users = result.scalars().all()

    permission_result = await session.execute(
        select(UserPlatformPermission)
    )

    permission_map: dict[uuid.UUID, list[str]] = {}

    for permission in permission_result.scalars().all():
        permission_map.setdefault(
            permission.user_id,
            [],
        ).append(permission.permission_slug)

    return [
        UserPlatformPermResponse(
            user_id=user.id,
            email=user.email,
            full_name=user.full_name,
            platform_role=user.platform_role,
            permissions=permission_map.get(user.id, []),
        )
        for user in users
    ]

@router.put(
    "/platform-permissions/{user_id}",
)
async def update_user_platform_permissions(
    user_id: uuid.UUID,
    body: UpdatePlatformPermissionsRequest,
    current_user: SuperAdminUser,
    session: DatabaseSession,
):
    user = await session.get(User, user_id)

    if not user or user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    valid_slugs = {
        permission["slug"]
        for permission in PLATFORM_PERMISSIONS
    }

    for slug in body.permissions:
        if slug not in valid_slugs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid permission slug: {slug}",
            )

    result = await session.execute(
        select(UserPlatformPermission).where(
            UserPlatformPermission.user_id == user_id
        )
    )

    existing_permissions = {
        permission.permission_slug: permission
        for permission in result.scalars().all()
    }

    requested_permissions = set(body.permissions)

    for slug in requested_permissions:
        if slug not in existing_permissions:
            session.add(
                UserPlatformPermission(
                    user_id=user_id,
                    permission_slug=slug,
                    granted_by=current_user.id,
                )
            )

    for slug, permission in existing_permissions.items():
        if slug not in requested_permissions:
            await session.delete(permission)

    await session.commit()

    return {
        "success": True,
        "message": "Permissions updated.",
    }