from sqlalchemy.orm import Session
from app.models.followup_model import FollowUpSlot, VisitType
import uuid
from pydantic import UUID4
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def save_followup_slot(
    db: Session,
    consultation_id: str,
    doctor_id: UUID4,
    patient_id: UUID4,
    condition_detected: str,
    suggested_time: datetime,
    visit_type: VisitType,
    suggested_reason: str,
    confirmed: bool = False
) -> FollowUpSlot:

    existing_slot = db.query(FollowUpSlot).filter(
        FollowUpSlot.consultation_id == consultation_id
    ).first()

    if existing_slot:
        logger.info(f"Follow-up slot for consultation_id {consultation_id} already exists. Returning existing slot ID: {existing_slot.id}")
        return existing_slot

    slot = FollowUpSlot(
        consultation_id=consultation_id,
        doctor_id=doctor_id,
        patient_id=patient_id,
        condition_detected=condition_detected,
        suggested_time=suggested_time,
        visit_type=visit_type,
        suggested_reason=suggested_reason,
        confirmed=confirmed
    )
    try:
        db.add(slot)
        db.commit()
        db.refresh(slot)
        logger.info(f"Created new follow-up slot for consultation_id {consultation_id}. Slot ID: {slot.id}")
        return slot
    except Exception as e:
         db.rollback()
         logger.error(f"Database error saving new follow-up slot for consultation {consultation_id}: {e}", exc_info=True)
         raise e