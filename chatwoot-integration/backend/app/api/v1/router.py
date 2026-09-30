from fastapi import APIRouter

from app.api.v1.endpoints import faq, crisp_webhook

api_router = APIRouter()

api_router.include_router(faq.router)
api_router.include_router(crisp_webhook.router)