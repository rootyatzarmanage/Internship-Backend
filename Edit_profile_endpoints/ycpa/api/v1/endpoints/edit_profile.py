import logging

from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from pydantic import ValidationError
from fastapi.responses import FileResponse

from ycpa.core.auth.dependencies import CurrentUser
from ycpa.core.database.dependencies import DatabaseSession
from ycpa.core.schemas.responses import SuccessResponse

from ycpa.schemas.requests.edit_profile import EditProfileRequest
from ycpa.schemas.responses.edit_profile import EditProfileResponse
from ycpa.services.edit_profile import EditProfileService


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/edit_profile",
    tags=["Edit Profile"],
)


@router.patch(
    "",
    response_model=SuccessResponse[EditProfileResponse],
    status_code=status.HTTP_200_OK,
    summary="Update logged-in user's profile",
)
async def edit_profile(
    current_user: CurrentUser,
    session: DatabaseSession,

    first_name: str | None = Form(default=None),
    last_name: str | None = Form(default=None),
    email: str | None = Form(default=None),

    country_code: str | None = Form(default=None),
    phone: str | None = Form(default=None),

    country: str | None = Form(default=None),
    state: str | None = Form(default=None),
    district: str | None = Form(default=None),
    pincode: str | None = Form(default=None),   
    image: UploadFile | None = File(default=None),
    delete: int | None = Form(default=0, ge=0, le=1),
):
    try:
        form_data = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "country_code": country_code,
            "phone": phone,
            "country": country,
            "state": state,
            "district": district,
            "pincode": pincode,
            "delete": delete,
        }
        form_data = {
            key: value
            for key, value in form_data.items()
            if value is not None
        }
        try:
            request_data = EditProfileRequest.model_validate(form_data)

        except ValidationError as exc:

            errors = [
                {
                    "field": ".".join(str(item) for item in error["loc"]),
                    "message": error["msg"],
                    "type": error["type"],
                }
                for error in exc.errors(
                    include_url=False,
                    include_context=False,
                )
            ]

            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=errors,
            )
        data = request_data.model_dump(exclude_unset=True)
        service = EditProfileService(session)

        updated_profile = await service.edit_profile(
            user_id=current_user.id,
            data=data,
            image=image,
        )

        return SuccessResponse(
            success=True,
            message="Profile updated successfully",
            data=EditProfileResponse.model_validate(updated_profile),
        )

    except HTTPException:
        raise

    except Exception:
        logger.exception(
            "Failed to update profile",
            extra={"user_id": str(current_user.id)},
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile",
        )


@router.get(
    "/image",
    status_code=status.HTTP_200_OK,
    summary="Get logged-in user's profile image as a file",
)
async def get_profile_image(
    current_user: CurrentUser,
    session: DatabaseSession,
):
    try:
        service = EditProfileService(session)

        image_path = await service.get_profile_image_path(
            current_user.id
        )

        return FileResponse(
            path=image_path,
            filename=image_path.name,
            media_type={
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".webp": "image/webp",
            }.get(
                image_path.suffix.lower(),
                "application/octet-stream",
            ),
        )

    except HTTPException:
        raise

    except Exception:
        logger.exception(
            "Failed to fetch profile image",
            extra={"user_id": str(current_user.id)},
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch profile image",
        )

@router.get(
    "",
    response_model=SuccessResponse[EditProfileResponse],
    status_code=status.HTTP_200_OK,
    summary="Get logged-in user's editable profile",
)
async def get_edit_profile(
    current_user: CurrentUser,
    session: DatabaseSession,
):
    try:
        service = EditProfileService(session)

        profile = await service.get_profile(
            user_id=current_user.id
        )

        return SuccessResponse(
            success=True,
            message="Profile fetched successfully",
            data=EditProfileResponse.model_validate(profile),
        )

    except HTTPException:
        raise

    except Exception:
        logger.exception(
            "Failed to fetch profile",
            extra={"user_id": str(current_user.id)},
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch profile",
        )