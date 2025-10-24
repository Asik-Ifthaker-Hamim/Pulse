from sqlalchemy.orm import Session
from app.models.followup_model import FollowUpSlot
from datetime import datetime

def query_upcoming_schedule(db: Session, doctor_id: str):
    now = datetime.utcnow()
    upcoming = db.query(FollowUpSlot).filter(
        FollowUpSlot.doctor_id == doctor_id,
        FollowUpSlot.suggested_time >= now
    ).order_by(FollowUpSlot.suggested_time.asc()).all()

    return [
        {
            "patient_id": slot.patient_id,
            "condition": slot.condition_detected,
            "time": slot.suggested_time.isoformat(),
            "visit_type": slot.visit_type.value,
            "reason": slot.suggested_reason,
            "confirmed": slot.confirmed
        }
        for slot in upcoming
    ]
def confirm_next_unconfirmed(db: Session, doctor_id: str):
    next_slot = db.query(FollowUpSlot).filter(
        FollowUpSlot.doctor_id == doctor_id,
        FollowUpSlot.confirmed == False
    ).order_by(FollowUpSlot.suggested_time.asc()).first()

    if not next_slot:
        return None

    next_slot.confirmed = True
    db.commit()
    db.refresh(next_slot)
    return next_slot
