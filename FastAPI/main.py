from fastapi import FastAPI
from app.api import (
    consultation_processing, chatbot, education_summary,
    patient_schedule, patient_management, doctor_management
)
from app.db.connection import engine, Base
from app.models import (
    transcription_model, soap_prescription_model, followup_model,
    schedule_model, patient_model, doctor_model
)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI-Enhanced Clinical Consultation and Documentation System",
    description="An AI system for clinical consultations and documentation.",
    version="0.1.0"
)
app.include_router(patient_management.router, prefix="/api", tags=["Patient Management"])
app.include_router(doctor_management.router, prefix="/api", tags=["Doctor Management"])
app.include_router(patient_schedule.router, prefix="/api", tags=["Schedule Management"])
app.include_router(consultation_processing.router, prefix="/api/consultation", tags=["Consultation Processing & Review"])
app.include_router(chatbot.router, prefix="/api", tags=["Doctor Chatbot"])
app.include_router(education_summary.router, prefix="/api/education", tags=["Patient Education"])


@app.get("/")
def root():
    return {
        "message": (
            "Endpoints:\n"
            # --- Registration & Management ---
            "- POST /api/patients/register → Register a new patient\n"
            "- GET  /api/patients/ → Get list of all patients\n"
            "- POST /api/doctors/register → Register a new doctor profile\n"
            "- GET  /api/doctors/ → Get list of all doctor profiles\n"
            # --- Scheduling ---
            "- POST /api/schedule/doctor-availability → Doctor submits free time slots\n"
            "- POST /api/schedule/recommend-slot → Patient requests slot recommendations\n" 
            "- POST /api/schedule/book-slot → Patient books a selected slot\n"
            # --- Consultation Flow ---
            "- POST /api/consultation/text-transcription → Submit conversation\n"
            "- POST /api/consultation/review-transcription → Review & update conversation\n"
            "- POST /api/consultation/generate-soap-prescription → Generate SOAP note and prescription\n"
            "- POST /api/consultation/generate-followup → Generate and store follow-up appointment slot\n"
            "- POST /api/education/generate-education-summary → Generate health education summary\n"
            # --- Chatbot ---
            "- POST /api/chatbot → Doctor chatbot (e.g., check schedule, ask questions)\n"
        )
    }