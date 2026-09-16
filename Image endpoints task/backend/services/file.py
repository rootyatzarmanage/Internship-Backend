import uuid
from pathlib import Path
from datetime import datetime, timezone

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import ConflictException
from backend.core.storage.r2 import get_r2_storage
from backend.models.file import File
from backend.repositories.file import FileRepository
from backend.schemas.requests.file import FileUploadRequest
from backend.schemas.response.file import FileResponse
from backend.services.base import BaseService


class FileService(BaseService):
    def __init__(self, session:AsyncSession):
        super().__init__(session)
        self.repo = FileRepository(session)
        self.storage = get_r2_storage()
    async def upload(
            self,
            body : FileUploadRequest,
            upload_file : UploadFile,
            user_id : uuid.UUID
    )-> FileResponse:
        if not upload_file.filename:
            raise ConflictException("File name is required")
        file_id = uuid.uuid4()
        file_name = Path(
            upload_file.filename
        ).name
        extension = Path(
            file_name
        ).suffix.lower().lstrip(".")
        if not extension:
            raise ConflictException("File must have an extention")
        object_key = (
            f"users/{user_id}/"
            f"{file_id}_{file_name}"
        )
        try:
            self.storage.upload_file(
                upload_file.file,
                object_key,
                upload_file.content_type
            )
            file_record = File(
                id = file_id,
                name = file_name,
                category = body.category,
                type = extension,
                user_id = user_id,
                object_key = object_key
            )
            file_record = await self.repo.create(
                file_record
            )
            await self.session.commit()
            await self.session.refresh(file_record)
            return FileResponse.model_validate(file_record)
        except Exception:
            try:
                self.storage.delete_file(
                    object_key
                )
            except Exception:
                pass
            await self.session.rollback()
            raise

