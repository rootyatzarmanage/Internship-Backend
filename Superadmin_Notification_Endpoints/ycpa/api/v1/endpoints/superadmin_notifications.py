import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from ycpa.core.auth.dependencies import SuperAdminUser
from ycpa.core.database.dependencies import DatabaseSession
from ycpa.core.schemas.responses import SuccessResponse
from ycpa.schemas.requests.notification import NotificationCreateRequest, NotificationListRequest
from ycpa.schemas.responses.notification import (
    CreateNotificationResponse,
    MarkAllReadResponse,
    NotificationCategoryResponse,
    NotificationListResponse,
    NotificationResponse,
    UnreadCountResponse,
)
from ycpa.services.superadmin_notification import SuperAdminNotificationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/super-admin/notifications", tags=["Super Admin Notifications"])


@router.get(
    "",
    response_model=SuccessResponse[NotificationListResponse],
    status_code=status.HTTP_200_OK,
    summary="List my notifications (paginated, filter by category / read state / search)",
)
async def list_notifications(
    current_user: SuperAdminUser,
    session: DatabaseSession,
    req: NotificationListRequest = Depends(),
) -> SuccessResponse[NotificationListResponse]:
    service = SuperAdminNotificationService(session)
    data = await service.list_notifications(current_user, req)
    return SuccessResponse(success=True, message="Notifications retrieved.", data=data)


@router.post(
    "",
    response_model=SuccessResponse[CreateNotificationResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a notification for every super admin",
)
async def create_notification(
    body: NotificationCreateRequest,
    current_user: SuperAdminUser,
    session: DatabaseSession,
) -> SuccessResponse[CreateNotificationResponse]:
    service = SuperAdminNotificationService(session)
    data = await service.create(current_user, body)
    return SuccessResponse(success=True, message="Notification created.", data=data)


@router.get(
    "/categories",
    response_model=SuccessResponse[list[NotificationCategoryResponse]],
    status_code=status.HTTP_200_OK,
    summary="Notification categories (hard-coded) for the menu filter",
)
async def list_categories(
    current_user: SuperAdminUser,
    session: DatabaseSession,
) -> SuccessResponse[list[NotificationCategoryResponse]]:
    service = SuperAdminNotificationService(session)
    return SuccessResponse(success=True, data=service.list_categories())


@router.get(
    "/unread-count",
    response_model=SuccessResponse[UnreadCountResponse],
    status_code=status.HTTP_200_OK,
    summary="Unread badge count, total and per category",
)
async def unread_count(
    current_user: SuperAdminUser,
    session: DatabaseSession,
) -> SuccessResponse[UnreadCountResponse]:
    service = SuperAdminNotificationService(session)
    return SuccessResponse(success=True, data=await service.unread_count(current_user))


@router.patch(
    "/read-all",
    response_model=SuccessResponse[MarkAllReadResponse],
    status_code=status.HTTP_200_OK,
    summary="Mark all my unread notifications as read (optionally one category)",
)
async def mark_all_read(
    current_user: SuperAdminUser,
    session: DatabaseSession,
    category_id: Optional[UUID] = Query(None, description="Only this category"),
) -> SuccessResponse[MarkAllReadResponse]:
    service = SuperAdminNotificationService(session)
    data = await service.mark_all_read(current_user, category_id)
    return SuccessResponse(success=True, message="Notifications marked as read.", data=data)


@router.patch(
    "/{notification_id}/read",
    response_model=SuccessResponse[NotificationResponse],
    status_code=status.HTTP_200_OK,
    summary="Mark one notification as read",
)
async def mark_read(
    notification_id: UUID,
    current_user: SuperAdminUser,
    session: DatabaseSession,
) -> SuccessResponse[NotificationResponse]:
    service = SuperAdminNotificationService(session)
    data = await service.mark_read(current_user, notification_id)
    return SuccessResponse(success=True, message="Notification marked as read.", data=data)


@router.delete(
    "/{notification_id}",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete one notification (only for me; other super admins keep theirs)",
)
async def delete_notification(
    notification_id: UUID,
    current_user: SuperAdminUser,
    session: DatabaseSession,
) -> SuccessResponse:
    service = SuperAdminNotificationService(session)
    await service.delete(current_user, notification_id)
    return SuccessResponse(success=True, message="Notification deleted.")
