import uuid
from langchain_community.utilities import SQLDatabase
from DBAgent.query_prompt import get_query_prompt
from DBAgent.tool import define_tool
from DBAgent.graph import build_graph_from


class Querier():
    def __init__(self, llm):
        self.init_database()
        tools = define_tool(self.db, llm)
        chain = get_query_prompt() | llm.bind_tools(tools)
        self.graph = build_graph_from(chain, tools)
    
    def init_database(self):
        self.db = SQLDatabase.from_uri("postgresql+psycopg2://postgres:123@localhost:5432/finance-tracker")

        
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
        # events = self.graph.stream(
        #     {"messages": [("user", query)]}, config, stream_mode="values"
        # )
        # for event in events:
        #     _print_event(event, _printed)
        msg = {"messages": [("user", query)]}
        messages = self.graph.invoke(msg,config)
        # print(messages['messages'][-1].content)
        return messages


# if __name__ == "__main__":
#     agent = Querier()
#     agent.execute_query("What is the average amount of money I consume per month? My account ID is 0")