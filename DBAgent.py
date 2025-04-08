from langchain_community.utilities import SQLDatabase
import psycopg2
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from util.tool import define_tool


class DBAgent:
    def __init__(self):
        self.init_database()
        self.init_llm()
        self.tools = define_tool(self.db, self.llm)
    
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
        pass

    def fetch_results(self):
        # Logic to fetch results from the executed query
        pass