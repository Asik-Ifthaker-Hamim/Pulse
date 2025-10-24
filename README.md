# Pulse

An AI-powered clinical assistant built using LangGraph, FastAPI, LangChain, and OpenAI that streamlines doctor-patient interactions — from transcription analysis to SOAP notes, prescription validation, follow-up suggestions, chatbot assistance, patient education, and appointment booking.

📌 **Introduction**

Doctors often face time constraints in documenting patient interactions, generating prescriptions, scheduling follow-ups, and educating patients. This project automates and optimizes the clinical workflow using AI agents that analyze consultations, generate clinical notes, validate medications, suggest follow-ups, provide health summaries, and manage appointments. It utilizes LangGraph for orchestration and follows a structured project layout (API, Agents, CRUD, Schemas, Prompts, Utils) for maintainability.

🚀 **Key Features**

1.  **📝 Transcription Ingestion & Analysis:**
    *   Accepts doctor-patient conversation text via API (`/api/langgraph/text-transcription`).
    *   Requires associated `doctor_id` and `patient_id` (UUIDs) for context and storage linkage.
    *   Saves or updates transcriptions in the database (`crud_transcription`).
    *   Analyzes conversations for missed clinical questions and feedback using `FeedBackAgent` (prompts stored in `app/prompts/`).

2.  **💊 SOAP Note & Prescription Generation:**
    *   Generates SOAP notes and draft prescriptions using `SOAPPrescriptionAgent` (prompt in `app/prompts/`).
    *   Extracts all mentioned medications from the draft using LLM guidance and regex.
    *   Validates each extracted medication against the OpenFDA database.
    *   Appends a structured validation report to the SOAP/prescription report.
    *   Saves the complete report (`crud_soap_prescription`).

3.  **📆 Follow-Up Suggestion & Scheduling:**
    *   Analyzes consultation context using `FollowUpAgent` (prompt in `app/prompts/`).
    *   Suggests timeframe, visit type (in-person/telehealth), condition, and reason.
    *   Saves the suggested follow-up slot (`crud_followup`), preventing duplicates for the same consultation ID.

4.  **🤖 Doctor Chatbot Assistant:**
    *   Provides an interactive chat interface (`/api/chatbot`).
    *   Uses a LangChain Agent (`AgentExecutor` with `create_openai_functions_agent`) powered by `gpt-4o`.
    *   Equipped with tools (`app/agents/chatbot_agent.py`) interacting with `crud` functions and external services:
        *   `get_doctor_schedule`: Retrieves upcoming follow-ups (requires `doctor_id`).
        *   `confirm_next_appointment`: Confirms the next unconfirmed follow-up, updates DB, and sends detailed confirmation emails with Google Meet link generation for telehealth (requires `doctor_id`).
        *   `answer_medical_question`: Answers general medical questions using Tavily web search and LLM synthesis (`medical_knowledge_tool`).
    *   Returns structured `ChatbotResponse` based on tool usage inspection.

5.  **📚 Health Education Summary:**
    *   Generates a patient-friendly summary using `EducationSummaryAgent` (prompt in `app/prompts/`).
    *   Triggered via API (`/api/langgraph/generate-education-summary`).

6.  **👤 Patient & Doctor Profile Management:**
    *   API endpoints to register new patients (`/api/patients/register`) and doctors (`/api/doctors/register`) using `crud` functions, ensuring uniqueness based on *all* provided profile details.
    *   API endpoints to retrieve lists of all registered patients (`/api/patients/`) and doctors (`/api/doctors/`).

7.  **🗓️ Appointment Scheduling System:**
    *   Doctors submit available time slots (`/api/schedule/doctor-availability`).
    *   Patients request slot recommendations (`/api/schedule/recommend-slot`).
    *   Patients book slots (`/api/schedule/book-slot`), triggering `PatientSlotBookingAgent` which updates DB and sends detailed confirmation emails.

🛠️ **Tech Stack / Tools Used**

| Component            | Technology Used                             |
| :------------------- | :------------------------------------------ |
| Backend Framework    | FastAPI                                     |
| Orchestration        | LangGraph                                   |
| LLM Integration      | LangChain (`ChatOpenAI`, Agents, Tools)      |
| LLM Model            | OpenAI GPT-4o                               |
| Web Search           | Tavily API (via LangChain tool)             |
| Drug Validation      | OpenFDA API                                 |
| Calendar Integration | Google Calendar API (via Client Library)    |
| Database             | PostgreSQL                                  |
| ORM                  | SQLAlchemy                                  |
| Schema Validation    | Pydantic                                    |
| Email                | SMTP (e.g., Gmail App Password)             |

🧩 **Workflow Architecture**


[Workflow Diagram](docs/images/updated_workflow.png) 

*   **Brief Text Summary:** The system primarily processes consultations through `main_graph`. This saves text, runs analysis (`FeedBackAgent`), generates SOAP/Rx with validation (`SOAPPrescriptionAgent`), suggests follow-ups (`FollowUpAgent`), and triggers subgraphs for education (`EducationSummaryGraph`) and scheduling (`PatientScheduleGraph`). A separate `DoctorChatbotAgent` uses tools for schedule checks, confirmations (with Google Meet link generation), and medical Q&A. Database operations are handled via dedicated `crud` modules.

📡 **API Endpoints**

1.  **Register Patient**
    *   `POST /api/patients/register`
    *   Input: JSON Body (`PatientCreate`: name, email, contact\_number, etc.)
    *   Output: JSON (`PatientRead`: includes patient `id`)
2.  **List Patients**
    *   `GET /api/patients/`
    *   Input: None
    *   Output: List `[PatientRead]`
3.  **Register Doctor**
    *   `POST /api/doctors/register`
    *   Input: JSON Body (`DoctorCreate`: name, email, designation, etc.)
    *   Output: JSON (`DoctorRead`: includes doctor `id`)
4.  **List Doctors**
    *   `GET /api/doctors/`
    *   Input: None
    *   Output: List `[DoctorRead]`
5.  **Submit Doctor Availability**
    *   `POST /api/schedule/doctor-availability`
    *   Input (Form): `doctor_id` (str), `name`, `education`, `designation`, `location`, `start_time` (datetime), `end_time` (datetime), `doctor_email`
    *   Output: `{"message": ..., "slot_id": ...}`
6.  **Recommend Slots (Patient)**
    *   `POST /api/schedule/recommend-slot`
    *   Input (Form): `patient_query` (str), Optional: `patient_query_date` (str), `patient_query_time` (str), `patient_query_designation` (str)
    *   Output: `{"available_slots": ..., "recommendation": ...}`
7.  **Book Slot (Patient)**
    *   `POST /api/schedule/book-slot`
    *   Input (Form): `selected_slot_id` (UUID), `patient_name`, `patient_email`, `patient_id` (UUID)
    *   Output: `{"slot_id": ..., "confirmation": ...}`
8.  **Submit Consultation (Graph Trigger)**
    *   `POST /api/langgraph/text-transcription`
    *   Input (Form): `formatted_dialogue` (str), `doctor_id` (UUID), `patient_id` (UUID), Optional: `consultation_id` (str)
    *   Output: JSON (`TranscriptionAnalysisResponse`)
9.  **Review/Update Consultation**
    *   `POST /api/langgraph/review-transcription`
    *   Input (Form): `consultation_id` (str), `updated_dialogue` (str)
    *   Output: JSON (`ReviewResponse`)
10. **Generate SOAP/Prescription**
    *   `POST /api/langgraph/generate-soap-prescription`
    *   Input (Form): `consultation_id` (str)
    *   Output: JSON (`SOAPResponse`)
11. **Generate Follow-up**
    *   `POST /api/langgraph/generate-followup`
    *   Input (Form): `consultation_id` (str)
    *   Output: JSON (`FollowupResponse`)
12. **Generate Education Summary**
    *   `POST /api/langgraph/generate-education-summary`
    *   Input (Form): `consultation_id` (str)
    *   Output: JSON (`EducationSummaryResponse`)
13. **Doctor Chatbot**
    *   `POST /api/chatbot`
    *   Input (Form): `doctor_id` (UUID), `message` (str)
    *   Output: JSON (`ChatbotResponse`)

📚 **Database Tables (Schema Overview)**

*   **`patients`**: id (PK, UUID), name, email (Unique), contact\_number, address, date\_of\_birth
*   **`doctors`**: id (PK, UUID), name, email (Unique), designation, education, location
*   **`transcriptions`**: consultation\_id (PK, String), formatted\_dialogue (Text), doctor\_id (FK->doctors.id, UUID), patient\_id (FK->patients.id, UUID)
*   **`doctor_slots`**: id (PK, UUID), doctor\_id (String - *Review: FK->doctors.id?*), name, education, designation, location, start\_time, end\_time, doctor\_email, is\_booked
*   **`appointments`**: id (PK, UUID), slot\_id (FK->doctor\_slots.id, UUID), patient\_id (FK->patients.id, UUID), patient\_name, patient\_email, doctor\_email, status
*   **`followup_slots`**: id (PK, UUID), consultation\_id (String, Nullable), doctor\_id (FK->doctors.id, UUID), patient\_id (FK->patients.id, UUID), suggested\_reason, condition\_detected, suggested\_time, visit\_type (Enum), confirmed, created\_at
*   **`soap_prescriptions`**: id (PK, String - *Review: UUID?*), consultation\_id (String), report (Text)
*   **`education_summaries`**: *(Assumed Structure)* id (PK, UUID), consultation\_id (FK, String), summary\_content (Text), created\_at


✅ **Setup**

1.  **Clone Repository:**
    ```bash
    git clone https://github.com/Liberate-Labs/AI-intern-multiagent-projects.git
    cd AI-Enhanced Clinical Consultation and Documentation System
    ```
2.  **Environment Variables:** Create a `.env` file in the root directory:
    ```env
    DATABASE_URL=postgresql://user:password@host:port/database
    OPENAI_API_KEY=sk-...
    TAVILY_API_KEY=tvly-...
    EMAIL_USER=your_email@gmail.com
    EMAIL_PASS=your_gmail_app_password # IMPORTANT: Use App Password for Gmail if 2FA is enabled
    GOOGLE_SERVICE_ACCOUNT_FILE=/path/to/your/service_account_key.json # Absolute or relative path
    GOOGLE_CALENDAR_ID=your_secondary_calendar_id@group.calendar.google.com # ID of the shared secondary calendar
    ```
3.  **Install Dependencies:**
    ```bash
    python -m venv venv # Create venv
    venv\Scripts\activate.bat # Activate venv
    # source venv/bin/activate # For MacOS
    pip install --upgrade pip
    pip install -r requirements.txt
    # Ensure Google client libs are in requirements.txt or install:
    # pip install google-api-python-client google-auth-oauthlib
    ```
4.  **Google Cloud Setup:**
    *   Enable the "Google Calendar API" in your Google Cloud project.
    *   Create a Service Account and download its JSON key file.
    *   Create a *secondary* Google Calendar.
    *   Share the secondary calendar with your service account email, granting "Make changes to events" permission.
    *   Update `.env` with the key file path and the secondary calendar ID.
5.  **Database Setup:** Ensure PostgreSQL is running and the database exists. Run the application once (`uvicorn...`) to allow SQLAlchemy (`Base.metadata.create_all`) to create/update tables. Use a migration tool like Alembic for robust schema management in production or complex development.
6.  **Run Application:**
    ```bash
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    ```
7.  **Access:** Open `http://localhost:8000/docs` for the API documentation and testing interface.