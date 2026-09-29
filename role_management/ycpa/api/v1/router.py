from fastapi import APIRouter

from ycpa.api.v1.endpoints.users import router as users_router
from ycpa.api.v1.endpoints.auth import router as auth_router
from ycpa.api.v1.endpoints.cognito import router as cognito_router
from ycpa.api.v1.endpoints.rbac import router as rbac_router


api_router = APIRouter()

api_router.include_router(users_router)
api_router.include_router(auth_router)
api_router.include_router(cognito_router)
api_router.include_router(rbac_router)