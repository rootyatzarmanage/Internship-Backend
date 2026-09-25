import logging
from datetime import date

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ycpa.models.order import Order
from ycpa.models.user import User

logger = logging.getLogger(__name__)


class AdminPaymentRepository:

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def get_payments(
        self,
        search: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        payment_status: str | None = None,
        payment_method: str | None = None,
    ) -> list[tuple[Order, User]]:

        query = (select(
                Order,
                User,
            ).join(
                User,
                User.id == Order.user_id,
            ).where(
                User.deleted_at.is_(None),
            )
        )

        if search:
            search_value = search.strip()

            search_conditions = [
                User.id.cast(str).ilike(
                    f"%{search_value}%"
                ),
                Order.plan.ilike(
                    f"%{search_value}%"
                ),
                Order.amount.cast(str).ilike(
                    f"%{search_value}%"
                ),
            ]

            query = query.where(
                or_(*search_conditions)
            )
        if start_date:
            query = query.where(
                Order.created_at >= start_date
            )

        if end_date:
            query = query.where(
                Order.created_at
                < end_date.fromordinal(
                    end_date.toordinal() + 1
                )
            )

        if payment_status:
            query = query.where(
                Order.status.ilike(payment_status)
            )

        if payment_method:
            query = query.where(
                Order.payment_method.ilike(payment_method)
            )
        query = query.order_by(
            Order.created_at.desc()
        )

        result = await self.session.execute(query)

        return result.all()