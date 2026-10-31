import logging

from fastapi import APIRouter, Query, status

from ycpa.core.auth.dependencies import SuperAdminUser
from ycpa.core.database.dependencies import DatabaseSession
from ycpa.core.schemas.responses import SuccessResponse
from ycpa.schemas.requests.superadmin_pricing import SaveSuperadminPricingRequest
from ycpa.schemas.responses.superadmin_pricing import ConvertedPricingResponse, SuperadminPricingResponse
from ycpa.services.superadmin_pricing import SuperadminPricingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/superadmin/pricing", tags=["Super Admin - Pricing"])


@router.get(
    "",
    response_model=SuccessResponse[SuperadminPricingResponse],
    status_code=status.HTTP_200_OK,
    summary="Get the pricing page configuration",
)
async def get_pricing(
    current_user: SuperAdminUser,
    session: DatabaseSession,
) -> SuccessResponse[SuperadminPricingResponse]:
    service = SuperadminPricingService(session)
    row = await service.get_pricing()
    if row is None:
        return SuccessResponse(success=True, message="Pricing is not configured yet.", data=None)
    return SuccessResponse(
        success=True,
        message="Pricing retrieved.",
        data=SuperadminPricingResponse.model_validate(row),
    )


@router.post(
    "",
    response_model=SuccessResponse[SuperadminPricingResponse],
    status_code=status.HTTP_200_OK,
    summary="Create or update the pricing page configuration",
)
@router.put(
    "",
    response_model=SuccessResponse[SuperadminPricingResponse],
    status_code=status.HTTP_200_OK,
    summary="Save the pricing page configuration",
)
async def save_pricing(
    body: SaveSuperadminPricingRequest,
    current_user: SuperAdminUser,
    session: DatabaseSession,
) -> SuccessResponse[SuperadminPricingResponse]:
    service = SuperadminPricingService(session)
    row = await service.save_pricing(body, current_user)
    await session.commit()
    return SuccessResponse(
        success=True,
        message="Pricing saved successfully.",
        data=SuperadminPricingResponse.model_validate(row),
    )


@router.get(
    "/convert",
    response_model=SuccessResponse[ConvertedPricingResponse],
    status_code=status.HTTP_200_OK,
    summary="Get the saved prices converted to another currency (Frankfurter rates)",
)
async def convert_pricing(
    current_user: SuperAdminUser,
    session: DatabaseSession,
    to: str = Query(..., pattern=r"^[A-Za-z]{3}$", description="Target ISO 4217 code, e.g. USD"),
) -> SuccessResponse[ConvertedPricingResponse]:
    service = SuperadminPricingService(session)
    result = await service.convert_pricing(to)
    return SuccessResponse(
        success=True,
        message="Pricing converted.",
        data=ConvertedPricingResponse.model_validate(result),
    )
