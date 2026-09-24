import logging

from fastapi import APIRouter, Query
from ycpa.core.auth.dependencies import CurrentUser
from ycpa.core.database.dependencies import DatabaseSession

from ycpa.core.schemas.responses import SuccessResponse,BaseResponse

from ycpa.schemas.responses.workspace_overview import WorkspaceOverviewResponse
from ycpa.services.workspace_overview import WorkspaceOverviewService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix= "/workspace_overview",
    tags = ["Workspace Overview"]
)

@router.get(
    "",
    response_model = BaseResponse[WorkspaceOverviewResponse],
    summary = "Get workspace Overview" 
)
async def get_workspace_overview(
    session : DatabaseSession,
    current_user : CurrentUser,
    filter_type : str = Query(
        default = "all",
        alias = "filter",
        description = (
            "Workspace filter: ",
            "all, my_workspace,shared"
        ),
        pattern = "^(all|my_workspace|shared)$",   
    ),
)-> BaseResponse[WorkspaceOverviewResponse]:
    service = WorkspaceOverviewService(session)
    data = await service.get_workspace_overview(
        user_id = current_user.id,
        filter_type = filter_type
    )
    return SuccessResponse(
        success = True,
        message = "Workspace overview fetched successfully",
        data = data 
    )