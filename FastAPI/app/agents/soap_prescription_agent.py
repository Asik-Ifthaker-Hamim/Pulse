from app.core.llm_client import llm
from langchain_core.messages import SystemMessage, HumanMessage
from app.core.config import settings
from app.schemas.agent_state import AgentState
from app.db.connection import get_db
from app.models.transcription_model import Transcription
from app.crud.crud_soap_prescription import save_soap_prescription
import requests
import re
from app.prompts.soap_prompts import SOAP_TEMPLATE as soap_template

def validate_with_openfda(med_name: str) -> str:
    try:
        url = f"https://api.fda.gov/drug/label.json?search=openfda.generic_name:{med_name.lower()}&limit=1"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        if response.json().get("results"):
            return f"✔️ {med_name} found in OpenFDA"
        else:
            return f"⚠️ {med_name} not found in OpenFDA (check spelling or if it's brand name)"
    except requests.exceptions.RequestException as req_err:
         print(f"Network error validating {med_name}: {req_err}")
         return f"❌ Network error during OpenFDA validation for {med_name}"
    except Exception as e:
        print(f"Error validating {med_name} with OpenFDA: {e}")
        return f"❌ Error validating {med_name} with OpenFDA"

class SOAPPrescriptionAgent:
    def run(self, state: AgentState) -> dict:
        if not llm:
            return {"error": "LLM client not available."}
        db = next(get_db())
        transcription = db.query(Transcription).filter(
            Transcription.consultation_id == state.consultation_id
        ).first()
        if not transcription:
            db.close()
            return {"error": "Consultation ID not found."}

        messages = [
            SystemMessage(content="You generate SOAP notes, prescription drafts, and a separate medication list based on consultations."),
            HumanMessage(content=soap_template.format(dialogue=transcription.formatted_dialogue))
        ]

        llm_output_raw = "Error: Could not generate SOAP/prescription."
        main_report_section = llm_output_raw
        medication_names = []

        try:
            response = llm.invoke(messages)
            llm_output_raw = response.content.strip()

            parts = re.split(r'\n---\nMEDICATION_LIST:', llm_output_raw, maxsplit=1, flags=re.IGNORECASE)
            main_report_section = parts[0].strip()

            if len(parts) > 1:
                med_list_str = parts[1].strip()
                medication_names = [name.strip() for name in med_list_str.split(',') if name.strip()]
            else:
                 print("Warning: MEDICATION_LIST marker not found in LLM output. Attempting regex fallback.")
                 med_matches = re.findall(r"Medication:\s*([^\n]+)", main_report_section, re.IGNORECASE)
                 if med_matches:
                      medication_names = [name.strip() for name in med_matches]

        except Exception as e:
            print(f"Error calling LLM or parsing response for SOAP/prescription: {e}")

        validation_results = []
        if medication_names:
            print(f"Found medications to validate: {medication_names}")
            for med_name in medication_names:
                validation_results.append(validate_with_openfda(med_name))
        else:
             print("No medications extracted from LLM response for validation.")
             validation_results.append("No medication names found in the draft to validate.")

        validation_report_str = "**OpenFDA Validation Checks**\n"
        validation_report_str += "\n".join([f"- {result}" for result in validation_results])

        full_report = f"{main_report_section}\n\n---\n{validation_report_str}"

        saved = None
        error_msg = None
        try:
            saved = save_soap_prescription(db, state.consultation_id, full_report)
        except Exception as db_error:
             print(f"Error saving SOAP prescription to DB: {db_error}")
             error_msg = "Generated report but failed to save to database."
        finally:
            db.close()

        return {
            "consultation_id": state.consultation_id,
            "report_id": saved.id if saved else None,
            "soap_and_prescription": full_report,
            "error": error_msg
        }