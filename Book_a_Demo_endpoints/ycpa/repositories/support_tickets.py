from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ycpa.models.tickets import Ticket
from ycpa.models.workspace import (
    AimProject, AimProjectMember, AimWorkspace,
    PimProject, PimProjectMember, PimWorkspace,
)
from ycpa.repositories.base import BaseRepository

_PRODUCTS = (
    ("pim", PimProject, PimWorkspace, PimProjectMember),
    ("aim", AimProject, AimWorkspace, AimProjectMember),
)


class SupportTicketRepository(BaseRepository[Ticket]):
    def __init__(self, session: AsyncSession):
        super().__init__(Ticket, session)

    async def list_user_projects(self, user_id: UUID, q: str | None = None, limit: int = 50) -> list[dict]:
        cards: list[dict] = []
        for ptype, P, W, M in _PRODUCTS:
            stmt = (
                select(P, W.name)
                .join(W, W.id == P.workspace_id)
                .where(
                    P.deleted_at.is_(None),
                    or_(W.owner_id == user_id, P.id.in_(select(M.project_id).where(M.user_id == user_id))),
                )
                .order_by(P.created_at.desc())
                .limit(limit)
            )
            if q:
                stmt = stmt.where(P.name.ilike(f"%{q}%"))
            for p, ws_name in (await self.session.execute(stmt)).all():
                cards.append(dict(
                    id=p.id, name=p.name, description=p.description, thumbnail_url=p.thumbnail_url,
                    product_type=ptype, workspace_id=p.workspace_id, workspace_name=ws_name, created_at=p.created_at,
                ))
        cards.sort(key=lambda c: c["created_at"], reverse=True)
        return cards[:limit]

    async def list_by_user(self, user_id: UUID, page: int, per_page: int) -> tuple[list[Ticket], int]:
        cond = (Ticket.user_id == user_id, Ticket.deleted_at.is_(None))
        total = (await self.session.execute(select(func.count(Ticket.id)).where(*cond))).scalar() or 0
        rows = await self.session.execute(
            select(Ticket).where(*cond).order_by(Ticket.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
        )
        return list(rows.scalars().all()), total
