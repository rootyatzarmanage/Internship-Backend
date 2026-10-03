import uuid

from ycpa.models.control_panel import ControlPanel
from ycpa.repositories.control_panel import ControlPanelRepository
from ycpa.schemas.requests.control_panel import ControlPanelCreateRequest, ControlPanelUpdateRequest

class ControlPanelService:
    FIELD_TYPES = {
        1 : "image",
        2 : "text",
        3 : "rich_text"
    }
    def __init__(self,repository : ControlPanelRepository):
        self.repository = repository

    @classmethod
    def validate_field_value(cls,fieldtype:int,value:str|None) -> None:
        if fieldtype not in cls.FIELD_TYPES:
            raise ValueError("Invalid fieldtype. Allowed values are 1, 2, and 3.")
        if value is None:
            return
        if fieldtype == 1:
            if not value.strip():
                raise ValueError("Image field cannot be empty")
        elif fieldtype == 2:
            if "\n" in value or "\r" in value:
                raise ValueError("Single-line text cannot contain line breaks")
        elif fieldtype == 3:
            if not value.strip():
                raise ValueError("Rich text field cannot be empty")

    async def create_control_panel(self,payload: ControlPanelCreateRequest) -> ControlPanel:
        self.validate_field_value(
            payload.fieldtype,
            payload.name_prefix,
        )
        existing = await self.repository.get_control_panel_by_name(payload.name)
        if existing:
            raise ValueError("A control panel with this name already exists")
        control_panel = await self.repository.create_control_panel(
            name = payload.name,
            name_prefix = payload.name_prefix,
            fieldtype = payload.fieldtype
        )
        await self.repository.session.commit()
        return control_panel

    async def get_all_control_panels(self,control_panel_id: uuid.UUID | None = None,name: str | None = None,limit: int = 50,offset: int = 0) -> list[ControlPanel]:
        return await self.repository.get_all_control_panels(
            control_panel_id=control_panel_id,
            name=name,
            limit=limit,
            offset=offset,
        )
    
    async def get_control_panel_by_id(self,control_panel_id: uuid.UUID,) -> ControlPanel | None:
        return await self.repository.get_control_panel_by_id(control_panel_id)

    async def update_control_panel(self,control_panel: ControlPanel,payload: ControlPanelUpdateRequest) -> ControlPanel:
        updates = payload.model_dump(exclude_unset = True)
        new_fieldtype = updates.get("fieldtype",control_panel.fieldtype)
        new_value = updates.get("name_prefix",control_panel.name_prefix)
        self.validate_field_value(new_fieldtype,new_value)
        if "name" in updates:
            existing = await self.repository.get_control_panel_by_name(updates["name"])
            if existing and existing.id != control_panel.id:
                raise ValueError("A control panel with this name already exists")
        updated = await self.repository.update_control_panel(control_panel,updates)
        await self.repository.session.commit()
        await self.repository.session.refresh(updated)
        return updated

    async def delete_control_panel(self,control_panel: ControlPanel) -> None:
        await self.repository.soft_delete_control_panel(control_panel)
        await self.repository.session.commit()

