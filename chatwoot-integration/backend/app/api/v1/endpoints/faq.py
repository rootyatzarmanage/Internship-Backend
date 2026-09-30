from fastapi import APIRouter, HTTPException, status

from app.schemas.faq import (
    FAQCreate,
    FAQUpdate,
    FAQQuery,
    FAQAnswerResponse
)

from app.services.faq_service import FAQService
from app.services.crisp_service import CrispService


router = APIRouter(
    prefix="/faq",
    tags=["FAQ"]
)

faq_service = FAQService()
crisp_service = CrispService()


# GET ALL FAQ
@router.get("/")
async def get_faqs():

    return {
        "success": True,
        "data": faq_service.get_all_faqs()
    }


# CREATE FAQ
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_faq(data: FAQCreate):

    faq = faq_service.create_faq(data)

    return {
        "success": True,
        "message": "FAQ created successfully",
        "data": faq
    }


# UPDATE FAQ
@router.put("/{faq_id}")
async def update_faq(faq_id: int, data: FAQUpdate):

    faq = faq_service.update_faq(faq_id, data)

    if not faq:
        raise HTTPException(
            status_code=404,
            detail="FAQ not found"
        )

    return {
        "success": True,
        "message": "FAQ updated successfully",
        "data": faq
    }


# DELETE FAQ
@router.delete("/{faq_id}")
async def delete_faq(faq_id: int):

    deleted = faq_service.delete_faq(faq_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="FAQ not found"
        )

    return {
        "success": True,
        "message": "FAQ deleted successfully"
    }


# SEARCH FAQ / GET ANSWER
@router.post("/answer", response_model=FAQAnswerResponse)
async def get_faq_answer(data: FAQQuery):

    return faq_service.find_answer(data.question)


# FIND FAQ AND SEND ANSWER TO CRISP
@router.post("/reply/{session_id}")
async def reply_from_faq(
    session_id: str,
    data: FAQQuery
):

    result = faq_service.find_answer(data.question)

    if not result["matched"]:
        return result

    crisp_response = await crisp_service.send_message(
        session_id=session_id,
        message=result["answer"]
    )

    return {
        "success": True,
        "message": "FAQ answer sent to Crisp",
        "answer": result["answer"],
        "crisp_response": crisp_response
    }