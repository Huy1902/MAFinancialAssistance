from typing import Literal, List, Optional
from typing_extensions import TypedDict
from langgraph.graph import MessagesState
from langchain_core.messages import BaseMessage

# Define options including the new summarizer
members = ["querier", "researcher", "summarizer"]
options = members + ["FINISH"]

# Pydantic model for structured supervisor output
from pydantic import BaseModel, Field

class SupervisorDecision(BaseModel):
    """The decision on the next step and the specific task prompt."""
    next_node: Literal[*options] = Field(description=f"The next worker node to call: {', '.join(members)} or FINISH.")
    task_prompt: Optional[str] = Field(description="The specific, detailed prompt or question for the selected worker node. Should be empty if next_node is 'summarizer' or 'FINISH'.")

class AgentState(MessagesState):
    """Extends MessagesState to include routing information and task details."""
    next_node: str
    current_task_prompt: str
    querier_ran: bool # Flag to track if querier has run
    # Store the original query for the summarizer
    original_query: str