import logging
from uuid import UUID

from fastapi import APIRouter, Query, status

from ycpa.core.auth.dependencies import SuperAdminUser
from ycpa.core.database.dependencies import DatabaseSession
from ycpa.core.schemas.responses import SuccessResponse
from ycpa.schemas.requests.faq import FaqCreateRequest, FaqUpdateRequest
from ycpa.schemas.responses.faq import FaqListResponse, FaqPublicResponse, FaqResponse
from ycpa.services.faq import FaqService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/faqs", tags=["FAQ"])


@router.get(
    "",
    response_model=SuccessResponse[list[FaqPublicResponse] | FaqPublicResponse],
    status_code=status.HTTP_200_OK,
    summary="List active FAQs or get one by optional FAQ ID (public)",
)
async def list_faqs(
    session: DatabaseSession,
    faq_id: UUID | None = Query(default=None),
) -> SuccessResponse[list[FaqPublicResponse] | FaqPublicResponse]:
    service = FaqService(session)
    if faq_id is not None:
        faq = await service.get_public(faq_id)
        return SuccessResponse(success=True, data=FaqPublicResponse.model_validate(faq))

    faqs = await service.list_public()
    return SuccessResponse(
        success=True,
        data=[FaqPublicResponse.model_validate(f) for f in faqs],
    )


@router.get(
    "/manage",
    response_model=SuccessResponse[FaqListResponse],
    status_code=status.HTTP_200_OK,
    summary="List all FAQs incl. hidden ones (super admin)",
)
async def list_faqs_manage(
    session: DatabaseSession,
    current_user: SuperAdminUser,
    search: str | None = Query(default=None, max_length=100),
    is_active: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=100),
) -> SuccessResponse[FaqListResponse]:
    items, total = await FaqService(session).list_manage(search, is_active, page, per_page)
    return SuccessResponse(
        success=True,
        data=FaqListResponse(
            items=[FaqResponse.model_validate(f) for f in items],
            total=total,
            page=page,
            per_page=per_page,
        ),
    )


@router.post(
    "",
    response_model=SuccessResponse[FaqResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create FAQ (super admin)",
)
async def create_faq(
    body: FaqCreateRequest,
    session: DatabaseSession,
    current_user: SuperAdminUser,
) -> SuccessResponse[FaqResponse]:
    faq = await FaqService(session).create_faq(current_user, body)
    return SuccessResponse(
        success=True,
        message="FAQ created.",
        data=FaqResponse.model_validate(faq),
    )


@router.put(
    "/{faq_id}",
    response_model=SuccessResponse[FaqResponse],
    status_code=status.HTTP_200_OK,
    summary="Update FAQ (super admin)",
)
async def update_faq(
    faq_id: UUID,
    body: FaqUpdateRequest,
    session: DatabaseSession,
    current_user: SuperAdminUser,
) -> SuccessResponse[FaqResponse]:
    faq = await FaqService(session).update_faq(current_user, faq_id, body)
    return SuccessResponse(
        success=True,
        message="FAQ updated.",
        data=FaqResponse.model_validate(faq),
    )


@router.delete(
    "/{faq_id}",
    response_model=SuccessResponse[None],
    status_code=status.HTTP_200_OK,
    summary="Delete FAQ (super admin)",
)
async def delete_faq(
    faq_id: UUID,
    session: DatabaseSession,
    current_user: SuperAdminUser,
) -> SuccessResponse[None]:
    await FaqService(session).delete_faq(current_user, faq_id)
    return SuccessResponse(success=True, message="FAQ deleted.")
