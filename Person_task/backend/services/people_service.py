from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import ConflictException
from backend.models.person import Person
from backend.repositories.person import PersonRepository
from backend.schemas.requests.people_request import CreatePeopleRequest
from backend.schemas.response.people_response import BulkPersonResponse
from backend.services.base import BaseService

class BulkPersonService(BaseService):
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.repo = PersonRepository(session)

    async def create_people(self,body:CreatePeopleRequest) -> list[BulkPersonResponse]:
        people = []
        for person_data in body.people:
            if await self.repo.name_exists(person_data.name):
                raise ConflictException(f"Person with name '{person_data.name}' already exists")
            new_person = Person(
                name = person_data.name,
                age = person_data.age
            )
            person = await self.repo.create(new_person)
            people.append(person)
        await self.session.commit()
        for person in people:
            await self.session.refresh(person)
        return [
            BulkPersonResponse.model_validate(person)
            for person in people
        ]