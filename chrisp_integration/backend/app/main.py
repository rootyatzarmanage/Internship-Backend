from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.router import api_router


app = FastAPI(
    title="Crisp FAQ API",
    description="FastAPI FAQ management and Crisp integration",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"]
)


app.include_router(
    api_router,
    prefix="/api/v1"
)


@app.get("/")
async def root():

    return {
        "success": True,
        "message": "Crisp FAQ API is running"
    }


@app.get("/health")
async def health():

    return {"status": "healthy"}