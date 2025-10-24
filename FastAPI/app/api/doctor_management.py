from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.orm import Session
import uuid
from typing import List

from app.db.connection import get_db
from app.schemas.doctor_schema import DoctorCreate, DoctorRead
from app.crud import crud_doctor

router = APIRouter()

@router.post(
    "/doctors/register",
    response_model=DoctorRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Doctor Management"]
)
def register_doctor(
    doctor_in: DoctorCreate,
    db: Session = Depends(get_db)
):
    try:
        doctor = crud_doctor.create_doctor(db=db, doctor_data=doctor_in)
        return doctor
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {e}"
        )

@router.get(
    "/doctors/",
    response_model=List[DoctorRead],
    tags=["Doctor Management"]
)
def read_doctors(db: Session = Depends(get_db)):
    doctors = crud_doctor.get_all_doctors(db=db)
    return doctors