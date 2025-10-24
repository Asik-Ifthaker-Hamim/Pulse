import streamlit as st

st.set_page_config(
    page_title="AI-Enhanced Clinical Consultation and Documentation System",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Header ---
st.image("https://static.vecteezy.com/system/resources/previews/036/602/533/original/ai-generated-healthcare-providers-filled-colorful-logo-well-established-company-design-element-ai-art-for-corporate-branding-blue-chip-stocks-vector.jpg", width=200)  # Optional: Add a relevant logo/image
st.title("AI-Enhanced Clinical Consultation and Documentation System")
st.subheader("Streamlining Consultation Workflows")

st.markdown("---") 


st.markdown(
    """
    Welcome to the AI-Enhanced Clinical Consultation and Documentation System! An AI-powered clinical assistant built using StreamlitLangGraph, FastAPI, LangChain, and 
    OpenAI that streamlines doctor-patient interactions — from transcription analysis to SOAP notes, 
    prescription validation, follow-up suggestions, chatbot assistance, patient education, and appointment booking.
    """
)

st.markdown("---") 

st.header("✨ Key Features")
st.markdown("Navigate using the sidebar on the left to access these modules:")

col1, col2, col3 = st.columns(3, gap="large")

with col1:
    st.subheader("👤 Patient Management")
    st.markdown("- View registered patients.")
    st.markdown("- Register new patient profiles.")
    st.markdown("*(Page: Patient Management)*")


    st.subheader("🗓️ Scheduling")
    st.markdown("- Doctors add availability.")
    st.markdown("- View doctor schedules.")
    st.markdown("- Patients find & book slots.")
    st.markdown("*(Pages: Doctor Schedule, Patient Schedule)*")

with col2:
    st.subheader("👨‍⚕️ Doctor Management")
    st.markdown("- View registered doctors.")
    st.markdown("- Register new doctor profiles.")
    st.markdown("*(Page: Doctor Management)*")


    st.subheader("🤖 Chatbot Assistant")
    st.markdown("- Doctors interact with AI.")
    st.markdown("- Check schedules, confirm appointments.")
    st.markdown("- Ask medical questions (via search).")
    st.markdown("*(Page: Chatbot)*")


with col3:
    st.subheader("🩺 Consultation Processing")
    st.markdown("- Input dialogue via text, audio upload, or live recording.")
    st.markdown("- Append additional dialogue.")
    st.markdown("- Generate SOAP notes, follow-ups, education summaries.")
    st.markdown("- Download reports as PDF.")
    st.markdown("*(Page: Consultation Processing)*")

st.markdown("---") 
st.caption("Developed as an AI-enhanced clinical support tool.")