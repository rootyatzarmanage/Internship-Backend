import uuid
from io import BytesIO
from pathlib import Path
from zipfile import BadZipFile, ZipFile

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from ycpa.core.config import get_settings
from ycpa.core.exceptions import BadRequestException
from ycpa.models.tickets import Ticket, TicketAttachment, TicketProject
from ycpa.models.user import User
from ycpa.repositories.support_tickets import SupportTicketRepository
from ycpa.schemas.requests.support_tickets import CreateTicketRequest
from ycpa.schemas.responses.support_tickets import MyTicketsResponse, ProjectCardResponse, TicketResponse
from ycpa.services.base import BaseService
from ycpa.services.notification import notify

ALLOWED_EXT = {".pdf", ".jpg", ".jpeg", ".png", ".docx"}
MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_FILES = 5


def _validate_attachment_contents(file_name: str, ext: str, data: bytes) -> None:
    """Check the file type independently of the client-supplied MIME type."""
    signatures = {
        ".pdf": b"%PDF-",
        ".jpg": b"\xff\xd8\xff",
        ".jpeg": b"\xff\xd8\xff",
        ".png": b"\x89PNG\r\n\x1a\n",
    }
    if ext == ".docx":
        try:
            # Inspect the package directory without extracting or decompressing
            # untrusted entries. An arbitrary ZIP is not a Word document.
            with ZipFile(BytesIO(data)) as package:
                valid = {"[Content_Types].xml", "_rels/.rels", "word/document.xml"}.issubset(package.namelist())
        except BadZipFile:
            valid = False
    else:
        valid = data.startswith(signatures[ext])
    if not valid:
        raise BadRequestException(f"'{file_name}' contents do not match its file type")


async def save_attachments(ticket_id: uuid.UUID, files: list[UploadFile], user_id: uuid.UUID,
                           reply_id: uuid.UUID | None = None) -> list[TicketAttachment]:
    """Shared by ticket create + ticket reply. Stores under LOCAL_STORAGE_PATH/tickets/<ticket_id>/."""
    files = [f for f in files if f and f.filename]
    if len(files) > MAX_FILES:
        raise BadRequestException(f"Maximum {MAX_FILES} files allowed")
    s, out = get_settings(), []
    for f in files:
        if any(ord(char) < 32 or ord(char) == 127 for char in f.filename):
            raise BadRequestException("Invalid attachment filename")
        ext = Path(f.filename).suffix.lower()
        if ext not in ALLOWED_EXT:
            raise BadRequestException(f"Unsupported file type '{ext}'. Allowed: PDF, JPG, PNG, DOCX")
        data = await f.read(MAX_FILE_BYTES + 1)
        if len(data) > MAX_FILE_BYTES:
            raise BadRequestException(f"'{f.filename}' exceeds 10 MB")
        _validate_attachment_contents(f.filename, ext, data)
        rel = f"tickets/{ticket_id}/{uuid.uuid4().hex}{ext}"
        dest = Path(s.LOCAL_STORAGE_PATH) / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        out.append(TicketAttachment(
            id=uuid.uuid4(), ticket_id=ticket_id, reply_id=reply_id, file_name=Path(f.filename).name,
            file_path=rel, file_url=f"{s.API_V1_PREFIX}/storage-files/{rel}",
            content_type=f.content_type, size_bytes=len(data), uploaded_by=user_id,
        ))
    return out


class SupportTicketService(BaseService):
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.repo = SupportTicketRepository(session)

    async def list_projects(self, user: User, q: str | None, limit: int) -> list[ProjectCardResponse]:
        return [ProjectCardResponse(**c) for c in await self.repo.list_user_projects(user.id, q, limit)]

    async def create_ticket(self, user: User, data: CreateTicketRequest, files: list[UploadFile]) -> TicketResponse:
        cards = {(c["id"], c["product_type"]): c for c in await self.repo.list_user_projects(user.id, limit=1000)}
        projects = []
        for ref in data.projects:
            card = cards.get((ref.project_id, ref.product_type))
            if not card:
                raise BadRequestException(f"Project {ref.project_id} not found or not accessible")
            projects.append(TicketProject(
                project_id=card["id"], product_type=card["product_type"], project_name=card["name"],
                workspace_name=card["workspace_name"], thumbnail_url=card["thumbnail_url"],
            ))

        ticket = Ticket(
            id=uuid.uuid4(), user_id=user.id, category=data.category, subject=data.subject,
            message=data.message, status="pending", projects=projects,
        )
        ticket.attachments = await save_attachments(ticket.id, files, user.id)
        await self.repo.create(ticket)
        await self.log_audit("ticket.create", "ticket", str(ticket.id), user.id, payload={"ticket_no": ticket.ticket_no})
        await self.session.commit()
        await notify(self.session, "ticket", f"New ticket {ticket.ticket_id}",
                     {"Ticket ID": ticket.ticket_id, "Category": ticket.category, "Subject": ticket.subject})
        return TicketResponse.model_validate(ticket)

    async def my_tickets(self, user: User, page: int, per_page: int) -> MyTicketsResponse:
        items, total = await self.repo.list_by_user(user.id, page, per_page)
        return MyTicketsResponse(items=[TicketResponse.model_validate(t) for t in items], total=total, page=page, per_page=per_page)
