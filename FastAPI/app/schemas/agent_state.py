from pydantic import BaseModel, Field, UUID4
from typing import Optional, Dict, Any, List
from datetime import datetime

class AgentState(BaseModel):
    consultation_id: Optional[str] = None
    formatted_dialogue: Optional[str] = None
    analysis_feedback: Optional[str] = None
    updated_dialogue: Optional[str] = None
    soap_and_prescription: Optional[str] = None
    followup_id: Optional[UUID4] = None
    suggested_time: Optional[datetime] = None
    visit_type: Optional[str] = None
    followup_reason: Optional[str] = None
    education_summary: Optional[str] = None

    patient_query: Optional[str] = None
    patient_query_date: Optional[str] = None
    patient_query_time: Optional[str] = None
    patient_query_designation: Optional[str] = None
    selected_slot_id: Optional[str] = None
    patient_name: Optional[str] = None
    patient_email: Optional[str] = None

    available_slots: Optional[List[Dict[str, Any]]] = None
    recommendation: Optional[str] = None
    booking_confirmation: Optional[str] = None

    doctor_id: Optional[UUID4] = None
    patient_id: Optional[UUID4] = None

    class Config:
        arbitrary_types_allowed = True
        from_attributes = True

    def dict(self, **kwargs) -> Dict[str, Any]:
        dump = self.model_dump(exclude_unset=True, **kwargs)
        return dump