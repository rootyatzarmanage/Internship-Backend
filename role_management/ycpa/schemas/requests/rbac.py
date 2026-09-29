import uuid
from pydantic import BaseModel, Field


class PermissionFlags(BaseModel):
    can_view: bool = False
    can_create: bool = False
    can_edit: bool = False
    can_delete: bool = False
    can_approve: bool = False
    can_share: bool = False


class CreateRoleRequest(BaseModel):
    name: str
    description: str | None = None
    product_type: str
    workspace_id: uuid.UUID | None = None


class UpdateRoleRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


class UpsertPermissionRequest(BaseModel):
    module_id: uuid.UUID
    submodule_id: uuid.UUID | None = None
    can_view: bool = False
    can_create: bool = False
    can_edit: bool = False
    can_delete: bool = False
    can_approve: bool = False
    can_share: bool = False


class UpdatePlatformPermissionsRequest(BaseModel):
    permissions: list[str] = Field(default_factory=list)