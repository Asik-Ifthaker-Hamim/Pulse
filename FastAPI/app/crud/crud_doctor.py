from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import uuid
from typing import Optional, List

from app.models.doctor_model import Doctor
from app.schemas.doctor_schema import DoctorCreate

def create_doctor(db: Session, doctor_data: DoctorCreate) -> Doctor:
    doctor_dict = doctor_data.model_dump()
    existing_doctor = db.query(Doctor).filter_by(**doctor_dict).first()
    if existing_doctor:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Doctor profile with these exact details already exists.",
        )

    db_doctor = Doctor(**doctor_dict)
    db.add(db_doctor)
    try:
        db.commit()
        db.refresh(db_doctor)
        return db_doctor
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create doctor: {e}",
        )

def get_all_doctors(db: Session) -> List[Doctor]:
    return db.query(Doctor).order_by(Doctor.name).all()

def get_doctor_by_id(db: Session, doctor_id: uuid.UUID) -> Optional[Doctor]:
    """Retrieves a doctor profile by UUID."""
    return db.query(Doctor).filter(Doctor.id == doctor_id).first()
