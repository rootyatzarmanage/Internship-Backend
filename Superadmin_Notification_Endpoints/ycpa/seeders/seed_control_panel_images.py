"""Seed the three image fields in the control panel's Images section.

Run from the project root:
    venv/bin/python -m ycpa.seeders.seed_control_panel_images

Existing entries and uploaded image URLs are preserved on subsequent runs.
New entries have value=None until an image is uploaded.
"""

import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from ycpa.core.database.engine import engine
from ycpa.core.database.session import AsyncSessionLocal
from ycpa.repositories.control_panel import ControlPanelRepository


IMAGE_FIELDS = (
    ("Images/Site-Logo", "Site Logo"),
    ("Images/Invoice-Logo", "Invoice Logo"),
    ("Images/Invoice-Sign", "Invoice Sign"),
)


async def seed_control_panel_images(session: AsyncSession) -> None:
    repository = ControlPanelRepository(session)
    for slug, name in IMAGE_FIELDS:
        existing = await repository.get_control_panel_by_slug(slug, include_deleted=True)
        if existing is not None:
            status = "SKIP (soft-deleted)" if existing.deleted_at is not None else "SKIP"
            print(f"{status}  {slug}  id={existing.id}")
            continue

        entry = await repository.create_control_panel(
            slug=slug,
            name=name,
            fieldtype=1,
            name_prefix=None,
            value=None,
            value_json=None,
        )
        print(f"CREATE  {slug}  id={entry.id}")


async def main() -> None:
    try:
        async with AsyncSessionLocal() as session:
            async with session.begin():
                await seed_control_panel_images(session)
        print("Control panel image fields seeded successfully.")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
