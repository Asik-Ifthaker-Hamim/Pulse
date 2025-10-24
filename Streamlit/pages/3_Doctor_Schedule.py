import streamlit as st
from datetime import datetime, time, timedelta
from utils.api_client import get_doctors, add_doctor_availability, get_doctor_slots
import pandas as pd
import time as pytime

st.set_page_config(layout="wide", page_title="Doctor Schedule")
st.title("🗓️ Doctor Schedule Management")

st.header("Add New Availability Slot")
doctors_list = get_doctors()
if doctors_list is None: st.error("Cannot load doctor list."); st.stop()
if not doctors_list: st.warning("No doctors registered."); st.stop()
doctor_options_add = {f"{doc['name']} (ID: {doc['id']})": doc['id'] for doc in doctors_list}
with st.form("add_slot_form", border=True):
    selected_doctor_display_name_add = st.selectbox("Select Doctor*", options=list(doctor_options_add.keys()), index=None, placeholder="Choose doctor...", key="slot_doctor_select_add")
    col_date, col_start, col_end, col_loc = st.columns(4)
    with col_date: slot_date = st.date_input("Date*", key="slot_date")
    with col_start: start_time_input = st.time_input("Start Time*", step=timedelta(minutes=30), key="slot_start_time")
    with col_end: end_time_input = st.time_input("End Time*", step=timedelta(minutes=30), key="slot_end_time")
    with col_loc: slot_location = st.text_input("Slot Location (Optional)", key="slot_loc", placeholder="Defaults to Profile")
    submitted_add = st.form_submit_button("Add Availability Slot")
    if submitted_add:
        if not selected_doctor_display_name_add: st.error("Select a doctor.")
        elif not slot_date or not start_time_input or not end_time_input: st.error("Select Date/Time.")
        elif start_time_input >= end_time_input: st.error("Start time must be before end.")
        else:
            selected_doctor_id_add = doctor_options_add[selected_doctor_display_name_add]
            start_datetime = datetime.combine(slot_date, start_time_input)
            end_datetime = datetime.combine(slot_date, end_time_input)
            slot_data = {
                "doctor_id": str(selected_doctor_id_add),
                "start_time": start_datetime.isoformat(),
                "end_time": end_datetime.isoformat(),
                "location": slot_location if slot_location else None
            }
            response_add = add_doctor_availability(slot_data)
            if response_add:
                doc_name_add = selected_doctor_display_name_add.split(" (ID:")[0]
                st.success(f"✅ Slot added for Dr. {doc_name_add}! ID: {response_add.get('slot_id')}")
            else: st.error("❌ Failed to add slot.")

st.markdown("---")
st.header("View Existing Slots")

if not doctors_list: st.warning("Cannot proceed without doctor list."); st.stop()
doctor_options_view = {f"{doc['name']} (ID: {doc['id']})": doc['id'] for doc in doctors_list}
selected_doctor_display_name_view = st.selectbox("Select Doctor to View Schedule", options=list(doctor_options_view.keys()), index=None, placeholder="Choose a doctor...", key="view_doctor_select")
include_booked = st.checkbox("Include Booked Slots?", value=True, key="view_include_booked")
if 'loaded_doctor_id' not in st.session_state: st.session_state.loaded_doctor_id = None
if 'loaded_slots' not in st.session_state: st.session_state.loaded_slots = None

if selected_doctor_display_name_view:
    selected_doctor_id_view = doctor_options_view[selected_doctor_display_name_view]
    if st.button("Load Schedule", key="load_schedule_button"):
        with st.spinner(f"Loading schedule for {selected_doctor_display_name_view}..."):
            st.session_state.loaded_slots = get_doctor_slots(selected_doctor_id_view, include_booked)
            st.session_state.loaded_doctor_id = selected_doctor_id_view

if st.session_state.loaded_doctor_id and selected_doctor_display_name_view and \
   st.session_state.loaded_doctor_id == doctor_options_view[selected_doctor_display_name_view]:
    slots = st.session_state.loaded_slots
    if slots is not None:
        if not slots:
            st.info("No slots found for this doctor matching the criteria.")
        else:
            st.success(f"Displaying {len(slots)} slots:")
            num_columns = 3
            cols = st.columns(num_columns)
            for i, slot in enumerate(slots):
                col_index = i % num_columns
                with cols[col_index]:
                    container_opts = {"border": True}
                    header_color = "green" if not slot['is_booked'] else "orange"
                    with st.container(**container_opts):
                         if slot['is_booked']: st.markdown(f"<span style='color: {header_color}; font-weight: bold;'>(Booked)</span>", unsafe_allow_html=True)
                         else: st.markdown(f"<span style='color: {header_color}; font-weight: bold;'>(Available)</span>", unsafe_allow_html=True)
                         try:
                             start_dt_view = datetime.fromisoformat(slot['start_time']); end_dt_view = datetime.fromisoformat(slot['end_time'])
                             st.markdown(f"**🗓️ Date:** {start_dt_view.strftime('%Y-%m-%d')}")
                             st.markdown(f"**⏰ Time:** {start_dt_view.strftime('%I:%M %p')} - {end_dt_view.strftime('%I:%M %p')}")
                         except Exception: st.markdown(f"**Time:** {slot.get('start_time')} - {slot.get('end_time')}")
                         st.markdown(f"**📍 Location:** {slot.get('location', 'N/A')}")
                         st.caption(f"Slot ID: {slot.get('id', 'N/A')}")
                    st.markdown("<br>", unsafe_allow_html=True)
    elif st.session_state.loaded_doctor_id:
        st.error("Failed to retrieve schedule from the backend.")