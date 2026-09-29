import logging
from typing import Optional

from fastapi import APIRouter, Query, status
from pydantic import BaseModel, Field

from ycpa.core.auth.dependencies import CurrentUser
from ycpa.core.database.dependencies import DatabaseSession
from ycpa.core.schemas.responses import SuccessResponse
from ycpa.repositories.auth.users import UserRepository
from ycpa.schemas.responses.auth import UserProfileResponse
from ycpa.services.auth import AuthService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["Users"])



@router.get(
    "/me",
    response_model=SuccessResponse[UserProfileResponse],
    status_code=status.HTTP_200_OK,
    summary="Get my profile",
)
async def get_me(
    current_user: CurrentUser,
) -> SuccessResponse[UserProfileResponse]:
    return SuccessResponse(
        success=True,
        data=UserProfileResponse.model_validate(current_user),
    )



class UpdateProfileRequest(BaseModel):
    full_name:    Optional[str] = Field(None, min_length=2, max_length=100)
    company_name: Optional[str] = Field(None, max_length=255)
    job_title:    Optional[str] = Field(None, max_length=255)
    phone:        Optional[str] = Field(None, max_length=20)
    timezone:     Optional[str] = Field(None, max_length=100)


@router.patch(
    "/me",
    response_model=SuccessResponse[UserProfileResponse],
    status_code=status.HTTP_200_OK,
    summary="Update my profile",
)
async def update_me(
    body: UpdateProfileRequest,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> SuccessResponse[UserProfileResponse]:
    service = AuthService(session)
    updated = await service.update_profile(
        user_id=str(current_user.id),
        full_name=body.full_name,
        company_name=body.company_name,
        job_title=body.job_title,
        phone=body.phone,
        timezone=body.timezone,
    )
    return SuccessResponse(
        success=True,
        message="Profile updated.",
        data=updated,
    )



class UserSearchResult(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    company_name: Optional[str] = None

    model_config = {"from_attributes": True}


@router.get(
    "/search",
    response_model=SuccessResponse[list[UserSearchResult]],
    status_code=status.HTTP_200_OK,
    summary="Search users by name or email (for share/invite autocomplete)",
)
async def search_users(
    session: DatabaseSession,
    current_user: CurrentUser,
    q: str = Query(..., min_length=2, description="Search term — min 2 chars"),
    limit: int = Query(default=10, le=20),
) -> SuccessResponse[list[UserSearchResult]]:
    repo = UserRepository(session)
    users = await repo.search(q=q, exclude_id=current_user.id, limit=limit)
    return SuccessResponse(
        success=True,
        data=[
            UserSearchResult(
                id=str(u.id),
                email=u.email,
                full_name=u.full_name,
                avatar_url=u.avatar_url,
                company_name=u.company_name,
            )
            for u in users
        ],
    )