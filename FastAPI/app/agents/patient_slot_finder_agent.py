from app.core.llm_client import llm
from langchain_core.messages import SystemMessage, HumanMessage
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from app.db.connection import get_db
from app.models.schedule_model import DoctorSlot
from app.schemas.agent_state import AgentState
from app.core.config import settings
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
logger.setLevel(logging.INFO)

class SlotRecommendationAgent:
    def run(self, state: AgentState) -> Dict[str, Any]:
        db: Session = next(get_db())
        llm_recommendation_text = "Could not find any matching slots. Please broaden your search or try different criteria."
        available_slots_list: List[Dict[str, Any]] = []
        return_data = {
            "available_slots": [],
            "recommendation": "Search error occurred."
        }

        try:
            logger.info(f"SlotRecommendationAgent running for query: {state.patient_query}")
            query = db.query(DoctorSlot).filter(DoctorSlot.is_booked == False)

            log_filters = ["is_booked == False"]
            parsed_date = None
            if state.patient_query_date:
                try:
                    parsed_date = datetime.strptime(state.patient_query_date, '%Y-%m-%d').date()
                    query = query.filter(func.date(DoctorSlot.start_time) == parsed_date)
                    log_filters.append(f"date == {parsed_date}")
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid date format: '{state.patient_query_date}'. Ignoring date filter. Error: {e}")
            if state.patient_query_time:
                if parsed_date:
                    parsed_time = None
                    try:
                        parsed_time = datetime.strptime(state.patient_query_time, '%H:%M:%S').time()
                    except ValueError:
                        try:
                            parsed_time = datetime.strptime(state.patient_query_time, '%H:%M').time()
                        except (ValueError, TypeError) as e:
                             logger.warning(f"Invalid time format: '{state.patient_query_time}'. Ignoring time filter. Error: {e}")
                    if parsed_time:
                         target_dt = datetime.combine(parsed_date, parsed_time)
                         query = query.filter(DoctorSlot.start_time >= target_dt)
                         log_filters.append(f"start_time >= {target_dt}")
                else:
                    logger.warning(f"Time filter '{state.patient_query_time}' provided but no valid date. Ignoring time filter.")
            if state.patient_query_designation:
                designation_pattern = f"%{state.patient_query_designation}%"
                query = query.filter(DoctorSlot.designation.ilike(designation_pattern))
                log_filters.append(f"designation ilike {designation_pattern}")

            logger.info(f"Applied filters: {', '.join(log_filters)}")
            query = query.order_by(DoctorSlot.start_time)
            slots = query.all()

            logger.info(f"Database query returned {len(slots)} slots.")

            if slots:
                slot_list_str_for_llm = ""
                for s in slots:
                    slot_dict = {
                        "id": str(s.id),
                        "start_time": s.start_time.isoformat(),
                        "end_time": s.end_time.isoformat(),
                        "doctor_name": s.name,
                        "designation": s.designation,
                        "location": s.location
                    }
                    available_slots_list.append(slot_dict)
                    slot_info_str = (
                        f"Slot ID: {s.id}, Time: {s.start_time.strftime('%Y-%m-%d %H:%M')} - {s.end_time.strftime('%H:%M')}, "
                        f"Doctor: {s.name}, Specialty: {s.designation}, Location: {s.location}"
                    )
                    slot_list_str_for_llm += slot_info_str + "\n"

                if llm:
                    try:
                        llm_prompt_content = (
                             f"Patient query: '{state.patient_query}'.\n\n"
                             f"Based on this query and the following available appointments, "
                             f"briefly advise if a consultation seems appropriate and suggest which type of doctor might be suitable.\n\n"
                             f"Available Slots:\n{slot_list_str_for_llm.strip()}"
                        )
                        messages = [
                            SystemMessage(content="You are a helpful assistant analyzing patient queries and available doctor slots. Provide brief advice on consultation appropriateness and suggest a suitable doctor type based *only* on the query and available options. Be concise."),
                            HumanMessage(content=llm_prompt_content)
                        ]
                        response = llm.invoke(messages)
                        llm_recommendation = response.content.strip()
                        llm_recommendation_text = f"💡 Recommendation: {llm_recommendation}"
                        logger.info("LLM recommendation generated.")
                    except Exception as e:
                        logger.error(f"Error calling LLM for recommendation: {e}", exc_info=True)
                        llm_recommendation_text = "⚠️ Could not generate AI recommendation (LLM error)."
                else:
                     llm_recommendation_text = "⚠️ AI recommendation service not available."
            else:
                llm_recommendation_text = "No available slots found matching your specific criteria. You might try broadening your search."

            return_data["available_slots"] = available_slots_list
            return_data["recommendation"] = llm_recommendation_text

        except Exception as e:
            logger.error(f"Error during slot recommendation processing: {e}", exc_info=True)
            return_data["recommendation"] = "An internal error occurred while searching for slots."
            return_data["available_slots"] = []

        finally:
            if db: db.close()
            logger.info(f"SlotRecommendationAgent finished. Returning {len(return_data['available_slots'])} slots.")
            return return_data