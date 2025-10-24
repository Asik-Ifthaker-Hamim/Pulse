import requests
import streamlit as st
from config import FASTAPI_BASE_URL
from datetime import datetime
from typing import List, Dict, Optional, Any

API_URL = f"{FASTAPI_BASE_URL}/api"

def get_doctors():
    url = f"{API_URL}/doctors/"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error(f"Connection Error: Could not connect to the backend at {url}. Is the FastAPI server running?")
        return None
    except requests.exceptions.Timeout:
        st.error(f"Timeout Error: The request to {url} timed out.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching doctors: {e}")
        if e.response is not None:
            try:
                error_detail = e.response.json().get("detail", "No detail provided.")
                st.error(f"Backend error detail: {error_detail}")
            except: pass
        return None

def register_doctor(doctor_data: dict):
    url = f"{API_URL}/doctors/register"
    try:
        response = requests.post(url, json=doctor_data, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error(f"Connection Error: Could not connect to the backend at {url}. Is the FastAPI server running?")
        return None
    except requests.exceptions.Timeout:
        st.error(f"Timeout Error: The request to {url} timed out.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error registering doctor: {e}")
        if e.response is not None:
            try:
                error_detail = e.response.json().get("detail", "No detail provided by backend.")
                st.error(f"Backend error detail: {error_detail}")
            except requests.exceptions.JSONDecodeError:
                st.error(f"Backend returned non-JSON error (Status {e.response.status_code}): {e.response.text[:500]}")
            except Exception as json_e:
                st.error(f"Could not parse error details from backend response: {json_e}")
        return None

def get_patients():
    url = f"{API_URL}/patients/"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error(f"Connection Error: Could not connect to the backend at {url}. Is the FastAPI server running?")
        return None
    except requests.exceptions.Timeout:
        st.error(f"Timeout Error: The request to {url} timed out.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching patients: {e}")
        if e.response is not None:
            try:
                error_detail = e.response.json().get("detail", "No detail provided.")
                st.error(f"Backend error detail: {error_detail}")
            except: pass
        return None

def register_patient(patient_data: dict):
    url = f"{API_URL}/patients/register"
    try:
        response = requests.post(url, json=patient_data, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error(f"Connection Error: Could not connect to the backend at {url}. Is the FastAPI server running?")
        return None
    except requests.exceptions.Timeout:
        st.error(f"Timeout Error: The request to {url} timed out.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error registering patient: {e}")
        if e.response is not None:
            try:
                error_detail = e.response.json().get("detail", "No detail provided by backend.")
                st.error(f"Backend error detail: {error_detail}")
            except requests.exceptions.JSONDecodeError:
                st.error(f"Backend returned non-JSON error (Status {e.response.status_code}): {e.response.text[:500]}")
            except Exception as json_e:
                st.error(f"Could not parse error details from backend response: {json_e}")
        return None

def add_doctor_availability(slot_data: dict):
    url = f"{API_URL}/schedule/doctor-availability"
    try:
        required_data = {
            "doctor_id": slot_data.get("doctor_id"),
            "start_time": slot_data.get("start_time"),
            "end_time": slot_data.get("end_time"),
            "location": slot_data.get("location")
        }
        if required_data["location"] is None:
            del required_data["location"]
        response = requests.post(url, data=required_data, timeout=20)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error(f"Connection Error: Could not connect to the backend at {url}. Is the FastAPI server running?")
        return None
    except requests.exceptions.Timeout:
        st.error(f"Timeout Error: The request to {url} timed out.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error adding availability slot: {e}")
        if e.response is not None:
            try:
                error_detail = e.response.json().get("detail", "No detail provided by backend.")
                if isinstance(error_detail, list):
                     formatted_errors = "\n".join([f"- {err.get('loc', ['unknown'])[-1]}: {err.get('msg', 'Unknown error')}" for err in error_detail])
                     st.error(f"Backend validation errors:\n{formatted_errors}")
                else:
                     st.error(f"Backend error detail: {error_detail}")
            except requests.exceptions.JSONDecodeError:
                st.error(f"Backend returned non-JSON error (Status {e.response.status_code}): {e.response.text[:500]}")
            except Exception as json_e:
                st.error(f"Could not parse error details from backend response: {json_e}")
        return None

def recommend_slot(query_data: dict):
    url = f"{API_URL}/schedule/recommend-slot"
    try:
        response = requests.post(url, data=query_data, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error(f"Connection Error: Could not connect to the backend at {url}. Is the FastAPI server running?")
        return None
    except requests.exceptions.Timeout:
        st.error(f"Timeout Error: The request to {url} timed out.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error getting slot recommendations: {e}")
        if e.response is not None:
            try:
                error_detail = e.response.json().get("detail", "No detail provided by backend.")
                st.error(f"Backend error detail: {error_detail}")
            except requests.exceptions.JSONDecodeError:
                st.error(f"Backend returned non-JSON error (Status {e.response.status_code}): {e.response.text[:500]}")
            except Exception as json_e:
                st.error(f"Could not parse error details from backend response: {json_e}")
        return None

def book_slot(booking_data: dict):
    url = f"{API_URL}/schedule/book-slot"
    try:
        response = requests.post(url, data=booking_data, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error(f"Connection Error: Could not connect to the backend at {url}. Is the FastAPI server running?")
        return None
    except requests.exceptions.Timeout:
        st.error(f"Timeout Error: The request to {url} timed out.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error booking slot: {e}")
        if e.response is not None:
            try:
                error_detail = e.response.json().get("detail", "No detail provided by backend.")
                st.error(f"Backend error detail: {error_detail}")
            except requests.exceptions.JSONDecodeError:
                st.error(f"Backend returned non-JSON error (Status {e.response.status_code}): {e.response.text[:500]}")
            except Exception as json_e:
                st.error(f"Could not parse error details from backend response: {json_e}")
        return None

def get_doctor_slots(doctor_id: str, include_booked: bool = True):
    url = f"{API_URL}/schedule/doctor/{doctor_id}/slots"
    params = {"show_booked": include_booked}
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error(f"Connection Error: Could not connect to the backend at {url}. Is the FastAPI server running?")
        return None
    except requests.exceptions.Timeout:
        st.error(f"Timeout Error: The request to {url} timed out.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching doctor slots: {e}")
        if e.response is not None:
            try:
                error_detail = e.response.json().get("detail", "No detail provided by backend.")
                st.error(f"Backend error detail: {error_detail}")
            except requests.exceptions.JSONDecodeError:
                 st.error(f"Backend returned non-JSON error (Status {e.response.status_code}): {e.response.text[:500]}")
            except Exception as json_e:
                st.error(f"Could not parse error details from backend response: {json_e}")
        return None

def submit_consultation(dialogue: str, doctor_id: str, patient_id: str):
    url = f"{API_URL}/consultation/text-transcription"
    payload = {
        "formatted_dialogue": dialogue,
        "doctor_id": doctor_id,
        "patient_id": patient_id
    }
    try:
        response = requests.post(url, data=payload, timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error(f"Connection Error: Could not connect to the backend at {url}.")
        return None
    except requests.exceptions.Timeout:
        st.error(f"Timeout Error: The request to {url} timed out.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error submitting consultation: {e}")
        if e.response is not None:
            try:
                error_detail = e.response.json().get("detail", "No detail provided by backend.")
                st.error(f"Backend error detail: {error_detail}")
            except: pass
        return None

def update_consultation(consultation_id: str, updated_dialogue: str):
    url = f"{API_URL}/consultation/review-transcription"
    payload = {
        "consultation_id": consultation_id,
        "updated_dialogue": updated_dialogue
    }
    try:
        response = requests.post(url, data=payload, timeout=20)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error(f"Connection Error: Could not connect to the backend at {url}.")
        return None
    except requests.exceptions.Timeout:
        st.error(f"Timeout Error: The request to {url} timed out.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error updating dialogue: {e}")
        if e.response is not None:
            try:
                error_detail = e.response.json().get("detail", "No detail provided by backend.")
                st.error(f"Backend error detail: {error_detail}")
            except: pass
        return None

def generate_soap(consultation_id: str):
    url = f"{API_URL}/consultation/generate-soap-prescription"
    payload = {"consultation_id": consultation_id}
    try:
        response = requests.post(url, data=payload, timeout=45)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error(f"Connection Error: Could not connect to the backend at {url}.")
        return None
    except requests.exceptions.Timeout:
        st.error(f"Timeout Error: The request to {url} timed out.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error generating SOAP/Rx: {e}")
        if e.response is not None:
            try:
                error_detail = e.response.json().get("detail", "No detail provided by backend.")
                st.error(f"Backend error detail: {error_detail}")
            except: pass
        return None

def generate_followup(consultation_id: str):
    url = f"{API_URL}/consultation/generate-followup"
    payload = {"consultation_id": consultation_id}
    try:
        response = requests.post(url, data=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error(f"Connection Error: Could not connect to the backend at {url}.")
        return None
    except requests.exceptions.Timeout:
        st.error(f"Timeout Error: The request to {url} timed out.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error generating Follow-up: {e}")
        if e.response is not None:
            try:
                error_detail = e.response.json().get("detail", "No detail provided by backend.")
                st.error(f"Backend error detail: {error_detail}")
            except: pass
        return None

def generate_education(consultation_id: str):
    url = f"{API_URL}/education/generate-education-summary"
    payload = {"consultation_id": consultation_id}
    try:
        response = requests.post(url, data=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error(f"Connection Error: Could not connect to the backend at {url}.")
        return None
    except requests.exceptions.Timeout:
        st.error(f"Timeout Error: The request to {url} timed out.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error generating Education Summary: {e}")
        if e.response is not None:
            try:
                error_detail = e.response.json().get("detail", "No detail provided by backend.")
                st.error(f"Backend error detail: {error_detail}")
            except: pass
        return None

def ask_chatbot(doctor_id: str, message: str, chat_history: Optional[List[Dict[str, str]]] = None):
    url = f"{API_URL}/chatbot"
    payload = {
        "doctor_id": doctor_id,
        "message": message,
        "chat_history": chat_history if chat_history else []
    }
    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error(f"Connection Error: Could not connect to the chatbot backend at {url}.")
        return {"response_type": "error", "error_message": "Connection Error"}
    except requests.exceptions.Timeout:
        st.error(f"Timeout Error: The request to {url} timed out.")
        return {"response_type": "error", "error_message": "Request Timed Out"}
    except requests.exceptions.RequestException as e:
        st.error(f"Error interacting with chatbot: {e}")
        error_detail = "Chatbot backend error."
        if e.response is not None:
            try:
                error_detail = e.response.json().get("detail", error_detail)
            except: pass
        st.error(f"Backend error detail: {error_detail}")
        return {"response_type": "error", "error_message": f"Chatbot Error: {error_detail}"}

def transcribe_audio(audio_file_bytes: bytes, filename: str, content_type: str, language: str = 'en'):
    url = f"{API_URL}/consultation/transcribe-audio"
    files = {'audio_file': (filename, audio_file_bytes, content_type)}
    data = {'language': language}
    try:
        response = requests.post(url, files=files, data=data, timeout=90)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error(f"Connection Error: Could not connect to the transcription backend at {url}.")
        return None
    except requests.exceptions.Timeout:
        st.error(f"Timeout Error: The transcription request to {url} timed out.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error during transcription request: {e}")
        if e.response is not None:
            try:
                error_detail = e.response.json().get("detail", "No detail provided by backend.")
                st.error(f"Backend transcription error detail: {error_detail}")
            except: pass
        return None