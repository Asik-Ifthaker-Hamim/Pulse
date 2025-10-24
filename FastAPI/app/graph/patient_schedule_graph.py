from langgraph.graph import StateGraph, END
from app.schemas.agent_state import AgentState
from app.agents.patient_slot_finder_agent import SlotRecommendationAgent
from app.agents.patient_slot_booking_agent import PatientSlotBookingAgent
import logging

logger = logging.getLogger(__name__)

def run_slot_search_node(state: AgentState) -> dict:
    agent = SlotRecommendationAgent()
    return agent.run(state)

def run_slot_booking_node(state: AgentState) -> dict:
    agent = PatientSlotBookingAgent()
    return agent.run(state)

def should_book_slot(state: AgentState) -> str:
    if state.selected_slot_id:
        logger.debug(f"Routing to booking for slot_id: {state.selected_slot_id}")
        return "continue_to_booking"
    else:
        logger.debug("Routing to end (no slot_id selected)")
        return "end_recommendation"

workflow = StateGraph(AgentState)

workflow.add_node("search_slots", run_slot_search_node)
workflow.add_node("book_slot", run_slot_booking_node)

workflow.set_entry_point("search_slots")

workflow.add_conditional_edges(
    "search_slots",
    should_book_slot,
    {
        "continue_to_booking": "book_slot",
        "end_recommendation": END
    }
)

workflow.add_edge("book_slot", END)

patient_schedule_graph = workflow.compile()
logger.info("Patient Schedule Graph compiled.")