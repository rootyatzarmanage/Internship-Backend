from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TeamQuery(BaseModel):
    member_id: UUID | None = None
    name: str | None = None
    level_id: int | None = Field(None, ge=1)
    q: str = ""
    sort: Literal["name", "active", "free", "solved"] = "name"
    page: int = Field(1, ge=1)
    per_page: int = Field(8, ge=1, le=100)


class SettingsRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


class LevelCreateRequest(SettingsRequest):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=255)
    sla_hours: int = Field(12, ge=1, le=72)


class LevelSlaUpdateRequest(SettingsRequest):
    sla_hours: int = Field(..., ge=1, le=72)


class MemberCreateRequest(SettingsRequest):
    name: str = Field(..., min_length=1, max_length=100)
    level_id: int = Field(..., ge=1)
    user_id: UUID | None = None


class RulesUpdateRequest(SettingsRequest):
    auto_return: bool | None = None
    notify_super_admin: bool | None = None
    allow_skip_levels: bool | None = None


class CreateLevel(LevelCreateRequest):
    kind: Literal["level"]


class CreateMember(MemberCreateRequest):
    kind: Literal["member"]


class UpdateLevel(LevelSlaUpdateRequest):
    kind: Literal["level"]
    level_id: int = Field(..., ge=1)


class UpdateRules(RulesUpdateRequest):
    kind: Literal["rules"]


SettingsCreateRequest = Annotated[CreateLevel | CreateMember, Field(discriminator="kind")]
SettingsUpdateRequest = Annotated[UpdateLevel | UpdateRules, Field(discriminator="kind")]
