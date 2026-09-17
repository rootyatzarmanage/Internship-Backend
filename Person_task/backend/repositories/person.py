from uuid import UUID
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.person import Person 
from backend.repositories.base import BaseRepository

class PersonRepository(BaseRepository[Person]):
    def __init__(self, session: AsyncSession):
        super().__init__(Person, session)
    async def get_by_name(self, name: str) -> Person | None:
        result = await self.session.execute(
            select(Person).where(
                Person.name == name,
                Person.deleted_at.is_(None), 
            )
        )
        return result.scalar_one_or_none()
    
    async def name_exists(self, name: str) -> bool:
        return (await self.get_by_name(name)) is not None

    async def list_all(
        self, age: int | None = None, limit: int = 50, offset: int = 0
    ) -> list[Person]:
        stmt = select(Person).where(Person.deleted_at.is_(None))
        if age is not None:
            stmt = stmt.where(Person.age == age)
        stmt = stmt.order_by(Person.name.asc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_all(self, age: int | None = None) -> int:
        stmt = select(func.count()).select_from(Person).where(Person.deleted_at.is_(None))
        if age is not None:
            stmt = stmt.where(Person.age == age)
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def update_age(self, person_id: UUID, new_age: int) -> None:
        await self.session.execute(
            update(Person)
            .where(Person.id == person_id)
            .values(age=new_age)
        )
        await self.session.flush()
