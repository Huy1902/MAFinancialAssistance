from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import AnyMessage, add_messages

# Define State structure to hold messages and history
class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    query_count: int