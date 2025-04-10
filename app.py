# UI by streamlit
import os
from datetime import datetime
import streamlit as st
from SearchAgent.Searcher import Searcher
from dotenv import load_dotenv
from SuperviseAgent.Supervisor import Supervisor
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama

load_dotenv(override=True)

st.set_page_config(page_title="Finance Assistant", page_icon="😇")
st.title("Finace Assistant")

ACCOUNT_FILE_PATH = "/tmp/account_id.txt"
load_dotenv(override=True)
base_model = os.getenv("MODEL")
base_api = os.getenv("BASE_API")

# Read account ID before anything else


def get_account_id():
    if os.path.exists(ACCOUNT_FILE_PATH):
        with open(ACCOUNT_FILE_PATH) as f:
            return f.read().strip()
    return "1"


with st.sidebar:
    model = st.selectbox(label="Select model",
                         options=["Gemini-2-flash", "QWen2.5:0.5b", "llama3.2:1b"]
                         )
    typeSearch = st.selectbox(label="Select search",
                              options=["DeepSearch", "PersonalizedSearch"])
return_message = False
# print(model)
if model == "Gemini-2-flash":
    llm = ChatGoogleGenerativeAI(
    model=base_model, google_api_key=base_api, temperature=0)
else:
    llm = ChatOllama(model=model, temperature=0)
if typeSearch == "DeepSearch":
    agent = Searcher()
else:
    agent = Supervisor(llm)
    return_message = True

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
            conversation = ""
            for id, message in enumerate(st.session_state.messages):
                conversation = conversation + f"{id}. role:{message["role"]}, content: {message["content"]}\n"
                st.info(conversation)
            message = agent.execute(f"CURRENT TASK: {usr_msg} PREVIOUS TASK: {conversation}")
            st.session_state.messages.append(
                {"role": "assistant", "content": message})
            if return_message:
                st.write(message)
        except Exception as e:
            st.write(f"Error: {e}")
