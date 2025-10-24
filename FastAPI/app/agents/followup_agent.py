from app.core.llm_client import llm
from langchain_core.messages import SystemMessage, HumanMessage
from app.core.config import settings
from app.schemas.agent_state import AgentState
from app.models.transcription_model import Transcription
from app.crud.crud_followup import save_followup_slot
from app.db.connection import get_db
from app.models.followup_model import VisitType
from datetime import datetime, timedelta
import re
import logging
from app.prompts.followup_prompts import FOLLOWUP_PROMPT as followup_prompt
logger = logging.getLogger(__name__)

class FollowUpAgent:
    def run(self, state: AgentState) -> dict:
        db = None
        try:
            if not llm:
                return {"error": "LLM client not available."}
            db = next(get_db())
            transcription = db.query(Transcription).filter(
                Transcription.consultation_id == state.consultation_id
            ).first()
            if not transcription:
                return {"error": "Consultation not found"}

            dialogue = transcription.formatted_dialogue
            messages = [
                SystemMessage(content="You assist in clinical scheduling decisions based on consultations."),
                HumanMessage(content=followup_prompt.format(dialogue=dialogue))
            ]
            content = None
            try:
                response = llm.invoke(messages)
                content = response.content.strip()
            except Exception as e:
                logger.error(f"Error calling LLM for followup analysis: {e}", exc_info=True)
                return {"error": "Failed to analyze consultation for followup."}

            condition = "Not specified"
            reason = "General Checkup"
            visit_type_str = "in_person"
            time_expr = "in 7 days"
            days = 7

            try:
                condition_match = re.search(r"Condition:\s*(.*)", content)
                if condition_match: condition = condition_match.group(1).strip()

                reason_match = re.search(r"Reason:\s*(.*)", content)
                if reason_match: reason = reason_match.group(1).strip()

                type_match = re.search(r"Type:\s*(.*)", content)
                if type_match:
                    visit_type_str_raw = type_match.group(1).strip().lower().replace("-", "_")
                    if visit_type_str_raw in ["in_person", "telehealth"]:
                        visit_type_str = visit_type_str_raw

                time_match = re.search(r"Time:\s*(.*)", content)
                if time_match: time_expr = time_match.group(1).strip()

                num_match = re.search(r"\d+", time_expr)
                num_value = int(num_match.group(0)) if num_match else 1
                if "week" in time_expr:
                    days = num_value * 7
                elif "month" in time_expr:
                     days = num_value * 30
                elif "day" in time_expr:
                    days = num_value

            except Exception as parse_error:
                 logger.warning(f"Failed to parse LLM followup output: {parse_error}. Content: '{content}'. Using defaults.")

            suggested_date = datetime.utcnow() + timedelta(days=days)

            current_doctor_id = state.doctor_id
            current_patient_id = state.patient_id

            if not current_doctor_id or not current_patient_id:
                 logger.error("Doctor ID or Patient ID missing in state for FollowUpAgent.")
                 return {"error": "Required Doctor or Patient ID is missing."}

            slot = save_followup_slot(
                db=db,
                consultation_id=state.consultation_id,
                doctor_id=current_doctor_id,
                patient_id=current_patient_id,
                condition_detected=condition,
                suggested_time=suggested_date,
                visit_type=VisitType(visit_type_str),
                suggested_reason=reason,
            )

            return {
                "consultation_id": state.consultation_id,
                "followup_id": slot.id,
                "suggested_time": slot.suggested_time,
                "visit_type": slot.visit_type.value,
                "reason": slot.suggested_reason
            }
        except Exception as e:
            logger.error(f"Error in FollowUpAgent run: {e}", exc_info=True)
            return {"error": f"An error occurred during follow-up processing: {e}"}
        finally:
             if db:
                 db.close()