from DBAgent.Querier import Querier
import os
import sys
import uuid


from SuperviseAgent.GraphBuilder import GraphBuilder
from langchain_core.messages import HumanMessage

sys.path.append(os.path.abspath(
    "/home/lumasty/Documents/GitHub/MAFinancialAssistance"))


class Supervisor():
    def __init__(self, llm):
        querier = Querier(llm)
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
