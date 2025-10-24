from fastapi import (
    APIRouter, Form, HTTPException, Depends, status,
    File, UploadFile
)
from sqlalchemy.orm import Session
from pydantic import UUID4, BaseModel
import uuid
import logging
from typing import Optional
from app.graph.main_graph import main_graph
from app.db.connection import get_db
from app.schemas.agent_state import AgentState
from app.models.transcription_model import Transcription
from app.schemas.consultation_schema import (
    TranscriptionAnalysisResponse, ReviewResponse, SOAPResponse, FollowupResponse
)
from app.services.transcription_service import transcribe_audio_openai

logger = logging.getLogger(__name__)
router = APIRouter()

class TranscriptionTextResponse(BaseModel):
    transcription: str

@router.post(
    "/transcribe-audio",
    response_model=TranscriptionTextResponse,
    tags=["Consultation Processing & Review"]
)
async def handle_audio_transcription(
    audio_file: UploadFile = File(..., description="Audio file to be transcribed."),
    language: str = Form('en', description="Language code (e.g., 'en', 'es', 'hi'). Defaults to 'en'.")
):
    logger.info(f"Received audio file: {audio_file.filename}, type: {audio_file.content_type}, target language: {language}")
    allowed_audio_types = ["audio/wav", "audio/mpeg", "audio/mp4", "audio/ogg", "audio/flac", "audio/aac", "audio/webm", "audio/x-m4a"]

    try:
        transcribed_text = await transcribe_audio_openai(audio_file, language=language)
        logger.info(f"Transcription successful for {audio_file.filename}. Length: {len(transcribed_text)}")
        return TranscriptionTextResponse(transcription=transcribed_text)
    except ValueError as ve:
         logger.error(f"Configuration error during transcription: {ve}")
         raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(ve))
    except ConnectionError as ce:
         logger.error(f"API connection error during transcription: {ce}")
         raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=str(ce))
    except RuntimeError as re:
         logger.error(f"Runtime error during transcription: {re}")
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(re))
    except Exception as e:
        logger.error(f"Unexpected error during transcription: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred during transcription: {e}")

@router.post(
    "/text-transcription",
    response_model=TranscriptionAnalysisResponse
)
def text_ingest(
    formatted_dialogue: str = Form(...),
    doctor_id: UUID4 = Form(...),
    patient_id: UUID4 = Form(...),
    consultation_id: Optional[str] = Form(None),
):
    initial_state = AgentState(
        consultation_id=consultation_id,
        formatted_dialogue=formatted_dialogue,
        doctor_id=doctor_id,
        patient_id=patient_id
    )
    try:
        final_state_dict = main_graph.invoke(initial_state.dict())
        return TranscriptionAnalysisResponse(**final_state_dict)
    except Exception as e:
        logger.error(f"Error processing text transcription: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing transcription: {e}")

@router.post("/review-transcription", response_model=ReviewResponse)
def review_transcription_flow(
    consultation_id: str = Form(...),
    updated_dialogue: str = Form(...),
    db: Session = Depends(get_db)
):
    transcription = db.query(Transcription).filter(
        Transcription.consultation_id == consultation_id
    ).first()
    if not transcription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consultation ID not found")

    merged_dialogue = transcription.formatted_dialogue.strip() + "\n\n---\n\n" + updated_dialogue.strip()
    transcription.formatted_dialogue = merged_dialogue
    db.commit()
    db.refresh(transcription)
    logger.info(f"Appended dialogue to consultation ID: {consultation_id}")
    return ReviewResponse(
        consultation_id=consultation_id,
        formatted_dialogue=merged_dialogue
    )

@router.post("/generate-soap-prescription", response_model=SOAPResponse)
def generate_soap_prescription(
    consultation_id: str = Form(...)
):
    from app.agents.soap_prescription_agent import SOAPPrescriptionAgent
    initial_state = AgentState(consultation_id=consultation_id)
    try:
        logger.info(f"Generating SOAP/Rx for consultation ID: {consultation_id}")
        result = SOAPPrescriptionAgent().run(initial_state)
        return SOAPResponse(**result)
    except Exception as e:
        logger.error(f"Error generating SOAP/Rx for {consultation_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating SOAP/prescription: {e}")

@router.post("/generate-followup", response_model=FollowupResponse)
def generate_followup_slot(
    consultation_id: str = Form(...)
):
    from app.agents.followup_agent import FollowUpAgent
    db = None
    try:
        db = next(get_db())
        transcription = db.query(Transcription).filter(Transcription.consultation_id == consultation_id).first()
        if not transcription:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consultation ID not found for followup generation")
        if not transcription.doctor_id or not transcription.patient_id:
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Doctor/Patient ID missing for this consultation")

        initial_state = AgentState(
             consultation_id=consultation_id,
             doctor_id=transcription.doctor_id,
             patient_id=transcription.patient_id
        )
        logger.info(f"Generating Followup for consultation ID: {consultation_id}")
        result = FollowUpAgent().run(initial_state)
        return FollowupResponse(**result)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error generating Followup for {consultation_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating Followup: {e}")
    finally:
        if db:
            db.close()