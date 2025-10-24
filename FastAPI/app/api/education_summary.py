from fastapi import APIRouter, Form, HTTPException
from app.schemas.agent_state import AgentState
from app.graph.education_summary_graph import education_summary_graph
from app.schemas.consultation_schema import EducationSummaryResponse

router = APIRouter()

@router.post(
    "/generate-education-summary",
    response_model=EducationSummaryResponse
)
def generate_education_summary(
    consultation_id: str = Form(...)
):
    initial_state = AgentState(consultation_id=consultation_id)
    try:
        result = education_summary_graph.invoke(initial_state.dict())
        return EducationSummaryResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating education summary: {e}")