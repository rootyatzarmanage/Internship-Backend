import logging

from ycpa.models.order import Order
from ycpa.models.user import User
from ycpa.repositories.admin_payment import AdminPaymentRepository
from ycpa.schemas.responses.admin_payment import (
    AdminPaymentItemResponse,
    AdminPaymentResponse,
)

logger = logging.getLogger(__name__)


class AdminPaymentService:

    def __init__(
        self,
        repository: AdminPaymentRepository,
    ):
        self.repository = repository

    async def get_payments(
        self,
        search: str | None = None,
        start_date=None,
        end_date=None,
        payment_status: str | None = None,
        payment_method: str | None = None,
    ) -> AdminPaymentResponse:

        rows = await self.repository.get_payments(
            search=search,
            start_date=start_date,
            end_date=end_date,
            payment_status=payment_status,
            payment_method=payment_method,
        )

        items = []

        for order, user in rows:
            items.append(
                AdminPaymentItemResponse(
                    sales_no=order.razorpay_order_id,
                    plan=order.plan,
                    user_id=user.id,
                    user_name=user.full_name,
                    user_email=user.email,
                    amount=order.amount,
                    currency=order.currency,
                    payment_method=self._format_payment_method(order.payment_method),
                    payment_status=self._format_payment_status(order.status),
                    date=order.created_at,
                )
            )

        return AdminPaymentResponse(
            items=items,
            total=len(items),
        )

    @staticmethod
    def _format_payment_method(
        payment_method: str | None,
    ) -> str | None:

        if not payment_method:
            return None

        value = payment_method.strip().lower()

        payment_method_map = {
            "upi": "UPI",
            "card": "Card",
            "netbanking": "Net Banking",
            "wallet": "Wallet",
            "emi": "EMI",
            "paylater": "Pay Later",
            "bank_transfer": "Bank Transfer",
            "emandate": "E-Mandate",
            "cardless_emi": "Cardless EMI",
            "ach": "ACH Transfer",
            "apple_pay": "Apple Pay",
        }

        return payment_method_map.get(
            value,
            payment_method,
        )

    @staticmethod
    def _format_payment_status(
        status: str | None,
    ) -> str:

        if not status:
            return "In Process"

        value = status.strip().lower()

        status_map = {
            "paid": "Success",
            "captured": "Success",
            "success": "Success",
            "failed": "Failed",
            "failure": "Failed",
            "created": "In Process",
            "processing": "In Process",
            "inprocess": "In Process",
        }

        return status_map.get(
            value,
            status,
        )