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
from GraphBuilder import GraphBuilder
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


graph = GraphBuilder(llm, querier).build_graph()
    
from IPython.display import display, Image

# graph_image = graph.get_graph(xray=True).draw_mermaid_png()
# Save the graph image to a file and display it
# output_path = "/home/lumasty/Documents/GitHub/MAFinancialAssistance/SuperviseAgent/graph.png"
# with open(output_path, "wb") as f:
#     f.write(graph_image)
# print(f"Graph image saved to {output_path}")
try:
    mermaid_code = graph.get_graph(xray=True).draw_mermaid()
    with open("/home/lumasty/Documents/GitHub/MAFinancialAssistance/SuperviseAgent/graph.mmd", "w") as f:
        f.write(mermaid_code)
except Exception as e:
    print("Mermaid render failed:", e)
