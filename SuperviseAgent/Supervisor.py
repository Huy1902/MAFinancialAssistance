from DBAgent.Querier import Querier
import os
import sys
import uuid

from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from SuperviseAgent.GraphBuilder import GraphBuilder
from langchain_core.messages import HumanMessage

sys.path.append(os.path.abspath(
    "/home/lumasty/Documents/GitHub/MAFinancialAssistance"))


class Supervisor():
    def __init__(self):
        load_dotenv(override=True)
        base_model = os.getenv("MODEL")
        base_api = os.getenv("BASE_API")

        llm = ChatGoogleGenerativeAI(
            model=base_model, google_api_key=base_api, temperature=0)
        querier = Querier()
        self.graph = GraphBuilder(llm, querier).build_graph()

    def execute(self, query):
        thread_id = str(uuid.uuid4())
        config = {
            "configurable": {
                # Checkpoints are accessed by thread_id
                "thread_id": thread_id,
            }
        }
        initial_state = {
            "messages": [HumanMessage(content=query)],
            "searched": False,
            "queried": False
        }
        # msg = {"messages": [("user", query)]}
        messages = self.graph.invoke(initial_state)
        return messages['messages'][-1].content

