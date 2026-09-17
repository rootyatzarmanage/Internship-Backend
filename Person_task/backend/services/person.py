from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import ConflictException
from backend.models.person import Person
from backend.repositories.person import PersonRepository
from backend.schemas.requests.person import CreatePersonRequest
from backend.schemas.response.person import PersonResponse 
from backend.services.base import BaseService


class PersonService(BaseService):
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.repo = PersonRepository(session)

    async def create_person(self, body: CreatePersonRequest) -> PersonResponse:
        if await self.repo.name_exists(body.name):
            raise ConflictException(f"Person with name '{body.name}' already exists")
        new_person = Person(
            name=body.name,
            age=body.age,
        )
        person = await self.repo.create(new_person)
        await self.session.commit()
        await self.session.refresh(person)
        return PersonResponse.model_validate(person)


