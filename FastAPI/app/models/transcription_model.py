from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.db.connection import Base

class Transcription(Base):
    __tablename__ = "transcriptions"

    consultation_id = Column(String, primary_key=True, index=True)
    formatted_dialogue = Column(Text)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("doctors.id"), nullable=True, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=True, index=True)