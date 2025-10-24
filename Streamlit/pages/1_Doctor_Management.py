import streamlit as st
import pandas as pd
from utils.api_client import get_doctors, register_doctor
import time

st.set_page_config(layout="wide", page_title="Doctor Management")
st.title("👨‍⚕️ Doctor Management")

st.header("Registered Doctors")
col_refresh, col_info = st.columns([1, 5])
with col_refresh:
    if st.button("🔄 Refresh List"):
        st.rerun()
with col_info:
    st.info("Showing currently registered doctors.")

doctors_data = get_doctors()
if doctors_data is not None:
    if not doctors_data:
        st.info("No doctors registered yet.")
    else:
        num_columns = 3
        cols = st.columns(num_columns)
        for i, doctor in enumerate(doctors_data):
            col_index = i % num_columns
            with cols[col_index]:
                with st.container(border=True):
                    st.subheader(f"🩺 Dr. {doctor.get('name', 'N/A')}")
                    st.text(f"Specialty: {doctor.get('designation', 'N/A')}")
                    st.caption(f"📧 Email: {doctor.get('email', 'N/A')}")
                    with st.expander("More Details"):
                        st.text(f"🎓 Education: {doctor.get('education', 'N/A')}")
                        st.text(f"📍 Location: {doctor.get('location', 'N/A')}")
                        st.caption(f"🆔 ID: {doctor.get('id', 'N/A')}")
                st.markdown("<br>", unsafe_allow_html=True)
else:
    st.warning("Could not retrieve doctor data.")

st.markdown("---")
st.header("Register New Doctor")
with st.form("register_doctor_form", border=False):
    st.write("Fill in the details below:")
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Full Name*", key="doc_name", placeholder="e.g., Dr. Jane Doe")
        designation = st.text_input("Designation / Specialty*", key="doc_designation", placeholder="e.g., Cardiologist")
        location = st.text_input("Location (Optional)", key="doc_location", placeholder="e.g., Main Clinic, City")
    with col2:
        email = st.text_input("Email*", key="doc_email", placeholder="e.g., jane.doe@clinic.com")
        education = st.text_input("Education*", key="doc_education", placeholder="e.g., MD, PhD")
    submitted = st.form_submit_button("Register Doctor Profile")
    if submitted:
        if not name or not email or not designation or not education:
            st.error("Please fill in all required fields marked with *.")
        else:
            doctor_data = {
                "name": name, "email": email, "designation": designation,
                "education": education, "location": location if location else None
            }
            response = register_doctor(doctor_data)
            if response:
                st.success(f"✅ Doctor '{response.get('name')}' registered successfully!")
                with st.expander("See Registration Details"): st.json(response)
            else:
                st.error("❌ Doctor registration failed.")