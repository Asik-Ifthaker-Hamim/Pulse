from sqlalchemy.orm import Session
from app.models.transcription_model import Transcription
import uuid
from pydantic import UUID4

def save_transcription(
    db: Session,
    formatted_dialogue: str,
    consultation_id: str = None,
    doctor_id: UUID4 = None,
    patient_id: UUID4 = None
) -> Transcription:
    consultation_id = consultation_id or str(uuid.uuid4())
    transcription = Transcription(
        consultation_id=consultation_id,
        formatted_dialogue=formatted_dialogue,
        doctor_id=doctor_id,
        patient_id=patient_id
    )
    db.add(transcription)
    db.commit()
    db.refresh(transcription)
    return transcription

def update_transcription_text(db: Session, consultation_id: str, new_text: str) -> None:
    transcription = db.query(Transcription).filter(Transcription.consultation_id == consultation_id).first()
    if transcription:
        transcription.formatted_dialogue = new_text
        db.commit()