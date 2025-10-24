# streamlit_frontend/pages/5_Consultation.py
import streamlit as st
from utils.api_client import (
    get_doctors as api_get_doctors,
    get_patients as api_get_patients,
    submit_consultation,
    update_consultation,
    generate_soap,
    generate_followup,
    generate_education,
    transcribe_audio
)
import uuid
import io
import time
import numpy as np
import sounddevice as sd
import soundfile as sf
import logging
import re # Import regex for markdown
# --- ReportLab Imports ---
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.units import inch
# --- End ReportLab Imports ---

@st.cache_data(ttl=300)
def get_cached_doctors(): return api_get_doctors()
@st.cache_data(ttl=300)
def get_cached_patients(): return api_get_patients()

SAMPLE_RATE = 16000
RECORDING_DURATION_SECONDS = 120
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO); logger.setLevel(logging.INFO)

def process_recorded_np_audio(audio_np, sample_rate=SAMPLE_RATE):
    if audio_np is None or audio_np.size == 0: logger.warning("process: No audio data."); st.warning("No audio captured."); return None
    try:
        logger.info(f"Processing audio. Shape: {audio_np.shape}, dtype: {audio_np.dtype}")
        if audio_np.dtype == np.float32: audio_np = (audio_np * 32767).astype(np.int16)
        elif audio_np.dtype != np.int16: logger.warning(f"Unexpected dtype {audio_np.dtype}, converting."); audio_np = audio_np.astype(np.int16)
        wav_buffer = io.BytesIO(); sf.write(wav_buffer, audio_np, sample_rate, format='WAV', subtype='PCM_16'); wav_buffer.seek(0); logger.info("Audio processed to WAV.")
        return wav_buffer.getvalue()
    except Exception as e: st.error(f"Error processing audio: {e}"); logger.error(f"ERROR processing audio: {e}", exc_info=True); return None

# --- PDF Generation Helper (Using ReportLab with Markdown) ---
def create_pdf_report(title: str, content: str) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=(8.5*inch, 11*inch),
                            leftMargin=0.75*inch, rightMargin=0.75*inch,
                            topMargin=0.75*inch, bottomMargin=0.75*inch)
    styles = getSampleStyleSheet()
    title_style = styles['h1']; title_style.alignment = TA_CENTER; title_style.spaceAfter = 0.3 * inch
    body_style = ParagraphStyle( name='ReportBody', parent=styles['Normal'], alignment=TA_JUSTIFY, spaceAfter=6, wordWrap='CJK', leading=14 )

    content = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', content)
    content = re.sub(r'__(.*?)__', r'<b>\1</b>', content)
    content = re.sub(r'\*(.*?)\*', r'<i>\1</i>', content)
    content = re.sub(r'_(.*?)_', r'<i>\1</i>', content)
    content = content.replace('\n', '<br/>')

    story = []
    story.append(Paragraph(title, title_style))
    story.append(Paragraph(content, body_style))

    try:
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes
    except Exception as e:
        logger.error(f"Error building PDF with ReportLab: {e}", exc_info=True)
        st.error(f"Failed to generate PDF: {e}")
        return None
# --- End PDF Helper ---

if 'current_consultation_id' not in st.session_state: st.session_state.current_consultation_id = None
if 'current_dialogue' not in st.session_state: st.session_state.current_dialogue = ""
if 'current_feedback' not in st.session_state: st.session_state.current_feedback = None
if 'soap_result' not in st.session_state: st.session_state.soap_result = None
if 'followup_result' not in st.session_state: st.session_state.followup_result = None
if 'education_result' not in st.session_state: st.session_state.education_result = None

st.set_page_config(layout="wide", page_title="Consultation Processing")
st.title("🩺 Consultation Processing & Analysis")
st.header("1. Input Consultation Dialogue")

input_method = st.radio(
    "Select Input Method:",
    ("Type/Paste Dialogue", "Upload Audio File", "Live Recording (Server-Side, Blocking)"),
    key="input_method_radio", horizontal=True
)

input_controls_area = st.container()
st.subheader("Current Dialogue / Transcript")
common_dialogue_key = "dialogue_edit_area"
edited_dialogue = st.text_area(
    "Edit the dialogue below before submitting for analysis:",
    value=st.session_state.get('current_dialogue', ''),
    height=300,
    key=common_dialogue_key
)
st.session_state.current_dialogue = edited_dialogue
st.caption("Use controls below to load from audio, or type/paste directly above.")

doctors_list = get_cached_doctors()
patients_list = get_cached_patients()
if doctors_list is None or patients_list is None: st.error("Could not load doctors or patients list."); st.stop()
if not doctors_list or not patients_list: st.warning("Please ensure doctor/patient registered."); st.stop()
doctor_options = {f"{doc['name']} ({doc['email']})": doc['id'] for doc in doctors_list}
patient_options = {f"{p['name']} ({p['email']})": p['id'] for p in patients_list}

with input_controls_area:
    if input_method == "Type/Paste Dialogue":
        st.caption("Type or paste dialogue directly into the text area above.")
    elif input_method == "Upload Audio File":
        lang_map_upload = {"English": "en", "Hindi": "hi", "Spanish": "es"}
        selected_lang_upload = st.selectbox("Audio Language (Upload)", options=lang_map_upload.keys(), key="lang_upload")
        selected_lang_code_upload = lang_map_upload[selected_lang_upload]
        uploaded_file = st.file_uploader("Choose audio file", type=["wav", "mp3", "m4a", "ogg", "flac", "aac", "webm"], key="audio_upload")
        if uploaded_file is not None:
            st.audio(uploaded_file, format=uploaded_file.type)
            if st.button("Transcribe Uploaded Audio", key="transcribe_upload_btn"):
                file_bytes = uploaded_file.getvalue()
                with st.spinner(f"Transcribing ({selected_lang_upload}) audio file..."):
                    result = transcribe_audio(file_bytes, uploaded_file.name, uploaded_file.type, language=selected_lang_code_upload)
                if result and "transcription" in result: st.session_state.current_dialogue = result["transcription"]; st.success("Transcript loaded above.")
                else: st.error("Transcription failed."); st.session_state.current_dialogue = ""
                st.rerun()
    elif input_method == "Live Recording (Server-Side, Blocking)":
        st.warning("⚠️ **Note:** Records from the *server's* microphone. App will freeze.")
        st.info(f"Click button below to start a {RECORDING_DURATION_SECONDS}-second recording.")
        try:
            devices = sd.query_devices(); input_devices = [d for d in devices if d['max_input_channels'] > 0]
            logger.info(f"Found {len(input_devices)} audio input devices.")
            if not input_devices: st.error("No audio input devices found on server."); st.stop()
        except Exception as e: st.error(f"Error querying audio devices: {e}."); logger.error(f"Query devices error: {e}", exc_info=True); st.stop()
        lang_map_live = {"English": "en", "Hindi": "hi", "Spanish": "es"}
        selected_lang_live = st.selectbox("Recording Language (Live)", options=lang_map_live.keys(), key="lang_live")
        selected_lang_code_live = lang_map_live[selected_lang_live]
        if st.button(f"Record {RECORDING_DURATION_SECONDS} sec ({selected_lang_live}) Audio & Transcribe", key="record_sd_blocking_btn"):
            try:
                with st.spinner(f"🔴 Recording for {RECORDING_DURATION_SECONDS}s..."):
                    logger.info(f"Starting {RECORDING_DURATION_SECONDS}s recording...")
                    myrecording = sd.rec(int(RECORDING_DURATION_SECONDS * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype='float32', blocking=True)
                    logger.info("Recording finished.")
                with st.spinner("Processing and transcribing..."):
                    audio_bytes = process_recorded_np_audio(myrecording, SAMPLE_RATE)
                    if audio_bytes:
                        logger.info("Sending for transcription...")
                        result = transcribe_audio(audio_bytes, "live_recording.wav", "audio/wav", language=selected_lang_code_live)
                        if result and "transcription" in result: st.session_state.current_dialogue = result["transcription"]; st.success("Transcript loaded above.")
                        else: st.error("Transcription failed."); st.session_state.current_dialogue = ""
                    st.rerun()
            except sd.PortAudioError as pae: logger.error(f"PortAudioError: {pae}", exc_info=True); st.error(f"Audio Error: {pae}. Check mic.")
            except Exception as e: logger.error(f"Blocking recording error: {e}", exc_info=True); st.error(f"Error: {e}")

st.divider()
st.header("2. Select Participants & Submit Dialogue for Analysis")
st.caption("Select the Doctor and Patient involved in the dialogue currently shown in the text area above.")
with st.form("consultation_submission_form_final"):
    col_doc, col_pat = st.columns(2);
    with col_doc: selected_doctor_display = st.selectbox("Select Doctor*", options=list(doctor_options.keys()), index=None, placeholder="Choose doctor...", key="submit_doc_select_final")
    with col_pat: selected_patient_display = st.selectbox("Select Patient*", options=list(patient_options.keys()), index=None, placeholder="Choose patient...", key="submit_pat_select_final")
    final_dialogue_to_submit = st.session_state.get(common_dialogue_key, '')
    submitted_consultation = st.form_submit_button("Start/Submit Consultation & Analyze")
    if submitted_consultation:
        if not selected_doctor_display or not selected_patient_display or not final_dialogue_to_submit: st.error("Please select doctor, patient, and ensure dialogue is present.")
        else:
            doctor_id = doctor_options[selected_doctor_display]; patient_id = patient_options[selected_patient_display]
            with st.spinner("Submitting consultation..."): result = submit_consultation(final_dialogue_to_submit, str(doctor_id), str(patient_id))
            if result and result.get("consultation_id"):
                st.session_state.current_consultation_id = result.get("consultation_id"); st.session_state.initial_feedback = result.get("analysis_feedback")
                st.session_state.current_dialogue = result.get("formatted_dialogue", final_dialogue_to_submit); st.session_state.soap_result = None; st.session_state.followup_result = None; st.session_state.education_result = None
                st.success(f"Consultation submitted! Current ID: {st.session_state.current_consultation_id}"); st.rerun()
            else: st.error("Failed to submit consultation."); st.session_state.current_consultation_id = None

st.divider()
if st.session_state.current_consultation_id:
    st.header(f"3. Process Consultation ID: `{st.session_state.current_consultation_id}`")
    with st.expander("Append More Dialogue (Optional)", expanded=False):
        st.caption("Add follow-up conversation parts here.")
        if st.session_state.current_dialogue: st.markdown("**Current Dialogue Snippet:**"); st.text(st.session_state.current_dialogue[:300]+"...")
        with st.form("append_dialogue_form"):
            additional_dialogue = st.text_area("Enter text to append:", height=150, key="append_dialogue_text")
            submitted_append = st.form_submit_button("Append to Dialogue")
            if submitted_append:
                if not additional_dialogue: st.warning("Please enter text.")
                else:
                    with st.spinner("Updating dialogue..."): update_result = update_consultation(st.session_state.current_consultation_id, additional_dialogue)
                    if update_result:
                        st.session_state.current_dialogue = update_result.get("formatted_dialogue"); st.session_state.soap_result = None; st.session_state.followup_result = None; st.session_state.education_result = None
                        st.success("Dialogue updated!"); st.rerun()
                    else: st.error("Failed to update dialogue.")
    st.subheader("Generate Reports for Current Consultation")
    st.caption(f"Actions use latest dialogue for ID: `{st.session_state.current_consultation_id}`")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Generate SOAP / Prescription", key="gen_soap_current"):
             with st.spinner("Generating SOAP..."): st.session_state.soap_result = generate_soap(st.session_state.current_consultation_id)
             if st.session_state.soap_result and st.session_state.soap_result.get("soap_and_prescription"): st.toast("SOAP/Rx generated!")
             else: st.toast("Failed.")
             st.rerun()
    with col2:
        if st.button("Suggest Follow-up", key="gen_followup_current"):
             with st.spinner("Generating follow-up..."): st.session_state.followup_result = generate_followup(st.session_state.current_consultation_id)
             if st.session_state.followup_result and st.session_state.followup_result.get("followup_id"): st.toast("Follow-up suggested!")
             elif st.session_state.followup_result: st.toast("Follow-up processed.")
             else: st.toast("Failed.")
             st.rerun()
    with col3:
        if st.button("Generate Education Summary", key="gen_education_current"):
             with st.spinner("Generating education summary..."): st.session_state.education_result = generate_education(st.session_state.current_consultation_id)
             if st.session_state.education_result and st.session_state.education_result.get("education_summary"): st.toast("Education summary generated!")
             else: st.toast("Failed.")
             st.rerun()
    st.divider()
    st.subheader("View Generated Reports")
    report_area = st.container()
    with report_area:
         displayed_something = False
         if st.session_state.soap_result:
             displayed_something = True
             with st.expander("SOAP Note & Prescription Draft", expanded=True):
                 soap_content = st.session_state.soap_result.get("soap_and_prescription"); report_id = st.session_state.soap_result.get("report_id", "unknown")
                 if st.session_state.soap_result.get("error"): st.error(f"SOAP/Rx Error: {st.session_state.soap_result['error']}")
                 if soap_content:
                      st.markdown(soap_content)
                      try:
                           pdf_bytes = create_pdf_report("SOAP Note & Prescription", soap_content)
                           if pdf_bytes:
                                st.download_button(label="Download SOAP PDF", data=pdf_bytes, file_name=f"SOAP_Note_{st.session_state.current_consultation_id}_{report_id}.pdf", mime="application/pdf", key="download_soap_pdf")
                      except Exception as pdf_e: st.error(f"Failed to generate/prepare SOAP PDF: {pdf_e}")
                 else: st.warning("SOAP/Rx generation did not return content.")
         if st.session_state.followup_result:
             displayed_something = True
             with st.expander("Follow-up Suggestion", expanded=True):
                 if st.session_state.followup_result.get("error"): st.error(f"Follow-up Error: {st.session_state.followup_result['error']}")
                 elif st.session_state.followup_result.get("followup_id"):
                     st.markdown(f"**Follow-up ID:** `{st.session_state.followup_result.get('followup_id')}`"); st.markdown(f"**Suggested Time:** {st.session_state.followup_result.get('suggested_time', 'N/A')}")
                     st.markdown(f"**Visit Type:** {st.session_state.followup_result.get('visit_type', 'N/A')}"); st.markdown(f"**Reason:** {st.session_state.followup_result.get('reason', 'N/A')}")
                 else: st.info("Follow-up processed. No specific slot generated or details missing.")
         if st.session_state.education_result:
             displayed_something = True
             with st.expander("Patient Education Summary", expanded=True):
                 edu_content = st.session_state.education_result.get("education_summary")
                 if st.session_state.education_result.get("error"): st.error(f"Education Summary Error: {st.session_state.education_result['error']}")
                 if edu_content:
                     st.markdown(edu_content)
                     try:
                          pdf_bytes = create_pdf_report("Patient Education Summary", edu_content)
                          if pdf_bytes:
                                st.download_button(label="Download Education PDF", data=pdf_bytes, file_name=f"Education_Summary_{st.session_state.current_consultation_id}.pdf", mime="application/pdf", key="download_edu_pdf")
                     except Exception as pdf_e: st.error(f"Failed to generate/prepare Education PDF: {pdf_e}")
                 else: st.warning("Education Summary generation did not return content.")
         if not displayed_something:
             st.caption("No reports generated yet for the current consultation session.")
else:
    st.info("Use the options above to input dialogue and start a consultation session.")