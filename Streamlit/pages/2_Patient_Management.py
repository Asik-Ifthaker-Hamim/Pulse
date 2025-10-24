import streamlit as st
from utils.api_client import get_patients, register_patient
import time

st.set_page_config(layout="wide", page_title="Patient Management")
st.title("👤 Patient Management")

st.header("Registered Patients")
col_refresh, col_info = st.columns([1, 5])
with col_refresh:
    if st.button("🔄 Refresh List"):
        st.rerun()
with col_info:
    st.info("Showing currently registered patients.")

patients_data = get_patients()
if patients_data is not None:
    if not patients_data:
        st.info("No patients registered yet.")
    else:
        num_columns = 3
        cols = st.columns(num_columns)
        for i, patient in enumerate(patients_data):
            col_index = i % num_columns
            with cols[col_index]:
                with st.container(border=True):
                    st.subheader(f"{patient.get('name', 'N/A')}")
                    st.text(f"📧 Email: {patient.get('email', 'N/A')}")
                    st.text(f"📞 Contact: {patient.get('contact_number', 'N/A')}")
                    with st.expander("More Details"):
                        st.text(f"🎂 DOB: {patient.get('date_of_birth', 'N/A')}")
                        st.text(f"🏠 Address: {patient.get('address', 'N/A')}")
                        st.caption(f"🆔 ID: {patient.get('id', 'N/A')}")
                st.markdown("<br>", unsafe_allow_html=True)
else:
    st.warning("Could not retrieve patient data.")

st.markdown("---")
st.header("Register New Patient")
with st.form("register_patient_form", border=False):
    st.write("Fill in the details below:")
    col1, col2 = st.columns(2)
    with col1:
        p_name = st.text_input("Full Name*", key="p_name", placeholder="e.g., John Smith")
        p_contact = st.text_input("Contact Number*", key="p_contact", placeholder="e.g., +1-555-123-4567")
        p_dob = st.text_input("Date of Birth (Optional)", key="p_dob", placeholder="e.g., YYYY-MM-DD")
    with col2:
        p_email = st.text_input("Email*", key="p_email", placeholder="e.g., john.smith@email.com")
        p_address = st.text_area("Address (Optional)", key="p_address", placeholder="e.g., 123 Main St, Anytown, USA")
    submitted = st.form_submit_button("Register Patient Profile")
    if submitted:
        if not p_name or not p_email or not p_contact:
            st.error("Please fill in required fields marked with *.")
        else:
            patient_data = {
                "name": p_name, "email": p_email, "contact_number": p_contact,
                "address": p_address if p_address else None,
                "date_of_birth": p_dob if p_dob else None
            }
            response = register_patient(patient_data)
            if response:
                st.success(f"✅ Patient '{response.get('name')}' registered successfully!")
                with st.expander("See Registration Details"): st.json(response)
            else:
                st.error("❌ Patient registration failed.")