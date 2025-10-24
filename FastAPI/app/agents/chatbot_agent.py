from sqlalchemy.orm import Session
from app.db.connection import get_db
from app.services import chatbot_utils, medical_knowledge_tool
from app.utils.email_helper import send_followup_confirmation_email
from app.crud.crud_patient import get_patient_by_id
from app.crud.crud_doctor import get_doctor_by_id
from app.schemas.chatbot_schema import ChatbotResponse
from app.schemas.knowledge_schema import MedicalKnowledgeOutput
from app.core.llm_client import llm
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.tools import tool
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.agents import AgentAction, AgentFinish
from pydantic import UUID4
from app.prompts.chatbot_prompts import CHATBOT_SYSTEM_PROMPT
import logging
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

@tool
def get_doctor_schedule(doctor_id: UUID4) -> dict:
    """
    Gets the upcoming schedule for the specified doctor ID (UUID).
    Returns a dictionary containing a list of appointments under the key 'schedule_details',
    or a message under the key 'message' if no appointments are found,
    or an error message under the key 'error'.
    """
    db: Session = next(get_db())
    try:
        schedule = chatbot_utils.query_upcoming_schedule(db, str(doctor_id))
        if not schedule:
            return {"message": "No upcoming appointments found."}
        serializable_schedule = []
        for item in schedule:
            item_copy = item.copy()
            item_copy['time'] = item_copy['time'].isoformat() if isinstance(item_copy.get('time'), datetime) else item_copy.get('time')
            serializable_schedule.append(item_copy)
        return {"schedule_details": serializable_schedule}
    except Exception as e:
        logger.error(f"Error fetching schedule for doctor {doctor_id}: {e}", exc_info=True)
        return {"error": f"Failed to retrieve schedule: {e}"}
    finally:
        if db: db.close()

@tool
def confirm_next_appointment(doctor_id: UUID4) -> dict:
    """
    Confirms the doctor's next unconfirmed follow-up appointment based on the provided doctor ID (UUID).
    It updates the appointment status in the database and attempts to send a confirmation email.
    Returns a dictionary containing confirmation details under the key 'confirmation_details',
    a status message under the key 'confirmation_status' if no appointment is found,
    or an error message under the key 'error'.
    """
    db: Session = next(get_db())
    try:
        slot = chatbot_utils.confirm_next_unconfirmed(db, str(doctor_id))
        if not slot:
            return {"confirmation_status": "No unconfirmed appointments found to confirm."}
        patient = get_patient_by_id(db, slot.patient_id)
        doctor = get_doctor_by_id(db, slot.doctor_id)
        email_status = "Could not retrieve full patient/doctor details for email."
        patient_contact = "N/A"
        doc_designation = "N/A"
        doc_education = "N/A"
        doc_location = "N/A"
        if patient:
            patient_contact = patient.contact_number or "N/A"
        if doctor:
            doc_designation = doctor.designation or "N/A"
            doc_education = doctor.education or "N/A"
            doc_location = doctor.location or "N/A"
        if patient and doctor:
             try:
                send_followup_confirmation_email(
                    patient_email=patient.email, doctor_email=doctor.email,
                    patient_name=patient.name, doctor_name=doctor.name,
                    followup_time=slot.suggested_time, visit_type=slot.visit_type.value,
                    reason=slot.suggested_reason,
                    doctor_designation=doc_designation,
                    doctor_education=doc_education,
                    doctor_location=doc_location,
                    patient_contact_number=patient_contact,
                    doctor_id=doctor.id,
                    patient_id=patient.id
                )
                email_status = "Confirmation email sent successfully."
             except Exception as mail_error:
                 logger.error(f"Failed to send followup confirmation email: {mail_error}", exc_info=True)
                 email_status = "Attempted to send confirmation email, but failed."
        else:
             logger.warning(f"Could not find full patient ({slot.patient_id}) or doctor ({slot.doctor_id}) details for email confirmation.")
        confirmation_details = (
            f"Follow-up on {slot.suggested_time.strftime('%Y-%m-%d %H:%M')} "
            f"({slot.visit_type.value}) for {patient.name if patient else 'patient ID '+str(slot.patient_id)}. "
            f"Reason: {slot.suggested_reason}. Status: Confirmed. Email Status: {email_status}"
        )
        return {"confirmation_details": confirmation_details}
    except Exception as e:
        logger.error(f"Error confirming appointment for doctor {doctor_id}: {e}", exc_info=True)
        return {"error": f"Failed to confirm appointment: {e}"}
    finally:
        if db: db.close()

@tool
def answer_medical_question(question: str) -> dict:
    """
    Answers a general medical, medicine, or health-related question using external knowledge search.
    Returns a dictionary representing the MedicalKnowledgeOutput structure.
    """
    knowledge_output: MedicalKnowledgeOutput = medical_knowledge_tool.get_medical_knowledge(question)
    return knowledge_output.model_dump()

tools = [get_doctor_schedule, confirm_next_appointment, answer_medical_question]

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", CHATBOT_SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)

agent_executor = None
if llm:
    openai_functions_agent = create_openai_functions_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(
        agent=openai_functions_agent,
        tools=tools,
        verbose=True,
        return_intermediate_steps=True
    )

class DoctorChatbotAgent:
    def run(self, doctor_id: UUID4, message: str, chat_history: Optional[List[Dict[str, str]]] = None) -> ChatbotResponse:
        if not agent_executor:
            logger.error("Chatbot agent executor not initialized.")
            return ChatbotResponse(response_type="error", error_message="Chatbot agent not initialized.")

        processed_history = []
        if chat_history:
            logger.info(f"Processing chat history with {len(chat_history)} entries for doctor {doctor_id}")
            for msg in chat_history:
                role = msg.get("role")
                content = msg.get("content")
                if not content:
                     continue
                if role == "user":
                    processed_history.append(HumanMessage(content=content))
                elif role == "assistant":
                    processed_history.append(AIMessage(content=content))
        else:
             logger.info(f"No chat history provided for doctor {doctor_id}")


        input_data = {
            "input": message,
            "chat_history": processed_history,
        }

        try:
            logger.info(f"Invoking agent executor for doctor {doctor_id} with input: {message}")
            result = agent_executor.invoke(input_data)
            agent_output_text = result.get("output", "Sorry, I could not process that request.")
            intermediate_steps = result.get("intermediate_steps", [])
            logger.info(f"Agent execution finished for doctor {doctor_id}. Output: {agent_output_text[:100]}...")

            response_type = "general"
            schedule_data_list = None
            knowledge_result_data = None

            if intermediate_steps:
                last_step = intermediate_steps[-1]
                action, observation = last_step
                logger.info(f"Agent last step - Tool: {action.tool}, Observation type: {type(observation)}")

                if isinstance(observation, dict):
                    if action.tool == "get_doctor_schedule":
                        response_type = "schedule"
                        schedule_data_list = observation.get("schedule_details")
                        logger.info(f"Schedule data found: {schedule_data_list}")
                    elif action.tool == "confirm_next_appointment":
                        response_type = "confirmation"
                        logger.info(f"Confirmation data: {observation.get('confirmation_details') or observation.get('confirmation_status')}")
                    elif action.tool == "answer_medical_question":
                        response_type = "knowledge"
                        try:
                             knowledge_result_data = MedicalKnowledgeOutput(**observation)
                             logger.info(f"Knowledge data parsed successfully for question: {knowledge_result_data.original_question}")
                        except Exception as parse_error:
                             logger.warning(f"Could not parse knowledge tool output: {parse_error}")
                             agent_output_text += "\n(Note: Could not fully parse knowledge details.)"
                else:
                     logger.warning(f"Observation from tool '{action.tool}' was not a dict: {observation}")

            if isinstance(schedule_data_list, list):
                 schedule_data_list = [
                      {k: (v.isoformat() if isinstance(v, datetime) else v) for k, v in item.items()}
                      for item in schedule_data_list
                 ]

            return ChatbotResponse(
                response_type=response_type,
                text_response=agent_output_text,
                schedule_data=schedule_data_list,
                knowledge_data=knowledge_result_data
            )

        except Exception as e:
            logger.error(f"Error running chatbot agent executor for doctor {doctor_id}: {e}", exc_info=True)
            return ChatbotResponse(response_type="error", error_message=f"An internal error occurred: {e}")