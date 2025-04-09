import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver
from langchain_community.utilities import SQLDatabase
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import tools_condition

from DBAgent.State import State
from DBAgent.Assistant import Assistant
from DBAgent.query_prompt import get_query_prompt
from DBAgent.support_function import create_tool_node_with_fallback
from DBAgent.tool import define_tool
from IPython.display import Image, display


def build_graph_from(chain, tools):

    builder = StateGraph(State)

    # Define nodes: these do the work
    builder.add_node("assistant", Assistant(chain))
    builder.add_node("tools", create_tool_node_with_fallback(tools))

    # Define edges: these determine how the control flow moves
    builder.set_entry_point("assistant")
    builder.add_conditional_edges(
        "assistant",
        # If the latest message (result) from assistant is a tool call -> tools_condition routes to tools
        # If the latest message (result) from assistant is a not a tool call -> tools_condition routes to END
        tools_condition,
        # "tools" calls one of our tools. END causes the graph to terminate (and respond to the user)
        {"tools": "tools", END: END},
    )
    builder.add_edge("tools", "assistant")

    # The checkpointer lets the graph persist its state
    # Use in-memory checkpointer
    memory = MemorySaver()
    graph = builder.compile(checkpointer=memory)

    return graph


if __name__ == "__main__":
    load_dotenv()
    base_model = os.getenv("MODEL")
    base_api = os.getenv("BASE_API")
    llm = ChatGoogleGenerativeAI(
        model=base_model, google_api_key=base_api, temperature=0)
    db = SQLDatabase.from_uri(
        "postgresql+psycopg2://postgres:123@localhost:5432/finance-tracker")
    tools = define_tool(db, llm)
    chain = get_query_prompt() | llm.bind_tools(tools)
    graph = build_graph_from(chain, tools)
    graph_image = graph.get_graph(xray=True).draw_mermaid_png()
    # Save the graph image to a file and display it
    output_path = "/home/lumasty/Documents/GitHub/MAFinancialAssistance/GraphNode/graph.png"
    with open(output_path, "wb") as f:
        f.write(graph_image)
    print(f"Graph image saved to {output_path}")
