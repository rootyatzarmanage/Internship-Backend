import uuid
from pydantic import BaseModel, ConfigDict


class RoleResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    product_type: str
    is_system: bool
    is_editable: bool
    is_active: bool
    created_by_type: str
    workspace_id: uuid.UUID | None

    model_config = ConfigDict(from_attributes=True)


class ModuleResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    product_type: str
    order: int

    model_config = ConfigDict(from_attributes=True)


class SubmoduleResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    order: int

    model_config = ConfigDict(from_attributes=True)


class ModuleWithSubmodules(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    product_type: str
    order: int
    submodules: list[SubmoduleResponse] = []

    model_config = ConfigDict(from_attributes=True)


class PermissionResponse(BaseModel):
    id: uuid.UUID
    role_id: uuid.UUID
    module_id: uuid.UUID
    submodule_id: uuid.UUID | None
    can_view: bool
    can_create: bool
    can_edit: bool
    can_delete: bool
    can_approve: bool
    can_share: bool

    model_config = ConfigDict(from_attributes=True)


class PlatformPermissionDefResponse(BaseModel):
    slug: str
    name: str
    description: str


class UserPlatformPermResponse(BaseModel):
    user_id: uuid.UUID
    email: str
    full_name: str
    platform_role: str
    permissions: list[str]