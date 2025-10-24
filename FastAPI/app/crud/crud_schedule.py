from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.schedule_model import DoctorSlot
import uuid
from typing import List

def get_slots_by_doctor_id(db: Session, doctor_id: uuid.UUID, include_booked: bool = True) -> List[DoctorSlot]:
    """Retrieves slots for a given doctor ID, optionally filtering out booked ones."""
   
    query = db.query(DoctorSlot).filter(DoctorSlot.doctor_id == str(doctor_id)) 

    if not include_booked:
        query = query.filter(DoctorSlot.is_booked == False)

    query = query.order_by(desc(DoctorSlot.start_time))

    return query.all()