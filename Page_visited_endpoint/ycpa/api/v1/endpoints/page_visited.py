import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from ycpa.core.auth.dependencies import get_optional_user
from ycpa.core.database.dependencies import DatabaseSession
from ycpa.repositories.page_visited import PageVisitedRepository
from ycpa.schemas.requests.page_visited import PageVisitedRequest
from ycpa.schemas.responses.page_visited import PageVisitedResponse
from ycpa.services.page_visited import PageVisitedService
from ycpa.core.schemas.responses import SuccessResponse
from ycpa.core.schemas.responses import BaseResponse


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/page_visited",
    tags=["Page_Visited"],
)


@router.post(
    "",
    response_model=BaseResponse[PageVisitedResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Record a page visit",
)
async def create_page_visited(
    request: Request,
    payload: PageVisitedRequest,
    session: DatabaseSession,
    current_user=Depends(get_optional_user),
) -> BaseResponse[PageVisitedResponse]:

    try:
        user_id: uuid.UUID | None = None
        if current_user is not None:
            user_id = current_user.id
        repository = PageVisitedRepository(session)
        service = PageVisitedService(repository)
        page_visit = await service.create_page_visit(
            request=request,
            payload=payload,
            user_id=user_id,
        )
        logger.info(
            "Page visit recorded successfully",
            extra={
                "page_visit_id": str(page_visit.id),
                "page_name": payload.page_name,
                "user_id": (
                    str(user_id)
                    if user_id
                    else None
                ),
            },
        )
        page_visit_response = PageVisitedResponse.model_validate(page_visit)
        return SuccessResponse(
            success=True,
            message= "Page visit recorded Successfully",
            data = page_visit_response
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception(
            "Failed to record page visit",
            extra={
                "page_name": payload.page_name,
                "page_url": payload.page_url,
                "user_id": (
                    str(current_user.id)
                    if current_user is not None
                    else None
                ),
            },
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record page visit.",
        )
