import uuid 
from fastapi import APIRouter, status ,File as FastAPIFile, Form, UploadFile
from backend.core.auth.dependencies import CurrentUser
from backend.core.database.dependencies import DatabaseSession
from backend.core.schemas.responses import SuccessResponse
from backend.models.file import FileCategory
from backend.schemas.requests.file import FileUploadRequest
from backend.schemas.response.file import FileResponse
from backend.services.file import FileService

file_router = APIRouter(
    prefix = "/file",
    tags= ["File"]
)

@file_router.post(
    "/upload",
    response_model = SuccessResponse[FileResponse],
    status_code= status.HTTP_201_CREATED
)
async def upload_file(
    category : FileCategory = Form(...),
    file : UploadFile = FastAPIFile(...),
    session : DatabaseSession = None,
    current_user : CurrentUser = None
)-> SuccessResponse[FileResponse]:
    body = FileUploadRequest(
        category = category
    )
    service = FileService(session)
    data = await service.upload(
        body = body,
        upload_file = file,
        user_id = current_user.id
    )
    return SuccessResponse(
        success = True,
        message = "File Upload successfully",
        data = data
    )
    