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
    PaymentMetricResponse,
    SuccessfulPaymentResponse,
    MonthlyTransactionResponse,
    YearlyRevenueResponse,
    PaymentMethodResponse,
    PaymentMethodItem,
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

@router.get(
    "/total_revenue",
    response_model=SuccessResponse[PaymentMetricResponse],
    status_code=status.HTTP_200_OK,
    summary="Get total revenue",
)
async def get_total_revenue(
    session: DatabaseSession,
    current_user: SuperAdminUser,
) -> SuccessResponse[PaymentMetricResponse]:

    try:
        repository = AdminPaymentRepository(session)
        service = AdminPaymentService(repository)

        data = await service.get_total_revenue()

        logger.info(
            "Total revenue fetched successfully",
            extra={
                "value": data,
            },
        )

        return SuccessResponse(
            success=True,
            message="Total revenue fetched successfully",
            data=PaymentMetricResponse(
                **data
            ),
        )

    except HTTPException:
        raise

    except Exception:

        logger.exception(
            "Failed to fetch total revenue"
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch total revenue.",
        )


@router.get(
    "/total_transactions",
    response_model=SuccessResponse[PaymentMetricResponse],
    status_code=status.HTTP_200_OK,
    summary="Get total transactions",
)
async def get_total_transactions(
    session: DatabaseSession,
    current_user: SuperAdminUser,
) -> SuccessResponse[PaymentMetricResponse]:

    try:
        repository = AdminPaymentRepository(session)
        service = AdminPaymentService(repository)

        data = await service.get_total_transactions()

        logger.info(
            "Total transactions fetched successfully",
            extra={
                "value": data,
            },
        )

        return SuccessResponse(
            success=True,
            message="Total transactions fetched successfully",
            data=PaymentMetricResponse(
                **data
            ),
        )

    except HTTPException:
        raise

    except Exception:

        logger.exception(
            "Failed to fetch total transactions"
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch total transactions.",
        )

@router.get(
    "/successful_payments",
    response_model=SuccessResponse[SuccessfulPaymentResponse],
    status_code=status.HTTP_200_OK,
    summary="Get successful payments",
)
async def get_successful_payments(
    session: DatabaseSession,
    current_user: SuperAdminUser,
) -> SuccessResponse[SuccessfulPaymentResponse]:

    try:
        repository = AdminPaymentRepository(session)
        service = AdminPaymentService(repository)

        data = await service.get_successful_payments()

        logger.info(
            "Successful payments fetched successfully",
            extra={
                "value": data,
            },
        )

        return SuccessResponse(
            success=True,
            message="Successful payments fetched successfully",
            data=SuccessfulPaymentResponse(
                **data
            ),
        )

    except HTTPException:
        raise

    except Exception:

        logger.exception(
            "Failed to fetch successful payments"
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch successful payments.",
        )


@router.get(
    "/monthly_transaction",
    response_model=SuccessResponse[MonthlyTransactionResponse],
    status_code=status.HTTP_200_OK,
    summary="Get current monthly transactions",
)
async def get_monthly_transaction(
    session: DatabaseSession,
    current_user: SuperAdminUser,
) -> SuccessResponse[MonthlyTransactionResponse]:

    try:
        repository = AdminPaymentRepository(session)
        service = AdminPaymentService(repository)

        data = await service.get_monthly_transaction()

        logger.info(
            "Monthly transaction fetched successfully",
            extra={
                "value": data,
            },
        )

        return SuccessResponse(
            success=True,
            message="Monthly transaction fetched successfully",
            data=MonthlyTransactionResponse(
                **data
            ),
        )

    except HTTPException:
        raise

    except Exception:

        logger.exception(
            "Failed to fetch monthly transaction"
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch monthly transaction.",
        )


@router.get(
    "/yearly_revenue",
    response_model=SuccessResponse[YearlyRevenueResponse],
    status_code=status.HTTP_200_OK,
    summary="Get yearly revenue statistics",
)
async def get_yearly_revenue(
    session: DatabaseSession,
    current_user: SuperAdminUser,
    year: int = Query(
        ...,
        description="Revenue year",
    ),
) -> SuccessResponse[YearlyRevenueResponse]:

    try:
        repository = AdminPaymentRepository(session)
        service = AdminPaymentService(repository)

        data = await service.get_yearly_revenue(
            year=year
        )

        logger.info(
            "Yearly revenue fetched successfully",
            extra={
                "year": year,
            },
        )

        return SuccessResponse(
            success=True,
            message="Yearly revenue fetched successfully",
            data=YearlyRevenueResponse(
                **data
            ),
        )

    except HTTPException:
        raise

    except Exception:

        logger.exception(
            "Failed to fetch yearly revenue",
            extra={
                "year": year,
            },
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch yearly revenue.",
        )

@router.get(
    "/payment_methods",
    response_model=SuccessResponse[PaymentMethodResponse],
    status_code=status.HTTP_200_OK,
    summary="Get payment method distribution",
)
async def get_payment_methods(
    session: DatabaseSession,
    current_user: SuperAdminUser,
) -> SuccessResponse[PaymentMethodResponse]:

    try:
        repository = AdminPaymentRepository(session)
        service = AdminPaymentService(repository)

        devices = await service.get_payment_methods()

        logger.info(
            "Payment methods fetched successfully",
            extra={
                "payment_methods_count": len(
                    devices
                ),
            },
        )

        data = PaymentMethodResponse(
            payment_methods=[
                PaymentMethodItem(
                    **item
                )
                for item in devices
            ]
        )

        return SuccessResponse(
            success=True,
            message="Payment methods fetched successfully",
            data=data,
        )

    except HTTPException:
        raise

    except Exception:

        logger.exception(
            "Failed to fetch payment methods"
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch payment methods.",
        )