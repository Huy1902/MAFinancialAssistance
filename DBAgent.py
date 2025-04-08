import uuid
from langchain_community.utilities import SQLDatabase
import psycopg2
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from GraphNode.query_prompt import get_query_prompt
from GraphNode.support_function import _print_event
from GraphNode.tool import define_tool
from GraphNode.graph import build_graph_from


class DBAgent:
    def __init__(self):
        self.init_database()
        self.init_llm()
        tools = define_tool(self.db, self.llm)
        chain = get_query_prompt() | self.llm.bind_tools(tools)
        self.graph = build_graph_from(chain, tools)
    
    def init_database(self):
        self.db = SQLDatabase.from_uri("postgresql+psycopg2://postgres:123@localhost:5432/finance-tracker")
    
    def init_llm(self):
        load_dotenv(override=True)
        base_model = os.getenv("MODEL")
        base_api = os.getenv("BASE_API")
        self.llm = ChatGoogleGenerativeAI(model=base_model, google_api_key=base_api, temperature=0)
        # experiment_prefix="sql-agent-gemini"
        # metadata = "Finance, gemini base-case-agent"
        
    def connect(self):
        # Logic to establish a database connection
        pass

    def close(self):
        # Logic to close the database connection
        pass

    def execute_query(self, query):
        # Logic to execute a database query
        
        # Use this unique ID to keep track of the session
        _printed = set()
        thread_id = str(uuid.uuid4())
        config = {
            "configurable": {
                # Checkpoints are accessed by thread_id
                "thread_id": thread_id,
            }
        }
        events = self.graph.stream(
            {"messages": [("user", query)]}, config, stream_mode="values"
        )
        for event in events:
            _print_event(event, _printed)


if __name__ == "__main__":
    agent = DBAgent()
    agent.execute_query("What is the average amount of money I consume per month? My account ID is 0")