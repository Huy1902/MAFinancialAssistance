from langchain_core.runnables import Runnable, RunnableConfig
from DBAgent.State import State
import streamlit as st

# Assistant
class Assistant:
    
    def __init__(self, runnable: Runnable):
        self.runnable = runnable

    def __call__(self, state: State, config: RunnableConfig):
        with st.spinner("Generate database query"):
            while True:
                # Append to state
                state = {**state}
                # Invoke the tool-calling LLM
                result = self.runnable.invoke(state)
                # If it is a tool call -> response is valid
                # If it has meaninful text -> response is valid
                # Otherwise, we re-prompt it b/c response is not meaninful
                if not result.tool_calls and (
                    not result.content
                    or isinstance(result.content, list)
                    and not result.content[0].get("text")
                ):
                    messages = state["messages"] + [("user", "Respond with a real output.")]
                    state = {**state, "messages": messages}
                else:
                    st.write(result)
                    break
        return {"messages": result}