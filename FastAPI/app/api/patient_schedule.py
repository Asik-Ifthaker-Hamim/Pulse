from fastapi import APIRouter, Form, Depends, HTTPException, status, Path, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid
import logging

from app.db.connection import get_db
from app.models.schedule_model import DoctorSlot
from app.schemas.agent_state import AgentState
from app.graph.patient_schedule_graph import patient_schedule_graph
from app.crud.crud_doctor import get_doctor_by_id
from app.crud.crud_schedule import get_slots_by_doctor_id
from app.schemas.schedule_schema import SlotRead

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post(
    "/schedule/doctor-availability",
    status_code=status.HTTP_201_CREATED
)
def add_doctor_slot(
    doctor_id_str: str = Form(..., alias="doctor_id"),
    start_time: datetime = Form(...),
    end_time: datetime = Form(...),
    slot_location: Optional[str] = Form(None, alias="location"),
    db: Session = Depends(get_db)
):
    logger.info(f"Received request to add slot for Doctor ID string: {doctor_id_str}")
    if start_time >= end_time:
        logger.warning(f"Validation failed: Start time {start_time} not before end time {end_time}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Start time must be before end time.")
    try:
        doctor_uuid = uuid.UUID(doctor_id_str)
    except ValueError:
         logger.error(f"Invalid Doctor ID format provided: {doctor_id_str}")
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid Doctor ID format: {doctor_id_str}")
    doctor = get_doctor_by_id(db, doctor_uuid)
    if not doctor:
        logger.error(f"Doctor profile not found for ID: {doctor_uuid}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Doctor with ID {doctor_uuid} not found.")
    logger.info(f"Found doctor details: {doctor.name} (ID: {doctor.id})")
    slot = DoctorSlot(
        doctor_id=str(doctor.id),
        name=doctor.name,
        education=doctor.education,
        designation=doctor.designation,
        location=slot_location or doctor.location or "Clinic Default",
        start_time=start_time,
        end_time=end_time,
        doctor_email=doctor.email,
        is_booked=False
    )
    try:
        db.add(slot)
        db.commit()
        db.refresh(slot)
        logger.info(f"Doctor slot ID {slot.id} added successfully for Dr. {doctor.name}")
        return {"message": "Slot added successfully.", "slot_id": str(slot.id)}
    except Exception as e:
        logger.error(f"Database error while adding slot for Dr. {doctor.name}: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save doctor availability slot.")


@router.post("/schedule/recommend-slot")
def recommend_slot(
    patient_query: str = Form(...),
    patient_query_date: Optional[str] = Form(None),
    patient_query_time: Optional[str] = Form(None),
    patient_query_designation: Optional[str] = Form(None),
):
    initial_state = AgentState(
        patient_query=patient_query, patient_query_date=patient_query_date,
        patient_query_time=patient_query_time, patient_query_designation=patient_query_designation,
        selected_slot_id=None,
        available_slots=None,
        recommendation=None
    )
    logger.debug(f"Invoking patient schedule graph for recommendation with initial state: {initial_state.dict()}")
    try:
        final_state_dict = patient_schedule_graph.invoke(initial_state.dict())
        logger.debug(f"Graph invocation for recommendation successful. Final state: {final_state_dict}")
        return {
            "recommendation": final_state_dict.get("recommendation", "Error: Recommendation processing failed."),
            "available_slots": final_state_dict.get("available_slots", [])
        }
    except Exception as e:
        logger.error(f"Error invoking patient schedule graph for recommendation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get slot recommendations due to an internal error.")


@router.post("/schedule/book-slot")
def book_slot(
    selected_slot_id: str = Form(...),
    patient_name: str = Form(...),
    patient_email: str = Form(...),
    patient_id: str = Form(...),
):
    try:
        slot_uuid = uuid.UUID(selected_slot_id)
    except ValueError:
        logger.warning(f"Booking attempt with invalid slot ID format: {selected_slot_id}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid slot ID format provided.")
    if not patient_name or not patient_email or not patient_id:
         logger.warning("Booking attempt missing required patient details.")
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Patient name, email, and ID are required for booking.")
    try:
        patient_uuid = uuid.UUID(patient_id)
    except ValueError:
        logger.warning(f"Booking attempt with invalid patient ID format: {patient_id}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid patient ID format provided.")
    initial_state = AgentState(
        selected_slot_id=str(slot_uuid),
        patient_name=patient_name,
        patient_email=patient_email,
        patient_id=str(patient_uuid)
    )
    logger.debug(f"Invoking patient schedule graph for booking: {initial_state.dict()}")
    try:
        final_state_dict = patient_schedule_graph.invoke(initial_state.dict())
        logger.debug(f"Graph invocation for booking successful: {final_state_dict}")
        return {
            "slot_id": selected_slot_id,
            "confirmation": final_state_dict.get("booking_confirmation", "Booking status uncertain.")
        }
    except Exception as e:
         logger.error(f"Error invoking patient schedule graph for booking slot {selected_slot_id}: {e}", exc_info=True)
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to process booking for slot {selected_slot_id} due to an internal error.")


@router.get(
    "/schedule/doctor/{doctor_id_str}/slots",
    response_model=List[SlotRead],
    tags=["Schedule Management"]
)
def view_doctor_slots(
    doctor_id_str: str = Path(..., description="The UUID of the doctor whose slots to retrieve"),
    show_booked: bool = Query(True, description="Include booked slots in the results"),
    db: Session = Depends(get_db)
):
    logger.info(f"Request received to view slots for doctor ID: {doctor_id_str}")
    try:
        doctor_uuid = uuid.UUID(doctor_id_str)
    except ValueError:
        logger.warning(f"Invalid UUID format for doctor ID: {doctor_id_str}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Doctor ID format.")
    try:
        slots = get_slots_by_doctor_id(db=db, doctor_id=doctor_uuid, include_booked=show_booked)
        logger.info(f"Retrieved {len(slots)} slots for doctor ID: {doctor_uuid}")
        return slots
    except Exception as e:
        logger.error(f"Error retrieving slots for doctor {doctor_uuid}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve doctor slots.")