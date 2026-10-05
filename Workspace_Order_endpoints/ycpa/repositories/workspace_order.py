from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ycpa.models.workspace_order import WorkspaceOrder


class WorkspaceOrderRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    async def get_user_order(
        self,
        user_id: UUID,
    ):
        query = (
            select(WorkspaceOrder)
            .where(
                WorkspaceOrder.user_id == user_id
            )
            .order_by(
                WorkspaceOrder.order_no.asc()
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def save_order(
        self,
        user_id: UUID,
        workspaces: list,
    ):

        await self.session.execute(
            delete(WorkspaceOrder).where(
                WorkspaceOrder.user_id == user_id
            )
        )

        await self.session.flush()

        records = []

        for item in workspaces:

            record = WorkspaceOrder(
                workspace_id=item.workspace_id,
                user_id=user_id,
                order_no=item.order_no,
            )

            records.append(record)
        self.session.add_all(records)
        await self.session.flush()
        return records