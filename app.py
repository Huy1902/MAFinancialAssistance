# UI by streamlit
import streamlit as st
from SearchAgent.Searcher import Searcher
from dotenv import load_dotenv
from SuperviseAgent.Supervisor import Supervisor
import os
from datetime import datetime

load_dotenv(override=True)

st.set_page_config(page_title="Finance Assistant", page_icon="😇")
st.title("Finace Assistant")

ACCOUNT_FILE_PATH = "/tmp/account_id.txt"

# Read account ID before anything else


def get_account_id():
    if os.path.exists(ACCOUNT_FILE_PATH):
        with open(ACCOUNT_FILE_PATH) as f:
            return f.read().strip()
    return "unknown"


with st.sidebar:
    model = st.selectbox(label="Select model",
                         options=["DeepSearch", "PersonalizedSearch"]
                         )
return_message = False
if model == "DeepSearch":
    agent = Searcher()
else:
    agent = Supervisor()
    return_message = True

conversation = ""
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant",
            "content": "Hi, I'm a chatbot who can search the web. How can I help you?"}
    ]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if usr_msg := st.chat_input():
    st.session_state.messages.append(
        {"role": "user", "content": usr_msg + f"My account ID is:{get_account_id()}"})
        
    st.chat_message("user").write(usr_msg)

    with st.chat_message("assistant"):
        try:
            if return_message:
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                usr_msg = usr_msg + f" My account ID is:{get_account_id()}. Today is {current_time} (Vietnam Time)"
            st.write(usr_msg)
            message = agent.execute(usr_msg)
            if return_message:
                st.write(message)
        except Exception as e:
            st.write(f"Error: {e}")
