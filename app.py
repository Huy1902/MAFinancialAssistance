# UI by streamlit
import streamlit as st
import asyncio
from SearchAgent import SearchAgent
from dotenv import load_dotenv


load_dotenv(override=True)

st.set_page_config(page_title="Finance Assistant", page_icon="😇")
st.title("Finace Assistant")

agent = SearchAgent()


def chunk_generator(llm, query):
    for chunk in llm.stream(query):
        yield chunk
        
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant",
            "content": "Hi, I'm a chatbot who can search the web. How can I help you?"}
    ]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if usr_msg := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": usr_msg})
    st.chat_message("user").write(usr_msg)

    with st.chat_message("assistant"):
        try:
            agent.task_stopped = False
            agent.stop_processing = False
            agent.execute(usr_msg)
        except Exception as e:
            st.write(f"Error: {e}")
