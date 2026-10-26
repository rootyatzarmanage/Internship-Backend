import re
import uuid

from ycpa.core.id_generator import DEFAULT_PREFIX, ID_TARGETS, renumber
from ycpa.models.control_panel import ControlPanel
from ycpa.repositories.control_panel import ControlPanelRepository
from ycpa.schemas.requests.control_panel import (
    ControlPanelBulkRequest, ControlPanelCreateRequest, ControlPanelUpdateRequest, MailValue,
)


class ControlPanelService:
    FIELD_TYPES = {1: "image", 2: "text", 3: "rich_text", 4: "id_configuration", 5: "mail", 6: "number"}

    def __init__(self, repository: ControlPanelRepository):
        self.repository = repository

    @classmethod
    def clean_values(cls, slug: str, fieldtype: int, name_prefix, value, value_json) -> dict:
        if fieldtype not in cls.FIELD_TYPES:
            raise ValueError("Invalid fieldtype. Allowed values are 1 to 6.")
        out = {"name_prefix": None, "value": None, "value_json": None}
        if fieldtype == 4:
            prefix = (name_prefix or "").strip().upper()
            if not re.fullmatch(r"[A-Z0-9]{1,10}", prefix):
                raise ValueError("ID prefix must be 1-10 letters or numbers")
            if slug not in ID_TARGETS:
                raise ValueError(f"No ID target is registered for '{slug}'")
            out["name_prefix"] = prefix
        elif fieldtype == 5:
            mail = MailValue.model_validate(value_json or {})
            main = str(mail.email).lower() if mail.email else None
            cc = list(dict.fromkeys(str(c).lower() for c in mail.cc if str(c).lower() != main))
            out["value_json"] = {"email": main, "cc": cc}
        else:
            if value is not None:
                if fieldtype in (1, 3) and not value.strip():
                    raise ValueError("Value cannot be empty")
                if fieldtype == 2 and ("\n" in value or "\r" in value):
                    raise ValueError("Single-line text cannot contain line breaks")
                if fieldtype == 6:
                    try:
                        ok = float(value) >= 0
                    except ValueError:
                        ok = False
                    if not ok:
                        raise ValueError("Value must be a non-negative number")
            out["value"] = value
        return out

    async def _apply(self, slug: str, name: str, fieldtype: int, data: dict) -> ControlPanel:
        cols = self.clean_values(slug, fieldtype, data.get("name_prefix"), data.get("value"), data.get("value_json"))
        existing = await self.repository.get_control_panel_by_slug(slug, include_deleted=True)
        if existing is None:
            old_prefix = DEFAULT_PREFIX.get(slug)
            obj = await self.repository.create_control_panel(slug=slug, name=name, fieldtype=fieldtype, **cols)
        else:
            old_prefix = existing.name_prefix or DEFAULT_PREFIX.get(slug)
            obj = await self.repository.update_control_panel(
                existing, {"name": name, "fieldtype": fieldtype, "deleted_at": None, **cols})
        if fieldtype == 4 and cols["name_prefix"] != old_prefix:
            await renumber(self.repository.session, slug, cols["name_prefix"])
        return obj

    async def create_control_panel(self, payload: ControlPanelCreateRequest) -> ControlPanel:
        if await self.repository.get_control_panel_by_slug(payload.slug):
            raise ValueError("A control panel entry with this slug already exists")
        obj = await self._apply(payload.slug, payload.name, payload.fieldtype, payload.model_dump())
        await self.repository.session.commit()
        return obj

    async def bulk_upsert(self, payload: ControlPanelBulkRequest) -> list[ControlPanel]:
        result = []
        for item in payload.items:
            result.append(await self._apply(item.slug, item.name, item.fieldtype, item.model_dump()))
        await self.repository.session.commit()
        return result

    async def get_all_control_panels(self, control_panel_id: uuid.UUID | None = None, name: str | None = None,
                                     slug: str | None = None, limit: int = 50, offset: int = 0) -> list[ControlPanel]:
        return await self.repository.get_all_control_panels(
            control_panel_id=control_panel_id, name=name, slug=slug, limit=limit, offset=offset)

    async def get_control_panel_by_id(self, control_panel_id: uuid.UUID) -> ControlPanel | None:
        return await self.repository.get_control_panel_by_id(control_panel_id)

    async def get_control_panel_by_slug(self, slug: str) -> ControlPanel | None:
        return await self.repository.get_control_panel_by_slug(slug)

    async def update_control_panel(self, control_panel: ControlPanel, payload: ControlPanelUpdateRequest) -> ControlPanel:
        u = payload.model_dump(exclude_unset=True)
        merged = {
            "name_prefix": u.get("name_prefix", control_panel.name_prefix),
            "value": u.get("value", control_panel.value),
            "value_json": u.get("value_json", control_panel.value_json),
        }
        updated = await self._apply(control_panel.slug, u.get("name", control_panel.name),
                                    u.get("fieldtype", control_panel.fieldtype), merged)
        await self.repository.session.commit()
        return updated

    async def delete_control_panel(self, control_panel: ControlPanel) -> None:
        await self.repository.soft_delete_control_panel(control_panel)
        await self.repository.session.commit()
