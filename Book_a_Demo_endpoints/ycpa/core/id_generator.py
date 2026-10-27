from sqlalchemy import event, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from ycpa.models.control_panel import ControlPanel, IdCounter
from ycpa.models.enquiry import BookDemo, ContactInformation
from ycpa.models.order import Order
from ycpa.models.subscription import SubscriptionPlan
from ycpa.models.tickets import Ticket
from ycpa.models.user import User
from ycpa.models.workspace import AimProject, AimWorkspace, PimProject, PimWorkspace


ID_TARGETS = {
    "ID-Configuration/Workspace":           [(PimWorkspace, "workspace_id"), (AimWorkspace, "workspace_id")],
    "ID-Configuration/Project":             [(PimProject, "project_id"), (AimProject, "project_id")],
    "ID-Configuration/Registered-User":     [(User, "user_id")],
    "ID-Configuration/Invoice":             [(Order, "invoice_id")],
    "ID-Configuration/Offering":            [(SubscriptionPlan, "offering_id")],
    "ID-Configuration/Ticket":              [(Ticket, "ticket_id")],
    "ID-Configuration/Contact-Information": [(ContactInformation, "contact_id")],
    "ID-Configuration/Book-a-Demo":         [(BookDemo, "book_demo_id")],
}

DEFAULT_PREFIX = {
    "ID-Configuration/Workspace": "W", "ID-Configuration/Project": "P", "ID-Configuration/Registered-User": "U",
    "ID-Configuration/Invoice": "I", "ID-Configuration/Offering": "O", "ID-Configuration/Ticket": "T",
    "ID-Configuration/Contact-Information": "C", "ID-Configuration/Book-a-Demo": "B",
}
_BY_MODEL = {model: (slug, col) for slug, targets in ID_TARGETS.items() for model, col in targets}


def format_id(prefix: str, n: int) -> str:
    block, num = divmod(n - 1, 999)          
    letters, i = "", block
    for _ in range(2):                       
        i, r = divmod(i, 26)
        letters = chr(65 + r) + letters
    while i:                                  
        i, r = divmod(i - 1, 26)
        letters = chr(65 + r) + letters
    return f"{prefix}{letters}-{num + 1:03d}"


@event.listens_for(Session, "before_flush")
def _assign_ids(session, flush_context, instances):
    for obj in list(session.new):
        spec = _BY_MODEL.get(type(obj))
        if spec is None:
            continue
        slug, col = spec
        if getattr(obj, col, None):
            continue
        with session.no_autoflush:
            session.execute(pg_insert(IdCounter).values(slug=slug, last_number=0)
                            .on_conflict_do_nothing(index_elements=["slug"]))
            n = session.execute(
                update(IdCounter).where(IdCounter.slug == slug)
                .values(last_number=IdCounter.last_number + 1).returning(IdCounter.last_number),
                execution_options={"synchronize_session": False},
            ).scalar_one()
            prefix = session.execute(
                select(ControlPanel.name_prefix).where(ControlPanel.slug == slug, ControlPanel.deleted_at.is_(None))
            ).scalar_one_or_none() or DEFAULT_PREFIX[slug]
        setattr(obj, col, format_id(prefix.strip().upper(), n))


async def renumber(session: AsyncSession, slug: str, prefix: str, only_missing: bool = False) -> int:
    await session.flush()
    await session.execute(pg_insert(IdCounter).values(slug=slug, last_number=0)
                          .on_conflict_do_nothing(index_elements=["slug"]))
    last = (await session.execute(
        select(IdCounter.last_number).where(IdCounter.slug == slug).with_for_update())).scalar_one()
    rows = []
    for model, col in ID_TARGETS[slug]:
        q = select(model)
        if only_missing:
            q = q.where(getattr(model, col).is_(None))
        rows += [(r.created_at, str(r.id), r, col) for r in (await session.execute(q)).scalars()]
    rows.sort(key=lambda x: (x[0], x[1]))
    n = last if only_missing else 0
    for _, _, obj, col in rows:
        n += 1
        setattr(obj, col, format_id(prefix, n))
    await session.execute(update(IdCounter).where(IdCounter.slug == slug).values(last_number=n))
    await session.flush()
    return n


async def backfill_all_ids(session: AsyncSession) -> None:
    for slug in ID_TARGETS:
        prefix = await session.scalar(select(ControlPanel.name_prefix).where(
            ControlPanel.slug == slug, ControlPanel.deleted_at.is_(None))) or DEFAULT_PREFIX[slug]
        await renumber(session, slug, prefix.strip().upper(), only_missing=True)
    await session.commit()
