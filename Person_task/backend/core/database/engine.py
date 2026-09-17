from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import AsyncAdaptedQueuePool
from backend.core.config import get_settings

settings = get_settings()

def create_database_engine() -> AsyncEngine:
    connect_args = {
        "server_settings": {
            "application_name": settings.APP_NAME,
        },
        "command_timeout": 30,
        "timeout": 30,
        "prepared_statement_cache_size": 0,
        "statement_cache_size": 0,
        "ssl": False  
    }
    return create_async_engine(
        str(settings.DATABASE_URL),
        echo=False,  
        poolclass=AsyncAdaptedQueuePool,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_pre_ping=settings.DB_POOL_PRE_PING,
        pool_recycle=settings.DB_POOL_RECYCLE,
        connect_args=connect_args,
    )

engine: AsyncEngine = create_database_engine()

__all__ = ["engine"]
