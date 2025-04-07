# UI by streamlit
import streamlit as st
import asyncio
from SearchAgent import SearchAgent
from dotenv import load_dotenv


load_dotenv(override=True)

st.set_page_config(page_title="RAGify", page_icon="🤖")
st.title("RAGify")

agent = SearchAgent()


def chunk_generator(llm, query):
    for chunk in llm.stream(query):
        yield chunk


with st.sidebar:
    # llm_model = st.selectbox(label="Select llm model",
    #                          options=[model.model for model in ollama.list().models if model.model != "nomic-embed-text:latest"]
    #                          )
    # search_engine = st.selectbox(label="Select search engine",
    #                          options=["google","duckduckgo"]
    #                          )
    n_results = st.number_input(label="Select number of web results",
                                min_value=1,
                                max_value=8,
                                value=4)
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
        # with st.spinner("extracting queries..."):
        #     # queries = extract_queries(usr_msg, model=llm_model)
        #     # print(queries)
        #     pass

        # with st.spinner("searching on the web..."):
        #     # asyncio.run(fetch_web_pages(queries, n_results, provider=search_engine))

        #     # embedding_function = get_embedding_function()
        #     pass

        # with st.spinner("extract info from webpages..."):
        #     # prompt, sources = generate_prompt(usr_msg, embedding_function)
        #     pass

        # with st.spinner("generating response..."):
        #     # llm = ChatOllama(model=llm_model, stream=True)

        #     # stream_data = chunk_generator(llm, prompt)
        #     # st.write_stream(stream_data)
        #     # st.write(sources)
        #     pass
        try:
            agent.execute(usr_msg)
            # st.write(agent.global_history)
        except Exception as e:
            st.write(f"Error: {e}")
