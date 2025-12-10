"""Pydantic schema models for HLD Agent.

These models are extracted exactly from hld_agent.py to maintain compatibility.
"""

from pydantic import BaseModel, Field
from typing import Optional, Annotated
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class ArchInputState(BaseModel):
    """Input state for architecture generation - extracted from hld_agent.py lines 19-21."""
    current_sequence: str = Field(..., min_length=1, description="Current architecture sequence")
    context: str = Field(default="", description="Additional context about the system being designed")


class ArchOutputState(BaseModel):
    """Output state for architecture generation - extracted from hld_agent.py lines 23-27."""
    explanation: str = Field(..., min_length=1, description="Why this component logically follows from the previous components")
    next: str = Field(..., min_length=1, description="Next component name or '__end__' to stop the sequence")
    current_sequence: str = Field(..., min_length=1, description="Updated full architecture sequence with the new component")
    reasoning: str = Field(..., min_length=1, description="Detailed architectural reasoning for this choice")


class StructuredArchitectureState(TypedDict):
    """LangGraph state for structured architecture generation - extracted from hld_agent.py lines 49-54."""
    messages: Annotated[list[BaseMessage], add_messages]
    input_state: ArchInputState
    output_state: Optional[ArchOutputState]
    is_complete: bool
    iteration_count: int  # Track iterations for recursion limit


# Test data for validation (from hld_agent.py lines 31-39)
SAMPLE_INPUT = ArchInputState(
    current_sequence="user req -> load balancer", 
    context="distributed job scheduler"
)

SAMPLE_OUTPUT = ArchOutputState(
    explanation="API gateway handles routing and authentication",
    next="api gateway", 
    current_sequence="user req -> load balancer -> api gateway",
    reasoning="In distributed systems, API gateways provide centralized request routing, authentication, and rate limiting"
)