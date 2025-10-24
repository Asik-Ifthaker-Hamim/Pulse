import smtplib
from email.message import EmailMessage
from app.core.config import settings
from datetime import datetime, timedelta
from pydantic import UUID4
import logging
import os
import time
from typing import Optional

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

def get_google_credentials():
    scopes = ['https://www.googleapis.com/auth/calendar.events']
    key_file_path = settings.GOOGLE_SERVICE_ACCOUNT_FILE
    if not key_file_path or not os.path.exists(key_file_path):
         logger.error("Google Service Account Key file path not found or not configured.")
         return None
    try:
        return service_account.Credentials.from_service_account_file(
            key_file_path, scopes=scopes)
    except Exception as e:
        logger.error(f"Failed to load Google credentials from {key_file_path}: {e}", exc_info=True)
        return None

def generate_google_meet_link(
    appointment_time: datetime,
    duration_minutes: int,
    summary: str,
    description: str,
    attendee_emails: list[str]
    ) -> Optional[str]:
    credentials = get_google_credentials()
    calendar_id = settings.GOOGLE_CALENDAR_ID

    if not credentials or not calendar_id:
        logger.error("Google credentials or Calendar ID missing. Cannot create event.")
        return None

    meet_link: Optional[str] = None
    event_link: Optional[str] = None
    event_id: Optional[str] = None

    try:
        service = build('calendar', 'v3', credentials=credentials)
        end_time = appointment_time + timedelta(minutes=duration_minutes)
        start_iso = appointment_time.isoformat() + 'Z'
        end_iso = end_time.isoformat() + 'Z'

        event_body = {
            'summary': summary,
            'description': description,
            'start': {'dateTime': start_iso},
            'end': {'dateTime': end_iso},
            'conferenceData': {
                'createRequest': {
                    'requestId': f"{summary.replace(' ', '_')}-{appointment_time.timestamp()}"
                }
            },
            'reminders': {
                'useDefault': False,
                'overrides': [{'method': 'popup', 'minutes': 10}],
            },
        }

        logger.info(f"Creating Google Calendar event on calendar '{calendar_id}' (minimal body, relying on default)")
        created_event = service.events().insert(
            calendarId=calendar_id,
            body=event_body
        ).execute()

        event_id = created_event.get('id')
        event_link = created_event.get('htmlLink')
        meet_link = created_event.get('hangoutLink')

        logger.info(f"Initial event creation response received for event: {event_link}")

        if not meet_link and event_id:
            logger.warning(f"hangoutLink not found in initial insert response for event {event_id}. Waiting and re-fetching.")
            time.sleep(3)
            try:
                refetched_event = service.events().get(
                    calendarId=calendar_id,
                    eventId=event_id
                ).execute()
                meet_link = refetched_event.get('hangoutLink')
                if meet_link:
                    logger.info(f"Successfully retrieved hangoutLink after re-fetching: {meet_link}")
                else:
                    conf_data = refetched_event.get('conferenceData')
                    if conf_data:
                         logger.error(f"hangoutLink still not found after re-fetching event {event_id}, but conferenceData exists: {conf_data}")
                    else:
                         logger.error(f"hangoutLink AND conferenceData not found after re-fetching event {event_id}. Calendar default might not be working as expected via API.")
            except HttpError as get_error:
                 logger.error(f'API error during event re-fetch: {get_error}', exc_info=True)
                 logger.error(f"Error details: {get_error.content}")
            except Exception as get_e:
                 logger.error(f'Unexpected error during event re-fetch: {get_e}', exc_info=True)
        elif meet_link:
             logger.info(f"Google Meet link found in initial response: {meet_link}")
        elif not event_id:
             logger.error("Event created but no event ID returned in response.")

        if meet_link:
            return meet_link
        elif event_link:
            logger.warning(f"Returning event link ({event_link}) as fallback since Meet link was not retrieved.")
            return event_link
        else:
            return None

    except HttpError as error:
        logger.error(f'An API error occurred during insert: {error}', exc_info=True)
        logger.error(f"Error details: {error.content}")
        return None
    except Exception as e:
         logger.error(f'An unexpected error occurred during Meet link generation: {e}', exc_info=True)
         return None


# --- Updated send_appointment_email ---
def send_appointment_email(
    patient_email: str,
    doctor_email: str,
    patient_name: str,
    doctor_name: str,
    start_time: datetime,
    end_time: datetime,
    doctor_designation: str,
    doctor_education: str,
    doctor_location: str,
    patient_contact_number: str,
    doctor_id: str,
    patient_id: UUID4
):
    appointment_time_str = start_time.strftime('%A, %B %d, %Y at %I:%M %p') # Example: Tuesday, August 20, 2024 at 04:00 PM
    duration_minutes = (end_time - start_time).total_seconds() / 60
    email_subject = f"Appointment Confirmation: {patient_name} with Dr. {doctor_name}"
    email_body = f"""
Dear {patient_name} and Dr. {doctor_name},

This email confirms the following appointment scheduled through our system:

Appointment Details
---------------------
Date & Time: {appointment_time_str}
Duration: {duration_minutes:.0f} minutes
Location: {doctor_location}

Patient Information
--------------------
Name: {patient_name}
Patient ID: {str(patient_id)}
Contact: {patient_contact_number}
Email: {patient_email}

Doctor Information
-------------------
Name: Dr. {doctor_name}
Doctor ID: {doctor_id}
Designation: {doctor_designation}
Education: {doctor_education}
Email: {doctor_email}

Please be prepared for your session and ensure timely arrival. If rescheduling is necessary, please contact the clinic office at your earliest convenience.

We look forward to assisting you.

Sincerely,

The Clinic Administration
"""

    msg = EmailMessage()
    msg.set_content(email_body)
    msg["Subject"] = email_subject
    msg["From"] = settings.EMAIL_USER
    msg["To"] = f"{patient_email}, {doctor_email}"
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.starttls()
            smtp.login(settings.EMAIL_USER, settings.EMAIL_PASS)
            smtp.send_message(msg)
        logger.info(f"Booked appointment confirmation email sent to {patient_email} and {doctor_email}")
    except Exception as e:
        logger.error(f"Booked appointment email send failed: {e}", exc_info=True)
        raise e

# --- Updated send_followup_confirmation_email ---
def send_followup_confirmation_email(
    patient_email: str,
    doctor_email: str,
    patient_name: str,
    doctor_name: str,
    followup_time: datetime,
    visit_type: str,
    reason: str,
    doctor_designation: str,
    doctor_education: str,
    doctor_location: str,
    patient_contact_number: str,
    doctor_id: UUID4,
    patient_id: UUID4
):
    followup_time_str = followup_time.strftime('%A, %B %d, %Y around %I:%M %p')
    visit_type_formatted = visit_type.replace('_', ' ').title()
    email_subject = f"Follow-up Appointment Confirmed: {patient_name} with Dr. {doctor_name}"

    connection_details_line = ""
    if visit_type.lower() == 'in_person':
        connection_details_line = f"Location: {doctor_location or 'Clinic Address (Please Confirm)'}"
    elif visit_type.lower() == 'telehealth':
        meet_summary = f"Follow-up: {patient_name} with Dr. {doctor_name}"
        meet_description = f"Reason: {reason}\nPatient ID: {patient_id}\nDoctor ID: {doctor_id}"
        attendees_for_context = [patient_email, doctor_email]
        duration = 30

        retrieved_link = generate_google_meet_link(
            appointment_time=followup_time,
            duration_minutes=duration,
            summary=meet_summary,
            description=meet_description,
            attendee_emails=attendees_for_context
        )

        if retrieved_link:
            if "meet.google.com" in retrieved_link:
                 connection_details_line = f"Meeting Link: {retrieved_link}\n(Please use this link to join the session at the scheduled time)"
            elif "google.com/calendar/event" in retrieved_link:
                 connection_details_line = f"Calendar Event: {retrieved_link}\n(Please click this link and find the 'Join with Google Meet' button inside the event details)"
            else:
                 connection_details_line = "Meeting Link: A calendar event was created but the link format is unexpected. Please check your Google Calendar or contact the clinic."
        else:
             connection_details_line = "Meeting Link: There was an error generating the meeting link. Please contact the clinic for telehealth details."
    else:
        connection_details_line = "Mode: Please confirm connection details with the clinic."


    email_body = f"""
Dear {patient_name} and Dr. {doctor_name},

This email confirms the follow-up appointment scheduled based on your recent consultation.

Follow-up Details
----------------------
Approximate Date & Time: {followup_time_str}
Visit Type: {visit_type_formatted}
Reason for Follow-up: {reason}
{connection_details_line}

Patient Information
--------------------
Name: {patient_name}
Patient ID: {str(patient_id)}
Contact: {patient_contact_number}
Email: {patient_email}

Doctor Information
-------------------
Name: Dr. {doctor_name}
Doctor ID: {str(doctor_id)}
Designation: {doctor_designation}
Education: {doctor_education}
Email: {doctor_email}

Our scheduling team may contact you closer to the date to finalize the exact appointment time if required. Please contact the clinic if you have any questions regarding this follow-up.

Sincerely,

The Clinic Administration
"""
    msg = EmailMessage()
    msg.set_content(email_body)
    msg["Subject"] = email_subject
    msg["From"] = settings.EMAIL_USER
    msg["To"] = f"{patient_email}, {doctor_email}"
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.starttls()
            smtp.login(settings.EMAIL_USER, settings.EMAIL_PASS)
            smtp.send_message(msg)
        logger.info(f"Follow-up confirmation email sent to {patient_email} and {doctor_email}")
    except Exception as e:
        logger.error(f"Follow-up email send failed: {e}", exc_info=True)
        raise e