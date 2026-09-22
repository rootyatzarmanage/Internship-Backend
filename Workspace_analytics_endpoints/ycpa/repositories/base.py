import logging
from datetime import datetime, timezone
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar  # noqa: UP035
from uuid import UUID

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.exc import DBAPIError, IntegrityError, OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from ycpa.core.database.base import Base
from ycpa.core.exceptions import (
    ConflictException,
    DatabaseException,
)

logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):

    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model      = model
        self.session    = session
        self.model_name = model.__name__


    async def get_by_id(self, id: UUID, include_deleted: bool = False) -> ModelType | None:
        try:
            query = select(self.model).where(self.model.id == id)
            if not include_deleted and hasattr(self.model, "deleted_at"):
                query = query.where(self.model.deleted_at.is_(None))
            result = await self.session.execute(query)
            return result.scalar_one_or_none()

        except DBAPIError as e:
            logger.error(f"DB error fetching {self.model_name}", extra={"id": str(id), "error": str(e)}, exc_info=True)
            raise DatabaseException(f"Failed to fetch {self.model_name}")

    async def get_by_field(self, field: str, value: Any, include_deleted: bool = False) -> ModelType | None:
        try:
            query = select(self.model).where(getattr(self.model, field) == value)
            if not include_deleted and hasattr(self.model, "deleted_at"):
                query = query.where(self.model.deleted_at.is_(None))
            result = await self.session.execute(query)
            return result.scalar_one_or_none()

        except DBAPIError as e:
            logger.error(f"DB error fetching {self.model_name} by {field}", extra={"field": field, "error": str(e)}, exc_info=True)
            raise DatabaseException(f"Failed to fetch {self.model_name}")

    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
        filters: dict[str, Any] | None = None,
        order_by: str | None = None,
        include_deleted: bool = False,
    ) -> list[ModelType]:
        try:
            query = select(self.model)
            if not include_deleted and hasattr(self.model, "deleted_at"):
                query = query.where(self.model.deleted_at.is_(None))

            if filters:
                for key, value in filters.items():
                    if hasattr(self.model, key):
                        if isinstance(value, list):
                            query = query.where(getattr(self.model, key).in_(value))
                        elif value is None:
                            query = query.where(getattr(self.model, key).is_(None))
                        else:
                            query = query.where(getattr(self.model, key) == value)

            if order_by:
                field = order_by.lstrip("-")
                if hasattr(self.model, field):
                    col = getattr(self.model, field)
                    query = query.order_by(col.desc() if order_by.startswith("-") else col)

            result = await self.session.execute(query.offset(offset).limit(limit))
            return list(result.scalars().all())

        except DBAPIError as e:
            logger.error(f"DB error fetching {self.model_name} list", extra={"filters": filters, "error": str(e)}, exc_info=True)
            raise DatabaseException(f"Failed to fetch {self.model_name} records")

    async def count(self, filters: dict[str, Any] | None = None, include_deleted: bool = False) -> Any | None:
        try:
            query = select(func.count()).select_from(self.model)
            if not include_deleted and hasattr(self.model, "deleted_at"):
                query = query.where(self.model.deleted_at.is_(None))
            if filters:
                for key, value in filters.items():
                    if hasattr(self.model, key):
                        query = query.where(getattr(self.model, key) == value)
            result = await self.session.execute(query)
            return result.scalar()

        except DBAPIError as e:
            logger.error(f"DB error counting {self.model_name}", extra={"error": str(e)}, exc_info=True)
            raise DatabaseException(f"Failed to count {self.model_name}")

    async def exists(self, id: UUID, include_deleted: bool = False) -> bool:
        try:
            query = select(self.model.id).where(self.model.id == id)
            if not include_deleted and hasattr(self.model, "deleted_at"):
                query = query.where(self.model.deleted_at.is_(None))
            result = await self.session.execute(query)
            return result.scalar_one_or_none() is not None

        except DBAPIError as e:
            logger.error(f"DB error checking {self.model_name} existence", extra={"id": str(id), "error": str(e)}, exc_info=True)
            raise DatabaseException(f"Failed to check {self.model_name} existence")

    async def search(self, search_term: str, search_fields: list[str], limit: int = 100, offset: int = 0) -> List[ModelType]:
        try:
            conditions = [
                getattr(self.model, field).ilike(f"%{search_term}%")
                for field in search_fields
                if hasattr(self.model, field)
            ]
            if not conditions:
                return []

            query = select(self.model).where(or_(*conditions))
            if hasattr(self.model, "deleted_at"):
                query = query.where(self.model.deleted_at.is_(None))
            result = await self.session.execute(query.offset(offset).limit(limit))
            return list(result.scalars().all())

        except DBAPIError as e:
            logger.error(f"DB error searching {self.model_name}", extra={"search_term": search_term, "error": str(e)}, exc_info=True)
            raise DatabaseException(f"Failed to search {self.model_name}")


    async def create(self, obj: ModelType) -> ModelType:
        try:
            self.session.add(obj)
            await self.session.flush()
            await self.session.refresh(obj)
            logger.debug(f"{self.model_name} created", extra={"id": str(obj.id) if hasattr(obj, "id") else None})
            return obj

        except IntegrityError as e:
            error_msg = str(e.orig) if hasattr(e, "orig") else str(e)
            logger.error(f"Integrity error creating {self.model_name}", extra={"error": error_msg[:200]}, exc_info=True)
            raise ConflictException(message=f"{self.model_name} already exists", details={"error": error_msg[:100]})

        except OperationalError as e:
            logger.critical(f"DB connection error creating {self.model_name}", extra={"error": str(e)[:200]}, exc_info=True)
            raise DatabaseException("Database connection error. Please try again.")

        except Exception as e:
            logger.error(f"Unexpected error creating {self.model_name}", extra={"error": str(e)}, exc_info=True)
            raise DatabaseException(f"Failed to bulk create {self.model_name}")

    async def update_by_id(self, id: UUID, values: dict[str, Any]) -> ModelType | None:
        try:
            if hasattr(self.model, "updated_at"):
                values["updated_at"] = datetime.now(timezone.utc)

            await self.session.execute(
                update(self.model).where(self.model.id == id).values(**values)
            )
            await self.session.flush()
            updated = await self.session.get(self.model, id)
            logger.debug(f"{self.model_name} updated", extra={"id": str(id), "fields": list(values.keys())})
            return updated

        except IntegrityError as e:
            error_msg = str(e.orig) if hasattr(e, "orig") else str(e)
            logger.error(f"Integrity error updating {self.model_name}", extra={"id": str(id), "error": error_msg[:200]}, exc_info=True)
            raise ConflictException(message=f"Failed to update {self.model_name} due to conflict", details={"error": error_msg[:100]})

        except Exception as e:
            logger.error(f"Error updating {self.model_name}", extra={"id": str(id), "error": str(e)}, exc_info=True)
            raise DatabaseException(f"Failed to update {self.model_name}")

    async def soft_delete(self, id: UUID, deleted_by: UUID) -> ModelType | None:
        try:
            await self.session.execute(
                update(self.model)
                .where(self.model.id == id)
                .values(deleted_at=datetime.now(timezone.utc), deleted_by=deleted_by)
            )
            await self.session.flush()
            logger.info(f"{self.model_name} soft deleted", extra={"id": str(id), "deleted_by": str(deleted_by)})
            return await self.get_by_id(id, include_deleted=True)

        except Exception as e:
            logger.error(f"Error soft deleting {self.model_name}", extra={"id": str(id), "error": str(e)}, exc_info=True)
            raise DatabaseException(f"Failed to delete {self.model_name}")

    async def hard_delete(self, id: UUID) -> bool:
        try:
            result = await self.session.execute(
                delete(self.model).where(self.model.id == id)
            )
            await self.session.flush()
            logger.info(f"{self.model_name} hard deleted", extra={"id": str(id)})
            return result.rowcount > 0

        except Exception as e:
            logger.error(f"Error hard deleting {self.model_name}", extra={"id": str(id), "error": str(e)}, exc_info=True)
            raise DatabaseException(f"Failed to delete {self.model_name}")

    async def bulk_create(self, objects: list[ModelType]) -> list[ModelType]:
        try:
            self.session.add_all(objects)
            await self.session.flush()
            for obj in objects:
                await self.session.refresh(obj)
            logger.info(f"Bulk created {len(objects)} {self.model_name} records")
            return objects

        except IntegrityError as e:
            error_msg = str(e.orig) if hasattr(e, "orig") else str(e)
            logger.error(f"Integrity error bulk creating {self.model_name}", extra={"count": len(objects), "error": error_msg[:200]}, exc_info=True)
            raise ConflictException(message="Bulk create failed due to conflict", details={"count": len(objects)})

        except Exception as e:
            logger.error(f"Error bulk creating {self.model_name}", extra={"count": len(objects), "error": str(e)}, exc_info=True)
            raise DatabaseException(f"Failed to bulk create {self.model_name}")

    async def get_with_pagination(
        self,
        page: int = 1,
        per_page: int = 10,
        filters: dict[str, Any] | None = None,
        order_by: str | None = None,
        include_deleted: bool = False,
    ) -> tuple[list[Base], Any | None]:
        try:
            total = await self.count(filters=filters, include_deleted=include_deleted)
            items = await self.get_all(
                limit=per_page,
                offset=(page - 1) * per_page,
                filters=filters,
                order_by=order_by,
                include_deleted=include_deleted,
            )
            return items, total

        except Exception as e:
            logger.error(f"Error paginating {self.model_name}", extra={"page": page, "per_page": per_page, "error": str(e)}, exc_info=True)
            raise DatabaseException(f"Failed to paginate {self.model_name}")
 