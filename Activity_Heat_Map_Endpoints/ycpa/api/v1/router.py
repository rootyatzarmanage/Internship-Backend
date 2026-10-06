from fastapi import APIRouter

from ycpa.api.v1.endpoints import (
    auth,
    cognito,
    users,
    activity_heat_map,
    activity_log
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(cognito.router)
api_router.include_router(users.router)
api_router.include_router(activity_heat_map.router)
api_router.include_router(activity_log.router)

