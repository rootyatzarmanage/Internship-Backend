import logging
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ycpa.repositories.workspace_order import WorkspaceOrderRepository
from ycpa.repositories.workspace_overview import WorkspaceOverviewRepository
from ycpa.services.base import BaseService

logger = logging.getLogger(__name__)


class WorkspaceOrderService(BaseService):

    def __init__(self, session: AsyncSession):
        super().__init__(session)

        self.repo = WorkspaceOrderRepository(session)

        self.workspace_repo = WorkspaceOverviewRepository(
            session
        )

    async def get_workspace_order(
        self,
        user_id: UUID,
    ):

        workspace_data = await self.workspace_repo.get_workspaces(
            user_id=user_id,
            filter_type="all",
        )

        saved_records = await self.repo.get_user_order(
            user_id
        )

        saved_order = {
            record.workspace_id: record.order_no
            for record in saved_records
        }

        ordered_workspaces = sorted(
            enumerate(workspace_data),
            key=lambda item: (
                saved_order.get(
                    item[1]["workspace"].id,
                    float("inf")
                ),
                item[0],
            ),
        )

        records = []

        for index, (_, item) in enumerate(
            ordered_workspaces,
            start=1,
        ):

            workspace = item["workspace"]

            records.append(
                {
                    "workspace_id": workspace.id,
                    "name": workspace.name,
                    "role": item["role"],
                    "order_no": index,
                }
            )

        return records

    async def update_workspace_order(
        self,
        user_id: UUID,
        workspaces: list,
    ):

        workspace_data = await self.workspace_repo.get_workspaces(
            user_id=user_id,
            filter_type="all",
        )

        requested_workspace_ids = {
            UUID(str(item.workspace_id))
            for item in workspaces
        }

        workspace_ids = {
            UUID(str(item["workspace"].id))
            for item in workspace_data
        }

        if not requested_workspace_ids.issubset(workspace_ids):

            invalid_workspace_ids = (
                requested_workspace_ids - workspace_ids
            )

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Invalid workspace IDs: "
                    + ", ".join(
                        str(workspace_id)
                        for workspace_id in invalid_workspace_ids
                    )
                ),
            )
        records = await self.repo.save_order(
            user_id=user_id,
            workspaces=workspaces,
        )

        await self.session.commit()

        return records
