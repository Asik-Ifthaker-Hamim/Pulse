import streamlit as st
from utils.api_client import get_doctors, ask_chatbot
import pandas as pd
from datetime import datetime

st.set_page_config(layout="wide", page_title="Doctor Chatbot")
st.title("🤖 Doctor Chatbot Assistant")

st.sidebar.header("Chat Settings")
doctors_list = get_doctors()
if doctors_list is None: st.error("Could not load doctor list."); st.stop()
if not doctors_list: st.warning("No doctors registered."); st.stop()
doctor_options = {f"{doc['name']} (ID: {doc['id']})": doc['id'] for doc in doctors_list}
selected_doctor_display = st.sidebar.selectbox("Select Doctor Profile", options=list(doctor_options.keys()), index=None, placeholder="Choose doctor...", key="chatbot_doctor_select")

selected_doctor_id = None
if selected_doctor_display:
    selected_doctor_id = doctor_options[selected_doctor_display]
    st.sidebar.caption(f"Chatting as Dr. {selected_doctor_display.split(' (ID:')[0]}")
    st.sidebar.caption(f"Using Doctor ID: `{selected_doctor_id}`")
else: st.warning("Please select a Doctor profile."); st.stop()

st.info("Ask questions about your schedule, confirm appointments, or ask general medical questions.")
st.caption("Examples: 'What is my schedule?', 'Confirm my next appointment', 'Side effects of metformin?'")

history_key = f"chat_history_{selected_doctor_id}"
if history_key not in st.session_state: st.session_state[history_key] = []

for message in st.session_state[history_key]:
    with st.chat_message(message["role"]):
        if "text" in message: st.markdown(message["text"])
        if message.get("response_type") == "schedule" and "schedule_data" in message:
             with st.expander("View Raw Schedule Data", expanded=False):
                 try: df = pd.DataFrame(message["schedule_data"]); st.dataframe(df, hide_index=True)
                 except Exception as e: st.error(f"Error displaying schedule: {e}"); st.json(message["schedule_data"])
        elif message.get("response_type") == "knowledge" and "knowledge_data" in message:
              k_data = message['knowledge_data']
              with st.expander(f"Knowledge Details: {k_data.get('original_question', 'N/A')}", expanded=False):
                  if k_data.get('summary'): st.markdown("**Summary:**"); st.markdown(k_data['summary'])
                  if k_data.get('error_message'): st.error(f"Search Error: {k_data['error_message']}")

if prompt := st.chat_input(f"Ask as Dr. {selected_doctor_display.split(' (ID:')[0]}..."):
    user_message_for_history = {"role": "user", "text": prompt}
    st.session_state[history_key].append(user_message_for_history)
    with st.chat_message("user"): st.markdown(prompt)
    history_for_backend = []
    for msg in st.session_state[history_key]:
        if msg.get("role") in ["user", "assistant"] and msg.get("text"):
            history_for_backend.append({"role": msg["role"], "content": msg["text"]})
    history_limit = 20; history_for_backend = history_for_backend[-history_limit:]
    with st.spinner("Thinking..."):
        response = ask_chatbot(doctor_id=str(selected_doctor_id), message=prompt, chat_history=history_for_backend)

    with st.chat_message("assistant"):
        assistant_message_content = {"role": "assistant"}
        if response and response.get("response_type") != "error":
            response_type = response.get("response_type", "general"); assistant_message_content["response_type"] = response_type
            text_resp = response.get("text_response", "Sorry, I couldn't process that."); st.markdown(text_resp); assistant_message_content["text"] = text_resp
            if response_type == "schedule" and response.get("schedule_data"):
                assistant_message_content["schedule_data"] = response["schedule_data"]
                with st.expander("View Raw Schedule Data", expanded=False):
                    try: df = pd.DataFrame(response["schedule_data"]); st.dataframe(df, hide_index=True)
                    except Exception as e: st.error(f"Error displaying schedule data: {e}"); st.json(response["schedule_data"])
            elif response_type == "knowledge" and response.get("knowledge_data"):
                 assistant_message_content["knowledge_data"] = response["knowledge_data"]; k_data = response["knowledge_data"]
                 with st.expander(f"Knowledge Details: {k_data.get('original_question', 'N/A')}", expanded=False):
                     if k_data.get('summary'): st.markdown("**Summary:**"); st.markdown(k_data['summary'])
                     if k_data.get('error_message'): st.error(f"Search Error: {k_data['error_message']}")
            elif response_type == "confirmation": pass
        else:
            error_msg = response.get("error_message", "Unknown error."); st.error(error_msg)
            assistant_message_content["text"] = f"Error: {error_msg}"; assistant_message_content["response_type"] = "error"
        if not st.session_state[history_key] or st.session_state[history_key][-1] != assistant_message_content:
            st.session_state[history_key].append(assistant_message_content)