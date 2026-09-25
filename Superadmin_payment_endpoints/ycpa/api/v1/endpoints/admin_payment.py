import logging
from datetime import date

from fastapi import APIRouter, HTTPException, Query, status

from ycpa.core.auth.dependencies import SuperAdminUser
from ycpa.core.database.dependencies import DatabaseSession
from ycpa.core.schemas.responses import SuccessResponse

from ycpa.repositories.admin_payment import AdminPaymentRepository

from ycpa.schemas.responses.admin_payment import (
    AdminPaymentResponse,
    PaymentMethod,
    PaymentStatus,
)

from ycpa.services.admin_payment import AdminPaymentService

logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/admin_payment",
    tags=["Admin Payment"],
)


@router.get(
    "",
    response_model=SuccessResponse[AdminPaymentResponse],
    status_code=status.HTTP_200_OK,
    summary="Get admin payment records",
)
async def get_admin_payments(
    session: DatabaseSession,
    current_user: SuperAdminUser,
    search: str | None = Query(
        None,
        description="Search by user ID, plan, or amount",
    ),
    start_date: date | None = Query(
        None,
        description="Filter payments from this date",
    ),

    end_date: date | None = Query(
        None,
        description="Filter payments up to this date",
    ),

    payment_status: PaymentStatus | None = Query(
        None,
        description="Filter by payment status",
    ),

    payment_method: PaymentMethod | None = Query(
        None,
        description="Filter by payment method",
    ),
) -> SuccessResponse[AdminPaymentResponse]:

    try:
        repository = AdminPaymentRepository(session)
        service = AdminPaymentService(repository)
        data = await service.get_payments(
            search=search,
            start_date=start_date,
            end_date=end_date,
            payment_status=(
                payment_status.value
                if payment_status
                else None
            ),
            payment_method=(
                payment_method.value
                if payment_method
                else None
            ),
        )
        logger.info(
            "Admin payment records fetched successfully",
            extra={
                "search": search,
                "start_date": (
                    str(start_date)
                    if start_date
                    else None
                ),
                "end_date": (
                    str(end_date)
                    if end_date
                    else None
                ),
                "payment_status": (
                    payment_status.value
                    if payment_status
                    else None
                ),
                "payment_method": (
                    payment_method.value
                    if payment_method
                    else None
                ),
                "total": data.total,
            },
        )
        return SuccessResponse(
            success=True,
            message="Payment records fetched successfully",
            data=data,
        )

    except HTTPException:
        raise

    except Exception:

        logger.exception(
            "Failed to fetch admin payment records",
            extra={
                "search": search,
                "start_date": (
                    str(start_date)
                    if start_date
                    else None
                ),
                "end_date": (
                    str(end_date)
                    if end_date
                    else None
                ),
            },
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch payment records.",
        )