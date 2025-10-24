from sqlalchemy import Column, String, Boolean, DateTime, Enum, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.db.connection import Base
import enum
from datetime import datetime
import uuid

class VisitType(str, enum.Enum):
    in_person = "in_person"
    telehealth = "telehealth"

class FollowUpSlot(Base):
    __tablename__ = "followup_slots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    consultation_id = Column(String, index=True, nullable=True)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("doctors.id"), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)
    suggested_reason = Column(Text)
    condition_detected = Column(String, nullable=True)
    suggested_time = Column(DateTime)
    visit_type = Column(Enum(VisitType))
    confirmed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)