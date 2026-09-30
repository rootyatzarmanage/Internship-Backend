from fastapi import APIRouter, Request, HTTPException
import logging

from app.core.config import settings
from app.services.faq_service import FAQService
from app.services.crisp_service import CrispService

router = APIRouter(
    prefix="/crisp",
    tags=["Crisp Integration"]
)

logger = logging.getLogger(__name__)

faq_service = FAQService()
crisp_service = CrispService()


@router.post("/webhook")
async def crisp_webhook(request: Request):

    payload = await request.json()

    # Verify the event is for your website
    if payload.get("website_id") != settings.CRISP_WEBSITE_ID:
        raise HTTPException(
            status_code=403,
            detail="Invalid website ID"
        )

    # Process only new visitor messages
    if payload.get("event") != "message:send":
        return {"success": True, "ignored": True}

    data = payload.get("data", {})

    # Ignore operator messages
    if data.get("from") != "user":
        return {"success": True, "ignored": True}

    # Process text messages only
    if data.get("type") != "text":
        return {"success": True, "ignored": True}

    question = data.get("content", "").strip()
    session_id = data.get("session_id")

    if not question or not session_id:
        return {"success": True, "ignored": True}

    logger.info("Visitor question received: %s", question)

    # Search FAQ
    result = faq_service.find_answer(question)

    if result["matched"]:

        answer = result["answer"]

    else:

        answer = (
            "Sorry, I couldn't find an answer to that question. "
            "Please leave your message and Janesh will get back to you."
        )

    # Send response into the same Crisp conversation
    await crisp_service.send_message(
        session_id=session_id,
        message=answer
    )

    return {
        "success": True,
        "message": "Crisp reply processed"
    }