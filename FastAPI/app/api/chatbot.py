from fastapi import APIRouter, HTTPException, Depends, Body
from app.agents.chatbot_agent import DoctorChatbotAgent
from app.schemas.chatbot_schema import ChatbotResponse
from pydantic import UUID4, BaseModel, Field
from typing import List, Dict, Optional
import json
import logging 

logger = logging.getLogger(__name__) 

router = APIRouter()

class ChatbotRequest(BaseModel):
    doctor_id: UUID4
    message: str
    chat_history: Optional[List[Dict[str, str]]] = Field(default_factory=list)

@router.post(
    "/chatbot",
    response_model=ChatbotResponse,
    tags=["Doctor Chatbot"]
)
async def ask_chatbot(
    request: ChatbotRequest = Body(...)
):
    logger.info(f"Received chatbot request for doctor: {request.doctor_id}")
    try:
        response_obj = DoctorChatbotAgent().run(
            doctor_id=request.doctor_id,
            message=request.message,
            chat_history=request.chat_history
        )
        return response_obj
    except Exception as e:
         logger.error(f"Chatbot endpoint error for doctor {request.doctor_id}: {e}", exc_info=True) 
         raise HTTPException(status_code=500, detail=f"Chatbot failed: {e}")