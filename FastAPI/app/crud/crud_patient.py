from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import uuid
from typing import Optional, List

from app.models.patient_model import Patient
from app.schemas.patient_schema import PatientCreate

def create_patient(db: Session, patient_data: PatientCreate) -> Patient:
    patient_dict = patient_data.model_dump()
    existing_patient = db.query(Patient).filter_by(**patient_dict).first()
    if existing_patient:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Patient with these exact details already exists.",
        )

    db_patient = Patient(**patient_dict)
    db.add(db_patient)
    try:
        db.commit()
        db.refresh(db_patient)
        return db_patient
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create patient: {e}",
        )

def get_all_patients(db: Session) -> List[Patient]:
    return db.query(Patient).order_by(Patient.name).all()

def get_patient_by_id(db: Session, patient_id: uuid.UUID) -> Optional[Patient]:
    """Retrieves a patient by their UUID."""
    return db.query(Patient).filter(Patient.id == patient_id).first()
