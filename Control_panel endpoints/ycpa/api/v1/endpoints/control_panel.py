import logging
import uuid

from fastapi import APIRouter, HTTPException, status, Query

from ycpa.core.auth.dependencies import SuperAdminUser
from ycpa.core.database.dependencies import DatabaseSession
from ycpa.core.schemas.responses import BaseResponse,SuccessResponse
from ycpa.repositories.control_panel import ControlPanelRepository
from ycpa.services.control_panel import ControlPanelService

from ycpa.schemas.requests.control_panel import ControlPanelCreateRequest, ControlPanelUpdateRequest

from ycpa.schemas.responses.control_panel import ControlPanelResponse

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/control_panel",
    tags=["Control Panel"],
)


def get_control_panel_service(session):
    repository = ControlPanelRepository(session)
    return ControlPanelService(repository)


@router.post(
    "",
    response_model=BaseResponse[ControlPanelResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_control_panel(
    payload: ControlPanelCreateRequest,
    session: DatabaseSession,
    current_user: SuperAdminUser,
):

    try:
        service = get_control_panel_service(session)
        control_panel = await service.create_control_panel(payload)
        return SuccessResponse(
            success=True,
            message="Control panel content created successfully",
            data=ControlPanelResponse.model_validate(control_panel),
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    except Exception:
        await session.rollback()
        logger.exception("Failed to create control panel content")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create control panel content",
        )


@router.get(
    "",
    response_model=BaseResponse[list[ControlPanelResponse]],
    status_code=status.HTTP_200_OK,
)
async def get_all_control_panels(
    session: DatabaseSession,
    current_user: SuperAdminUser,

    control_panel_id: uuid.UUID | None = Query(default=None, alias="id"),
    name: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):

    try:
        service = get_control_panel_service(session)

        control_panels = await service.get_all_control_panels(
            control_panel_id=control_panel_id,
            name=name,
            limit=limit,
            offset=offset,
        )

        data = [
            ControlPanelResponse.model_validate(item)
            for item in control_panels
        ]

        return SuccessResponse(
            success=True,
            message="Control panel contents fetched successfully",
            data=data,
        )

    except Exception:
        logger.exception("Failed to fetch control panel contents")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch control panel contents",
        )
    
@router.patch(
    "/{control_panel_id}",
    response_model=BaseResponse[ControlPanelResponse],
    status_code=status.HTTP_200_OK,
)
async def update_control_panel(
    control_panel_id: uuid.UUID,
    payload: ControlPanelUpdateRequest,
    session: DatabaseSession,
    current_user: SuperAdminUser,
):

    try:
        service = get_control_panel_service(session)

        control_panel = await service.get_control_panel_by_id(
            control_panel_id
        )

        if not control_panel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Control panel content not found",
            )

        updated = await service.update_control_panel(
            control_panel,
            payload,
        )

        return SuccessResponse(
            success=True,
            message="Control panel content updated successfully",
            data=ControlPanelResponse.model_validate(updated),
        )

    except HTTPException:
        raise

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    except Exception:
        await session.rollback()

        logger.exception("Failed to update control panel content")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update control panel content",
        )


@router.delete(
    "/{control_panel_id}",
    response_model=BaseResponse[dict],
    status_code=status.HTTP_200_OK,
)
async def delete_control_panel(
    control_panel_id: uuid.UUID,
    session: DatabaseSession,
    current_user: SuperAdminUser,
):

    try:
        service = get_control_panel_service(session)

        control_panel = await service.get_control_panel_by_id(
            control_panel_id
        )

        if not control_panel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Control panel content not found",
            )

        await service.delete_control_panel(control_panel)

        return SuccessResponse(
            success=True,
            message="Control panel content deleted successfully",
            data={"id": str(control_panel_id)},
        )

    except HTTPException:
        raise

    except Exception:
        await session.rollback()

        logger.exception("Failed to delete control panel content")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete control panel content",
        )