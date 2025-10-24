from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableLambda
from app.schemas.agent_state import AgentState
from app.agents.education_summary_agent import EducationSummaryAgent

def run_education_summary(state: AgentState) -> dict:
    result = EducationSummaryAgent().run(state)
    return {
        **state.dict(),
        "education_summary": result.get("education_summary")
    }

summary_node = RunnableLambda(run_education_summary)

graph = StateGraph(AgentState)
graph.add_node("generate_summary", summary_node)       
graph.set_entry_point("generate_summary")              
graph.add_edge("generate_summary", END)                

education_summary_graph = graph.compile()
