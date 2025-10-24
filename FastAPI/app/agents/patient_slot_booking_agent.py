from sqlalchemy.orm import Session
from app.db.connection import get_db
from app.models.schedule_model import DoctorSlot, Appointment
from app.models.patient_model import Patient
from app.utils.email_helper import send_appointment_email
from app.schemas.agent_state import AgentState
import logging
import uuid

logger = logging.getLogger(__name__)

class PatientSlotBookingAgent:
    def run(self, state: AgentState) -> dict:
        db: Session = next(get_db())
        confirmation_message = "❌ Booking failed. Please check inputs or try again."
        db_session_active = True 

        if not state.selected_slot_id:
             logger.warning("Booking attempt failed: No selected_slot_id provided.")
             confirmation_message = "❌ Booking failed: Slot ID was missing."
             db.close() 
             return {"booking_confirmation": confirmation_message}
        try:
            slot_uuid = uuid.UUID(state.selected_slot_id)
        except ValueError:
            logger.warning(f"Booking attempt failed: Invalid UUID format: {state.selected_slot_id}")
            confirmation_message = f"❌ Booking failed: Invalid Slot ID format provided."
            db.close()
            return {"booking_confirmation": confirmation_message}

        patient_contact = "N/A"
        patient_id_uuid = None
        if state.patient_id:
             try:
                 patient_id_uuid = uuid.UUID(str(state.patient_id))
                 patient_profile = db.query(Patient).filter(Patient.id == patient_id_uuid).first()
                 if patient_profile:
                     patient_contact = patient_profile.contact_number or "N/A"
                 else:
                     logger.warning(f"Could not find patient profile for ID {state.patient_id} during booking.")
             except ValueError:
                 logger.error(f"Invalid patient_id format in state: {state.patient_id}")
                 db.close()
                 return {"booking_confirmation": "❌ Booking failed: Invalid Patient ID format."}
             except Exception as fetch_err:
                 logger.error(f"Error fetching patient profile {state.patient_id}: {fetch_err}")
        else:
            logger.warning("Patient ID missing in state, cannot fetch contact number for email.")
            db.close()
            return {"booking_confirmation": "❌ Booking failed: Patient ID missing."}


        try:
            slot = db.query(DoctorSlot).filter(
                DoctorSlot.id == slot_uuid,
                DoctorSlot.is_booked == False
            ).with_for_update().first() 

            if not slot:
                logger.warning(f"Attempt to book non-existent/booked slot: {state.selected_slot_id}")
                confirmation_message = f"❌ Slot ID {state.selected_slot_id} not found or is already booked."
            else:
                slot.is_booked = True
                appt = Appointment(
                    slot_id=slot.id,
                    patient_id=patient_id_uuid,
                    patient_name=state.patient_name,
                    patient_email=state.patient_email,
                    doctor_email=slot.doctor_email,
                    status="confirmed"
                )
                db.add(appt)
                db.commit() 
                db.refresh(appt)
                logger.info(f"Appointment {appt.id} created for patient {appt.patient_id}, slot {slot.id} booked.")
                db_session_active = False 

                try:
                    send_appointment_email(
                        patient_email=appt.patient_email,
                        doctor_email=appt.doctor_email,
                        patient_name=appt.patient_name,
                        doctor_name=slot.name,
                        start_time=slot.start_time,
                        end_time=slot.end_time,
                        doctor_designation=slot.designation,
                        doctor_education=slot.education,
                        doctor_location=slot.location,
                        patient_contact_number=patient_contact,
                        doctor_id=slot.doctor_id,
                        patient_id=appt.patient_id
                    )
                    logger.info(f"Confirmation email sent for appointment {appt.id}")
                    confirmation_message = f"✅ Appointment booked for {slot.start_time.strftime('%Y-%m-%d %H:%M')} with Dr. {slot.name} ({slot.designation}). Confirmation sent to {appt.patient_email}."

                except Exception as mail_error:
                    logger.error(f"Failed to send confirmation email for appt {appt.id}: {mail_error}", exc_info=True)
                    confirmation_message = f"✅ Appointment booked successfully for {slot.start_time.strftime('%Y-%m-%d %H:%M')}, but failed to send confirmation email to {appt.patient_email}."

        except Exception as e:
            logger.error(f"Error during slot booking process for slot {state.selected_slot_id}: {e}", exc_info=True)
            if db_session_active: 
                 db.rollback()
            confirmation_message = f"❌ An internal error occurred during booking for slot {state.selected_slot_id}. Please try again."
        finally:
            if db:
                db.close()

        return {"booking_confirmation": confirmation_message}