from fastapi import APIRouter, status

from backend.core.database.dependencies import DatabaseSession
from backend.core.schemas.responses import SuccessResponse

from backend.schemas.requests.person import CreatePersonRequest
from backend.schemas.response.person import PersonResponse
from backend.schemas.requests.people_request import CreatePeopleRequest
from backend.schemas.response.people_response import BulkPersonResponse
from backend.services.person import PersonService
from backend.services.people_service import BulkPersonService

person_router = APIRouter(
    prefix = "/person",
    tags = ["Person"]
)

@person_router.post(
    "",
    response_model = SuccessResponse[PersonResponse],
    status_code = status.HTTP_201_CREATED,
)
async def create_person(
    body : CreatePersonRequest,
    session : DatabaseSession
)-> SuccessResponse[PersonResponse]:
    service = PersonService(session)
    data = await service.create_person(
        body
    )
    return SuccessResponse(
        success = True,
        message = "Person Created",
        data = data 
    )

@person_router.post(
    "/bulk",
    response_model = SuccessResponse[list[BulkPersonResponse]],
    status_code = status.HTTP_201_CREATED
)
async def create_people(
    body : CreatePeopleRequest,
    session : DatabaseSession,
)-> SuccessResponse[list[BulkPersonResponse]]:
    service = BulkPersonService(session)
    data = await service.create_people(
        body
    )
    return SuccessResponse(
        success = True,
        message = "Person Created",
        data = data
    )

