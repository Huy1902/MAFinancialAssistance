from typing import Literal
from typing_extensions import TypedDict
from langgraph.graph import MessagesState, END
from langgraph.types import Command
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.prebuilt import create_react_agent
import sys
import os
import streamlit as st
sys.path.append(os.path.abspath("/home/lumasty/Documents/GitHub/MAFinancialAssistance"))
os.environ["TAVILY_API_KEY"] = "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"
tavily_tool = TavilySearchResults(max_results=5)

from DBAgent.Querier import Querier
from SearchAgent.Searcher import Searcher


# Initialize Querier and Searcher
querier = Querier()
searcher = Searcher()

import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv


load_dotenv(override=True)

base_model = os.getenv("MODEL")
base_api = os.getenv("BASE_API")
base_url = os.getenv("BASE_URL")

    

llm = ChatGoogleGenerativeAI(model=base_model, google_api_key=base_api, temperature=0)


members = ["querier", "researcher"]
# Our team supervisor is an LLM node. It just picks the next agent to process
# and decides when the work is completed
options = members + ["FINISH"]

system_prompt = (
    "You are a supervisor tasked with managing a conversation between the"
    f" following workers: {members}. Given the following user request,"
    " respond with the worker to act next. Each worker will perform a"
    " task and respond with their results and status. When finished,"
    " respond with FINISH. Always finish "
)


class Router(TypedDict):
    """Worker to route to next. If no workers needed, route to FINISH."""
    next: Literal[*options]


class State(MessagesState):
    next: str
    queried: bool
    searched: bool


class GraphBuilder():
    def __init__(self, llm, querier):
        self.llm = llm
        self.querier = querier
        self.searcher = searcher
        self.research_agent = create_react_agent(
            llm, tools=[tavily_tool], prompt="You are a researcher. DO NOT do any math.")
        self.conversation = ""

    def supervisor_node(self, state: State) -> Command[Literal[*members, "__end__"]]:
        messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": self.conversation}] + state["messages"]
        response = self.llm.with_structured_output(Router).invoke(messages)
        goto = response["next"]
        
        # No constrain for researcher
        if goto == "FINISH" or (state["queried"] is True or state["searched"] is True):
            return Command(goto=END, update={"next": goto})
        
        # if state["queried"]:
        #     goto = "researcher"

        return Command(goto=goto, update={"next": goto})


    def query_node(self, state: State) -> Command[Literal["supervisor"]]:
        latest_message = state["messages"][-1].content
        result = self.querier.execute_query(latest_message + self.conversation)
        st.write(f"Result query: {result["messages"][-1].content}")
        self.conversation = self.conversation + result["messages"][-1].content
        print(self.conversation)
        return Command(
            update={
                "messages": [
                    HumanMessage(content=result["messages"][-1].content, name="querier")
                ],
                "queried": True
            },
            goto="supervisor",
        )
        
    def research_node(self, state: State) -> Command[Literal["supervisor"]]:
        result = self.research_agent.invoke(state)
        st.write(f"Result searching: {result["messages"][-1].content}")
        self.conversation = self.conversation + result["messages"][-1].content
        print(self.conversation)
        return Command(
            update={
                "messages": [
                    HumanMessage(content=result["messages"][-1].content, name="researcher")
                ],
                "searched": True
            },
            goto="supervisor",
        )

    def build_graph(self):
        builder = StateGraph(State)
        builder.add_edge(START, "supervisor")
        builder.add_node("supervisor", self.supervisor_node)
        builder.add_node("researcher", self.research_node)
        builder.add_node("querier", self.query_node)
        graph = builder.compile()
        return graph

if __name__ == "__main__":
    graph = GraphBuilder(llm, querier).build_graph()
    
    from IPython.display import display, Image

    graph_image = graph.get_graph(xray=True).draw_mermaid_png()
    # Save the graph image to a file and display it
    output_path = "/home/lumasty/Documents/GitHub/MAFinancialAssistance/SuperviseAgent/graph.png"
    with open(output_path, "wb") as f:
        f.write(graph_image)
    print(f"Graph image saved to {output_path}")
    graph = GraphBuilder(llm, querier).build_graph()
    
    # # Initial state
    # initial_state = {
    #     "messages": [HumanMessage(content="What financial assistance programs exist for small businesses?")],
    #     "searched": False,
    #     "queried": False
    # }
    
    # # Execute graph
    # for step in graph.stream(initial_state):
    #     node, result = next(iter(step.items()))
    #     st.write(f"Node: {node} | Result: {result}")