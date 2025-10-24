from app.core.llm_client import llm
from langchain_core.messages import SystemMessage, HumanMessage
from app.db.connection import get_db
from app.models.transcription_model import Transcription
from app.core.config import settings
from app.schemas.agent_state import AgentState
from sqlalchemy.orm import Session
from app.prompts.education_prompts import EDUCATION_PROMPT as education_prompt

class EducationSummaryAgent:
    def run(self, state: AgentState) -> dict:
        if not llm:
             return {"error": "LLM client not available."}
        db: Session = next(get_db())
        transcription = db.query(Transcription).filter(
            Transcription.consultation_id == state.consultation_id
        ).first()
        if not transcription:
            return {"error": "Consultation not found"}

        dialogue = transcription.formatted_dialogue
        messages = [
            SystemMessage(content="You help patients understand their diagnosis and treatment."),
            HumanMessage(content=education_prompt + f"\n\nConversation:\n{dialogue}")
        ]
        try:
            response = llm.invoke(messages)
            summary = response.content.strip()
        except Exception as e:
             print(f"Error calling LLM for education summary: {e}")
             summary = "Error: Could not generate education summary."

        return {
            "consultation_id": state.consultation_id,
            "education_summary": summary
        }