import streamlit as st
from utils.api_client import recommend_slot, book_slot, get_patients
from datetime import datetime, time, timedelta

st.set_page_config(layout="wide", page_title="Patient Schedule")
st.title("🗓️ Patient Appointment Scheduling")

tab_find, tab_book = st.tabs(["🔎 Find Available Slots", "✅ Book Appointment"])

with tab_find:
    st.header("Find Doctor Availability")
    st.markdown("Describe symptoms/reason, optionally filter by date/time/specialty.")
    with st.form("find_slot_form"):
        patient_query = st.text_area("Reason for Visit / Symptoms*", placeholder="e.g., 'Persistent cough and fever'")
        col_date, col_time, col_spec = st.columns(3)
        with col_date: query_date = st.date_input("Preferred Date (Optional)", value=None, key="q_date")
        with col_time: query_time = st.time_input("Preferred Start Time (Optional)", value=None, step=timedelta(minutes=30), key="q_time")
        with col_spec: query_designation = st.text_input("Preferred Specialty (Optional)", placeholder="e.g., Cardiologist", key="q_spec")
        submitted_find = st.form_submit_button("Search for Slots")
        if submitted_find:
            if not patient_query: st.error("Please describe the reason for your visit.")
            else:
                query_data = {
                    "patient_query": patient_query,
                    "patient_query_date": query_date.strftime('%Y-%m-%d') if query_date else None,
                    "patient_query_time": query_time.strftime('%H:%M:%S') if query_time else None,
                    "patient_query_designation": query_designation if query_designation else None,
                }
                query_data = {k: v for k, v in query_data.items() if v is not None}
                with st.spinner("Searching for available slots..."): recommendation_result = recommend_slot(query_data)
                if recommendation_result:
                    st.subheader("Search Results")
                    st.info("AI Recommendation:")
                    st.markdown(recommendation_result.get("recommendation", "No recommendation provided."))
                    available_slots = recommendation_result.get("available_slots")
                    if available_slots and isinstance(available_slots, list) and len(available_slots) > 0:
                        st.success(f"Found {len(available_slots)} matching slots:")
                        num_columns = 2
                        cols = st.columns(num_columns)
                        for i, slot in enumerate(available_slots):
                            col_index = i % num_columns
                            with cols[col_index]:
                                with st.container(border=True):
                                    st.markdown(f"**Dr. {slot.get('doctor_name', 'N/A')}** ({slot.get('designation', 'N/A')})")
                                    try:
                                        start_dt = datetime.fromisoformat(slot['start_time']); end_dt = datetime.fromisoformat(slot['end_time'])
                                        st.text(f"🗓️ {start_dt.strftime('%Y-%m-%d')}")
                                        st.text(f"⏰ {start_dt.strftime('%I:%M %p')} - {end_dt.strftime('%I:%M %p')}")
                                    except Exception: st.text(f"Time: {slot.get('start_time', 'N/A')} to {slot.get('end_time', 'N/A')}")
                                    st.text(f"📍 Location: {slot.get('location', 'N/A')}")
                                    slot_id = slot.get('id', 'N/A')
                                    st.code(f"{slot_id}", language=None)
                                    st.caption("Copy Slot ID for booking.")
                                st.markdown("<br>", unsafe_allow_html=True)
                    elif isinstance(available_slots, list) and len(available_slots) == 0: st.info("No available slots found matching criteria.")
                    else: st.warning("Could not retrieve available slots information.")
                else: st.error("Failed to get response from recommendation service.")

with tab_book:
    st.header("Book Your Selected Appointment")
    st.markdown("Select patient profile & paste Slot ID from search results.")
    patients_list = get_patients()
    if patients_list is None: st.error("Cannot load patient list."); st.stop()
    if not patients_list: st.warning("No patient profiles found."); st.stop()
    patient_options = {f"{p['name']} ({p['email']})": p for p in patients_list}
    with st.form("book_slot_form"):
        selected_patient_display = st.selectbox("Select Your Patient Profile*", options=list(patient_options.keys()), index=None, placeholder="Choose profile...", key="book_patient_select")
        selected_slot_id = st.text_input("Enter Slot ID to Book*", placeholder="Paste Slot ID", key="book_slot_id")
        submitted_book = st.form_submit_button("Confirm Booking")
        if submitted_book:
            if not selected_patient_display: st.error("Please select patient profile.")
            elif not selected_slot_id: st.error("Please enter Slot ID.")
            else:
                selected_patient_details = patient_options[selected_patient_display]
                booking_data = {
                    "selected_slot_id": selected_slot_id.strip(), "patient_name": selected_patient_details['name'],
                    "patient_email": selected_patient_details['email'], "patient_id": str(selected_patient_details['id'])
                }
                with st.spinner("Processing booking..."): booking_result = book_slot(booking_data)
                if booking_result:
                    st.subheader("Booking Confirmation")
                    confirmation_message = booking_result.get("confirmation", "Booking status unclear.")
                    if "✅" in confirmation_message or "booked successfully" in confirmation_message.lower(): st.success(confirmation_message)
                    else: st.warning(confirmation_message)
                else: st.error("Failed to submit booking request.")