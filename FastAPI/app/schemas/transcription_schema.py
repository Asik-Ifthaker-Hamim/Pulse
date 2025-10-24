from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TranscriptionResponse(BaseModel):
    consultation_id: str
    formatted_dialogue: str

    # SOAP + Prescription
    soap_and_prescription: Optional[str] = None

    # Follow-up Scheduling
    followup_id: Optional[str] = None
    suggested_time: Optional[datetime] = None
    visit_type: Optional[str] = None
    followup_reason: Optional[str] = None

    # Patient Education
    education_summary: Optional[str] = None

    class Config:
        from_attributes = True
