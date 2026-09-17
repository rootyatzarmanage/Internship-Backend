import logging
import os

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncConnection
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from backend.api.v1.endpoints.auth import auth_router
from backend.api.v1.endpoints.register import register_router
from backend.api.v1.endpoints.forgot_password import forgot_router
from backend.api.v1.endpoints.file import file_router
from backend.core.config import get_settings
from backend.core.database.base import Base
from backend.core.database.engine import engine
from backend.core.exception_handlers import app_exception_handler
from backend.core.exceptions import AppException
# from ycpa.core.error_handlers import register_exception_handlers
# from ycpa.core.lifespan import lifespan
# from ycpa.core.logger import VisualLogger, setup_logging
# from ycpa.middleware.registry import register_middleware

settings = get_settings()

# setup_logging()
if settings.ENVIRONMENT == "production":
    logging.getLogger("sqlalchemy.engine").disabled = True

logger = logging.getLogger(__name__)
enable_docs = settings.DEBUG or settings.ENVIRONMENT != "production"
@asynccontextmanager

async def lifespan(app: FastAPI):
    logger.info("Initializing database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables verified.")
    yield

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if enable_docs else None,
    redoc_url="/redoc" if enable_docs else None,
    openapi_url="/openapi.json" if enable_docs else None,
    swagger_ui_parameters={
        "defaultModelsExpandDepth": -1,
        "persistAuthorization": True,
    },
)

app.add_exception_handler(
    AppException,
    app_exception_handler
)
# middleware_manifest = register_middleware(app, settings)
# VisualLogger.middleware_table(middleware_manifest)
# register_exception_handlers(app)
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(register_router,prefix=settings.API_V1_PREFIX)
app.include_router(forgot_router,prefix=settings.API_V1_PREFIX)
app.include_router(file_router,prefix=settings.API_V1_PREFIX)

os.makedirs(settings.LOCAL_STORAGE_PATH, exist_ok=True)
app.mount(
    f"{settings.API_V1_PREFIX}/storage-files",
    StaticFiles(directory=settings.LOCAL_STORAGE_PATH),
    name="storage",
)
logger.info("Local storage mounted at %s/storage-files -> %s", settings.API_V1_PREFIX, settings.LOCAL_STORAGE_PATH)
 