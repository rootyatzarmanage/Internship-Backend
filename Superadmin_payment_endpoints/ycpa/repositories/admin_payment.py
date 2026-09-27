import logging
from datetime import date, timedelta, datetime

from sqlalchemy import String, cast, or_, select, func
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

        query = (
            select(
                Order,
                User,
            )
            .join(
                User,
                User.id == Order.user_id,
            )
            .where(
                User.deleted_at.is_(None),
            )
        )
        if search:
            search_value = search.strip()

            search_conditions = [
                cast(User.id, String).ilike(
                    f"%{search_value}%"
                ),
                Order.plan.ilike(
                    f"%{search_value}%"
                ),
                cast(Order.amount, String).ilike(
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
            next_day = end_date + timedelta(days=1)

            query = query.where(
                Order.created_at < next_day
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

    async def get_total_revenue(self) -> float:

        query = select(
            func.coalesce(
                func.sum(Order.amount),
                0,
            )
        ).where(
            func.lower(Order.status) == "success"
        )

        result = await self.session.execute(query)
        return float(result.scalar() or 0)

    async def get_revenue_between(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> float:

        query = select(
            func.coalesce(
                func.sum(Order.amount),
                0,
            )
        ).where(
            func.lower(Order.status) == "success",
            Order.created_at >= start_date,
            Order.created_at < end_date,
        )

        result = await self.session.execute(query)
        return float(result.scalar() or 0)
    
    async def get_total_transactions(self) -> int:

        query = select(func.count(Order.id))

        result = await self.session.execute(query)
        return int(result.scalar() or 0)

    async def get_transactions_between(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> int:

        query = select(
            func.count(Order.id)
        ).where(
            Order.created_at >= start_date,
            Order.created_at < end_date,
        )

        result = await self.session.execute(query)
        return int(result.scalar() or 0)
    
    async def get_successful_payments(self) -> int:

        query = select(func.count(Order.id)).where(
            func.lower(Order.status) == "success"
        )

        result = await self.session.execute(query)
        return int(result.scalar() or 0)

    async def get_successful_payments_between(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> int:

        query = select(func.count(Order.id)).where(
            func.lower(Order.status) == "success",
            Order.created_at >= start_date,
            Order.created_at < end_date,
        )

        result = await self.session.execute(query)
        return int(result.scalar() or 0)

    async def get_monthly_transactions(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> int:

        query = select(
            func.count(Order.id)
        ).where(
            Order.created_at >= start_date,
            Order.created_at < end_date,
        )

        result = await self.session.execute(query)
        return int(result.scalar() or 0)

    async def get_yearly_revenue(
        self,
        year: int,
    ) -> list:

        query = select(
            func.extract(
                "month",
                Order.created_at,
            ).label("month"),

            Order.product_type,

            func.coalesce(
                func.sum(Order.amount),
                0,
            ).label("revenue"),
        ).where(
            func.extract(
                "year",
                Order.created_at,
            ) == year,

            func.lower(Order.status) == "success",
        ).group_by(
            func.extract(
                "month",
                Order.created_at,
            ),
            Order.product_type,
        ).order_by(
            func.extract(
                "month",
                Order.created_at,
            )
        )

        result = await self.session.execute(query)
        return result.all()

    async def get_payment_methods(self) -> list:

        query = select(
            Order.payment_method,
            func.count(Order.id).label("count"),
        ).where(
            Order.payment_method.is_not(None),
        ).group_by(
            Order.payment_method,
        ).order_by(
            func.count(Order.id).desc(),
        )

        result = await self.session.execute(query)
        return result.all()
