from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from .knowledge_schema import MedicalKnowledgeOutput

class ChatbotResponse(BaseModel):
    response_type: str
    text_response: Optional[str] = None
    schedule_data: Optional[List[Dict[str, Any]]] = None
    knowledge_data: Optional[MedicalKnowledgeOutput] = None
    error_message: Optional[str] = None