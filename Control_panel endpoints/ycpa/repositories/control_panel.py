import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ycpa.models.control_panel import ControlPanel
from ycpa.repositories.base import BaseRepository

class ControlPanelRepository(BaseRepository):
    def __init__(self,session: AsyncSession):
        super().__init__(ControlPanel, session)

    async def create_control_panel(
            self,
            *,
            name: str,
            name_prefix: str | None = None,
            fieldtype: int
    )-> ControlPanel:
        control_panel = ControlPanel(
            name=name,
            name_prefix=name_prefix,
            fieldtype=fieldtype
        )
        self.session.add(control_panel)
        await self.session.flush()
        await self.session.refresh(control_panel)
        return control_panel
    
    async def get_all_control_panels(self,control_panel_id: uuid.UUID | None = None,name: str | None = None,limit: int = 50,offset: int = 0,) -> list[ControlPanel]:
        query = select(ControlPanel).where(ControlPanel.deleted_at.is_(None))
        if control_panel_id is not None:
            query = query.where(ControlPanel.id == control_panel_id)

        if name:
            query = query.where(ControlPanel.name.ilike(f"{name}%"))
        query = (
            query
            .order_by(ControlPanel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_control_panel_by_id(self,control_panel_id:uuid.UUID) -> ControlPanel | None:
        query = select(ControlPanel).where(
            ControlPanel.id == control_panel_id,
            ControlPanel.deleted_at.is_(None)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()  

    async def get_control_panel_by_name(self,name:str) -> ControlPanel | None:
        query = select(ControlPanel).where(
            ControlPanel.name == name,
            ControlPanel.deleted_at.is_(None)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update_control_panel(
            self,
            control_panel : ControlPanel,
            values : dict
    )-> ControlPanel:
        for field,value in values.items():
            setattr(control_panel,field,value)
        control_panel.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.refresh(control_panel)
        return control_panel

    async def soft_delete_control_panel(self,control_panel: ControlPanel) -> ControlPanel:
        control_panel.deleted_at = datetime.now(timezone.utc)
        control_panel.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        return control_panel
    