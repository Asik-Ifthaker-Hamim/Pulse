from pydantic import BaseModel
from typing import Optional, List, Dict, Any 
class MedicalKnowledgeOutput(BaseModel):
    """Structured output for the medical knowledge retrieval function."""
    status: str
    original_question: str
    summary: Optional[str] = None
    raw_search_results: Optional[List[Dict[str, Any]]] = None 
    error_message: Optional[str] = None