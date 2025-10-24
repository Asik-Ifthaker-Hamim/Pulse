from app.core.llm_client import llm
from langchain_core.messages import SystemMessage, HumanMessage
from app.schemas.agent_state import AgentState
from app.core.config import settings
from app.prompts.feedback_prompts import FEEDBACK_PROMPT_TEMPLATE as prompt_template

class FeedBackAgent:
    def run(self, state: AgentState) -> dict:
        if not llm:
             return {"error": "LLM client not available."}
        messages = [
            SystemMessage(content="You're a senior clinical assistant providing feedback."),
            HumanMessage(content=prompt_template.format(dialogue=state.formatted_dialogue))
        ]
        try:
            response = llm.invoke(messages)
            analysis = response.content.strip()
        except Exception as e:
            print(f"Error calling LLM for prompter analysis: {e}")
            analysis = "Error: Could not analyze conversation."

        return {
            "consultation_id": state.consultation_id,
            "formatted_dialogue": state.formatted_dialogue,
            "analysis_feedback": analysis
        }