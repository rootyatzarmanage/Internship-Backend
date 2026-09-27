import logging
import calendar
from datetime import datetime, timezone

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


    @staticmethod
    def _get_current_month_range():

        now = datetime.now(timezone.utc)

        current_start = datetime(
            now.year,
            now.month,
            1,
            tzinfo=timezone.utc,
        )

        if now.month == 12:
            next_month = datetime(
                now.year + 1,
                1,
                1,
                tzinfo=timezone.utc,
            )
        else:
            next_month = datetime(
                now.year,
                now.month + 1,
                1,
                tzinfo=timezone.utc,
            )

        return current_start, next_month

    @staticmethod
    def _get_previous_month_range():

        now = datetime.now(timezone.utc)

        current_month_start = datetime(
            now.year,
            now.month,
            1,
            tzinfo=timezone.utc,
        )

        if now.month == 1:

            previous_start = datetime(
                now.year - 1,
                12,
                1,
                tzinfo=timezone.utc,
            )

        else:

            previous_start = datetime(
                now.year,
                now.month - 1,
                1,
                tzinfo=timezone.utc,
            )

        return previous_start, current_month_start

    @staticmethod
    def _calculate_percentage_change(
        current_value: float,
        previous_value: float,
    ) -> float:

        if previous_value == 0:

            if current_value == 0:
                return 0.0

            return 100.0

        return round(
            (
                (current_value - previous_value)
                / previous_value
            )
            * 100,
            2,
        )

    async def get_total_revenue(self) -> dict:

        total_revenue = (await self.repository.get_total_revenue())

        current_start, current_end = (
            self._get_current_month_range()
        )

        previous_start, previous_end = (
            self._get_previous_month_range()
        )

        current_month_revenue = (
            await self.repository.get_revenue_between(
                current_start,
                current_end,
            )
        )

        previous_month_revenue = (
            await self.repository.get_revenue_between(
                previous_start,
                previous_end,
            )
        )

        percentage_change = (
            self._calculate_percentage_change(
                current_month_revenue,
                previous_month_revenue,
            )
        )

        return {
            "value": total_revenue,
            "percentage_change": percentage_change,
        }

    async def get_total_transactions(self) -> dict:

        total_transactions = (
            await self.repository.get_total_transactions()
        )

        current_start, current_end = (
            self._get_current_month_range()
        )

        previous_start, previous_end = (
            self._get_previous_month_range()
        )

        current_month_transactions = (
            await self.repository.get_transactions_between(
                current_start,
                current_end,
            )
        )

        previous_month_transactions = (
            await self.repository.get_transactions_between(
                previous_start,
                previous_end,
            )
        )

        percentage_change = (
            self._calculate_percentage_change(
                current_month_transactions,
                previous_month_transactions,
            )
        )

        return {
            "value": total_transactions,
            "percentage_change": percentage_change,
        }
    
    async def get_successful_payments(self) -> dict:

        total_successful_payments = (
            await self.repository.get_successful_payments()
        )

        current_start, current_end = (
            self._get_current_month_range()
        )

        previous_start, previous_end = (
            self._get_previous_month_range()
        )

        current_successful = (
            await self.repository.get_successful_payments_between(
                current_start,
                current_end,
            )
        )

        current_transactions = (
            await self.repository.get_transactions_between(
                current_start,
                current_end,
            )
        )

        previous_successful = (
            await self.repository.get_successful_payments_between(
                previous_start,
                previous_end,
            )
        )

        previous_transactions = (
            await self.repository.get_transactions_between(
                previous_start,
                previous_end,
            )
        )

        if current_transactions == 0:
            current_success_rate = 0.0
        else:
            current_success_rate = (
                current_successful
                / current_transactions
            ) * 100

        if previous_transactions == 0:
            previous_success_rate = 0.0
        else:
            previous_success_rate = (
                previous_successful
                / previous_transactions
            ) * 100

        percentage_change = (
            self._calculate_percentage_change(
                current_success_rate,
                previous_success_rate,
            )
        )

        return {
            "value": total_successful_payments,
            "percentage_change": percentage_change,
        }

    async def get_monthly_transaction(self) -> dict:

        current_start, current_end = (
            self._get_current_month_range()
        )

        previous_start, previous_end = (
            self._get_previous_month_range()
        )

        current_transactions = (
            await self.repository.get_monthly_transactions(
                current_start,
                current_end,
            )
        )

        previous_transactions = (
            await self.repository.get_monthly_transactions(
                previous_start,
                previous_end,
            )
        )

        percentage_change = (
            self._calculate_percentage_change(
                current_transactions,
                previous_transactions,
            )
        )

        return {
            "value": current_transactions,
            "percentage_change": percentage_change,
        }

    async def get_yearly_revenue(
        self,
        year: int,
    ) -> dict:

        rows = await self.repository.get_yearly_revenue(
            year
        )

        months = [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ]

        monthly_data = {}

        for month in range(1, 13):

            monthly_data[month] = {
                "month": months[month - 1],
                "pim_project": 0.0,
                "aim_project": 0.0,
                "pim_aim_project": 0.0,
            }

        for row in rows:

            month_number = int(row.month)

            product_type = (
                row.product_type or ""
            ).strip().lower()

            revenue = float(
                row.revenue or 0
            )

            if product_type == "pim":

                monthly_data[
                    month_number
                ]["pim_project"] += revenue

            elif product_type == "aim":

                monthly_data[
                    month_number
                ]["aim_project"] += revenue

            elif product_type in (
                "pim + aim",
                "pim+aim",
            ):

                monthly_data[
                    month_number
                ]["pim_aim_project"] += revenue

        months_data = list(
            monthly_data.values()
        )

        total_revenue = sum(
            month["pim_project"]
            + month["aim_project"]
            + month["pim_aim_project"]
            for month in months_data
        )

        return {
            "year": year,
            "total_revenue": round(
                total_revenue,
                2,
            ),
            "months": months_data,
        }

    async def get_payment_methods(self) -> list[dict]:

        rows = (
            await self.repository.get_payment_methods()
        )

        return [
            {
                "payment_method": (
                    payment_method
                    if payment_method
                    else "Unknown"
                ),
                "count": count,
            }
            for payment_method, count in rows
        ]