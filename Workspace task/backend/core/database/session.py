from collections.abc import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from backend.core.database.base import Base
from backend.core.database.engine import engine

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.execute(text("SELECT 1")) 
        await conn.run_sync(Base.metadata.create_all) 

async def close_db() -> None:
    await engine.dispose()

__all__ = [
    "AsyncSessionLocal",
    "get_async_session",
    "init_db",
    "close_db",
]
