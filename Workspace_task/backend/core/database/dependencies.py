from typing import Annotated
 
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
 
from backend.core.database.session import get_async_session
 
DatabaseSession = Annotated[AsyncSession, Depends(get_async_session)]