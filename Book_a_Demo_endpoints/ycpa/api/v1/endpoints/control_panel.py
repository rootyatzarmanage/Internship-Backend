import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status, Query

from ycpa.core.auth.dependencies import SuperAdminUser
from ycpa.core.config import get_settings
from ycpa.core.database.dependencies import DatabaseSession
from ycpa.core.schemas.responses import BaseResponse,SuccessResponse
from ycpa.repositories.control_panel import ControlPanelRepository
from ycpa.services.control_panel import ControlPanelService

from ycpa.schemas.requests.control_panel import ControlPanelBulkRequest, ControlPanelCreateRequest, ControlPanelUpdateRequest

from ycpa.schemas.responses.control_panel import ControlPanelImageUploadResponse, ControlPanelResponse

logger = logging.getLogger(__name__)

settings = get_settings()

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
    slug: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):

    try:
        service = get_control_panel_service(session)

        control_panels = await service.get_all_control_panels(
            control_panel_id=control_panel_id,
            name=name,
            slug=slug,
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
    
@router.put("/bulk", response_model=BaseResponse[list[ControlPanelResponse]], status_code=status.HTTP_200_OK)
async def save_control_panel(payload: ControlPanelBulkRequest, session: DatabaseSession, current_user: SuperAdminUser):
    """Frontend 'Save' button: upserts every field by slug in one transaction."""
    try:
        items = await get_control_panel_service(session).bulk_upsert(payload)
        return SuccessResponse(success=True, message="Control panel saved successfully",
                               data=[ControlPanelResponse.model_validate(i) for i in items])
    except ValueError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception:
        await session.rollback()
        logger.exception("Failed to save control panel")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save control panel")


@router.get("/by-slug/{slug:path}", response_model=BaseResponse[ControlPanelResponse])
async def get_control_panel_by_slug(slug: str, session: DatabaseSession, current_user: SuperAdminUser):
    item = await get_control_panel_service(session).get_control_panel_by_slug(slug)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Control panel content not found")
    return SuccessResponse(success=True, message="Control panel content fetched successfully",
                           data=ControlPanelResponse.model_validate(item))


@router.post("/upload-image", response_model=BaseResponse[ControlPanelImageUploadResponse], status_code=status.HTTP_201_CREATED)
async def upload_control_panel_image(
    session: DatabaseSession,
    current_user: SuperAdminUser,
    control_panel_id: uuid.UUID = Form(
        ...,
        description="UUID of the existing control panel image field (fieldtype=1). The uploaded URL is saved to its value.",
    ),
    file: UploadFile = File(...),
):
    """Upload an image for an existing image field and save its URL to that field."""
    service = get_control_panel_service(session)
    control_panel = await service.get_control_panel_by_id(control_panel_id)
    if control_panel is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Control panel content not found")
    if control_panel.fieldtype != 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The selected control panel field must have fieldtype=1 (image)")

    ext = Path(file.filename or "").suffix.lower()
    if ext not in {".png", ".jpg", ".jpeg", ".webp"} or not (file.content_type or "").startswith("image/"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PNG, JPG or WEBP images are allowed")
    data = await file.read(5 * 1024 * 1024 + 1)
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image cannot be empty")
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image must be 5 MB or smaller")
    image_id = uuid.uuid4()
    relative_path = Path("superadmin") / "controlpanel" / str(control_panel.id) / f"{image_id}{ext}"
    destination = Path(settings.LOCAL_STORAGE_PATH) / relative_path
    url = f"{settings.API_V1_PREFIX}/storage-files/{relative_path.as_posix()}"
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        await service.update_control_panel(control_panel, ControlPanelUpdateRequest(value=url))
    except Exception:
        await session.rollback()
        destination.unlink(missing_ok=True)
        logger.exception("Failed to upload control panel image")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to upload control panel image")
    return SuccessResponse(success=True, message="Image uploaded",
                           data=ControlPanelImageUploadResponse(
                               control_panel_id=control_panel.id, slug=control_panel.slug,
                               image_id=image_id, url=url,
                           ))


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
