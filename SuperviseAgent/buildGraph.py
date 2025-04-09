from typing import Literal
from typing_extensions import TypedDict
from langgraph.graph import MessagesState, END
from langgraph.types import Command
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
import sys
import os
sys.path.append(os.path.abspath("/home/lumasty/Documents/GitHub/MAFinancialAssistance"))


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


members = ["querier", "searcher"]
# Our team supervisor is an LLM node. It just picks the next agent to process
# and decides when the work is completed
options = members + ["FINISH"]

system_prompt = (
    "You are a supervisor managing specialized AI workers: {member}.\n\n"

    "The user will provide a high-level request or question. Your job is to:\n"
    "1. Break the user request into smaller sub-tasks.\n"
    "2. Assign each sub-task to the appropriate worker.\n"
    "   - Use 'searcher' for internet searches, general knowledge, current events, or finding external facts.\n"
    "   - Use 'querier' to query internal databases, perform data lookups, or analyze structured data.\n"
    "3. Route the next unfinished sub-task to the correct agent.\n"
    "4. When all sub-tasks have been completed, respond with 'FINISH'.\n\n"

    "Return ONLY one of the following:\n"
    "- 'searcher' → if the next task requires internet research.\n"
    "- 'querier' → if the next task requires querying internal databases.\n"
    "- 'FINISH' → if all work is complete.\n\n"

    "You will receive the full conversation history, including user input and agent outputs. Use that to determine what has already been done and what remains.\n"
)


class Router(TypedDict):
    """Worker to route to next. If no workers needed, route to FINISH."""
    next: Literal[*options]


class State(MessagesState):
    next: str


class GraphBuilder():
    def __init__(self, llm, querier, searcher):
        self.llm = llm
        self.querier = querier
        self.searcher = searcher

    def supervisor_node(self, state: State) -> Command[Literal[*members, "__end__"]]:
        messages = [
        {"role": "system", "content": system_prompt},
        ] + state["messages"]
        response = self.llm.with_structured_output(Router).invoke(messages)
        goto = response["next"]
        if goto == "FINISH":
            goto = END

        return Command(goto=goto, update={"next": goto})
    
    def search_node(self, state: State) -> Command[Literal["supervisor"]]:
        latest_message = state["messages"][-1].content
        result = self.searcher.execute(latest_message)
        return Command(
            update={
                "messages": [
                    HumanMessage(content=result, name="researcher")
                ]
            },
            goto="supervisor",
        )


    def query_node(self, state: State) -> Command[Literal["supervisor"]]:
        latest_message = state["messages"][-1].content
        result = self.querier.execute_query(latest_message)
        return Command(
            update={
                "messages": [
                    HumanMessage(content=result["messages"][-1].content, name="querier")
                ]
            },
            goto="supervisor",
        )

    def buildGraph(self):
        builder = StateGraph(State)
        builder.add_edge(START, "supervisor")
        builder.add_node("supervisor", self.supervisor_node)
        builder.add_node("searcher", self.search_node)
        builder.add_node("querier", self.query_node)
        graph = builder.compile()
        return graph

if __name__ == "__main__":
    graph = GraphBuilder(llm, querier, searcher).buildGraph()
    
    from IPython.display import display, Image

    graph_image = graph.get_graph(xray=True).draw_mermaid_png()
    # Save the graph image to a file and display it
    output_path = "/home/lumasty/Documents/GitHub/MAFinancialAssistance/SuperviseAgent/graph.png"
    with open(output_path, "wb") as f:
        f.write(graph_image)
    print(f"Graph image saved to {output_path}")