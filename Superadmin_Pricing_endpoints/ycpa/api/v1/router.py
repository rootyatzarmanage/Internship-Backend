from fastapi import APIRouter

from ycpa.api.v1.endpoints import (
    auth,
    cognito,
    users,
    superadmin_pricing,
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(cognito.router)
api_router.include_router(users.router)
api_router.include_router(superadmin_pricing.router)

