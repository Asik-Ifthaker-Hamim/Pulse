from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableLambda
from app.schemas.agent_state import AgentState
from app.crud.crud_transcription import save_transcription
from app.db.connection import get_db
from sqlalchemy.orm import Session
from app.models.transcription_model import Transcription
from app.agents.feedback_agent import FeedBackAgent
from app.agents.soap_prescription_agent import SOAPPrescriptionAgent
from app.agents.followup_agent import FollowUpAgent
from app.graph.education_summary_graph import education_summary_graph
from app.graph.patient_schedule_graph import patient_schedule_graph
import uuid

def save_text_node(state: AgentState) -> dict:
    db: Session = next(get_db())
    consultation_id = state.consultation_id or str(uuid.uuid4())
    existing = None
    if state.consultation_id:
        existing = db.query(Transcription).filter(
            Transcription.consultation_id == state.consultation_id
        ).first()

    try:
        if existing:
            existing.formatted_dialogue = state.formatted_dialogue
            db.commit()
            db.refresh(existing)
            return {
                "consultation_id": existing.consultation_id,
                "formatted_dialogue": existing.formatted_dialogue,
                "doctor_id": existing.doctor_id,
                "patient_id": existing.patient_id
            }
        else:
            saved = save_transcription(
                db=db,
                formatted_dialogue=state.formatted_dialogue,
                consultation_id=consultation_id,
                doctor_id=state.doctor_id,
                patient_id=state.patient_id
            )
            return {
                "consultation_id": saved.consultation_id,
                "formatted_dialogue": saved.formatted_dialogue,
                "doctor_id": saved.doctor_id,
                "patient_id": saved.patient_id
            }
    except Exception as e:
        db.rollback()
        print(f"Error in save_text_node: {e}")
        return {
             "consultation_id": consultation_id,
             "formatted_dialogue": state.formatted_dialogue,
             "doctor_id": state.doctor_id,
             "patient_id": state.patient_id,
             "error": f"DB error saving transcription: {e}" 
             }
    finally:
        db.close()


def run_feedback(state: AgentState) -> dict:
    return FeedBackAgent().run(state)

def run_soap_prescription(state: AgentState) -> dict:
    return SOAPPrescriptionAgent().run(state)

def run_followup_scheduling(state: AgentState) -> dict:
    return FollowUpAgent().run(state)

education_node = RunnableLambda(lambda state: education_summary_graph.invoke(state.dict()))
schedule_node = RunnableLambda(lambda state: patient_schedule_graph.invoke(state.dict()))

save_node = RunnableLambda(save_text_node)
feedback_node = RunnableLambda(run_feedback)
soap_node = RunnableLambda(run_soap_prescription)
followup_node = RunnableLambda(run_followup_scheduling)

graph = StateGraph(AgentState)

graph.add_node("save_text", save_node)
graph.add_node("feedback", feedback_node)
graph.add_node("soap_prescription", soap_node)
graph.add_node("followup", followup_node)
graph.add_node("education_summary_node", education_node)
graph.add_node("patient_schedule_processing", schedule_node)

graph.set_entry_point("save_text")
graph.add_edge("save_text", "feedback")
graph.add_edge("feedback", "soap_prescription")
graph.add_edge("soap_prescription", "followup")
graph.add_edge("followup", "education_summary_node")
graph.add_edge("education_summary_node", "patient_schedule_processing")
graph.add_edge("patient_schedule_processing", END)

main_graph = graph.compile()