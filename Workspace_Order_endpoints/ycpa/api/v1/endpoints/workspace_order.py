import logging

from fastapi import APIRouter, status

from ycpa.core.auth.dependencies import CurrentUser
from ycpa.core.database.dependencies import DatabaseSession
from ycpa.core.schemas.responses import SuccessResponse

from ycpa.schemas.requests.workspace_order import WorkspaceOrderRequest

from ycpa.schemas.responses.workspace_order import (
    WorkspaceOrderResponse,
    WorkspaceOrderItemResponse,
)

from ycpa.services.workspace_order import WorkspaceOrderService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/workspace_order",
    tags=["Workspace Order"],
)


@router.get(
    "",
    response_model=SuccessResponse[WorkspaceOrderResponse],
    status_code=status.HTTP_200_OK,
    summary="Get user workspace order",
)
async def get_workspace_order(
    session: DatabaseSession,
    current_user: CurrentUser,
) -> SuccessResponse[WorkspaceOrderResponse]:

    service = WorkspaceOrderService(session)

    records = await service.get_workspace_order(
        user_id=current_user.id,
    )

    data = WorkspaceOrderResponse(
        workspaces=[
            WorkspaceOrderItemResponse(
                workspace_id=item["workspace_id"],
                name=item["name"],
                role=item["role"],
                order_no=item["order_no"],
            )
            for item in records
        ]
    )

    return SuccessResponse(
        success=True,
        message="Workspace order fetched successfully",
        data=data,
    )


@router.put(
    "",
    response_model=SuccessResponse[WorkspaceOrderResponse],
    status_code=status.HTTP_200_OK,
    summary="Update user workspace order",
)
async def update_workspace_order(
    request: WorkspaceOrderRequest,
    session: DatabaseSession,
    current_user: CurrentUser,
) -> SuccessResponse[WorkspaceOrderResponse]:

    service = WorkspaceOrderService(session)

    await service.update_workspace_order(
        user_id=current_user.id,
        workspaces=request.workspaces,
    )

    records = await service.get_workspace_order(
        user_id=current_user.id,
    )

    data = WorkspaceOrderResponse(
        workspaces=[
            WorkspaceOrderItemResponse(
                workspace_id=item["workspace_id"],
                name=item["name"],
                role=item["role"],
                order_no=item["order_no"],
            )
            for item in records
        ]
    )

    return SuccessResponse(
        success=True,
        message="Workspace order updated successfully",
        data=data,
    )