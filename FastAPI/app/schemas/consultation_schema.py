from pydantic import BaseModel, UUID4
from typing import Optional
from datetime import datetime 

class TranscriptionAnalysisResponse(BaseModel):
    consultation_id: str
    doctor_id: Optional[UUID4] = None
    patient_id: Optional[UUID4] = None
    formatted_dialogue: str
    analysis_feedback: Optional[str] = None

class ReviewResponse(BaseModel):
    consultation_id: str
    formatted_dialogue: str

class SOAPResponse(BaseModel):
    consultation_id: str
    report_id: Optional[str] = None
    soap_and_prescription: str
    error: Optional[str] = None

class FollowupResponse(BaseModel):
    consultation_id: str
    followup_id: Optional[UUID4] = None
    suggested_time: Optional[datetime] = None 
    visit_type: Optional[str] = None
    reason: Optional[str] = None
    error: Optional[str] = None

class EducationSummaryResponse(BaseModel):
    consultation_id: str
    education_summary: Optional[str] = None
    error: Optional[str] = None