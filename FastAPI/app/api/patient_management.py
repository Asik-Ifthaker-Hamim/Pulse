from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.orm import Session
import uuid
from typing import List

from app.db.connection import get_db
from app.schemas.patient_schema import PatientCreate, PatientRead
from app.crud import crud_patient

router = APIRouter()

@router.post(
    "/patients/register",
    response_model=PatientRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Patient Management"]
)
def register_patient(
    patient_in: PatientCreate,
    db: Session = Depends(get_db)
):
    try:
        patient = crud_patient.create_patient(db=db, patient_data=patient_in)
        return patient
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {e}"
        )

@router.get(
    "/patients/",
    response_model=List[PatientRead],
    tags=["Patient Management"]
)
def read_patients(db: Session = Depends(get_db)):
    patients = crud_patient.get_all_patients(db=db)
    return patients