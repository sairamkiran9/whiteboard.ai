"""LangGraph builder for HLD Agent.

This module contains the exact graph setup from hld_agent.py lines 256-298,
maintaining all configuration and flow logic.
"""

from langgraph.graph import START, StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from ..schemas.models import StructuredArchitectureState
from ..config.settings import get_settings
from ..utils.logging import get_logger
from .nodes import pure_structured_assistant, update_state_node, should_continue_simple

logger = get_logger(__name__)


def create_hld_graph(with_memory: bool = True):
    """
    Create the HLD architecture graph exactly as in hld_agent.py lines 256-298.
    
    Args:
        with_memory: Whether to enable memory checkpointing
        
    Returns:
        Compiled LangGraph instance
    """
    logger.info("🎯 Creating HLD graph - NO tools, NO complexity!")
    
    # Create the StateGraph with our custom state (from hld_agent.py line 260)
    builder = StateGraph(StructuredArchitectureState)
    
    # Define nodes (clean and simple) - from hld_agent.py lines 263-264
    builder.add_node("pure_assistant", pure_structured_assistant)
    builder.add_node("update_state", update_state_node)
    
    # Define edges (clean flow) - from hld_agent.py lines 275-282
    builder.add_edge(START, "pure_assistant")
    builder.add_conditional_edges(
        "pure_assistant",
        should_continue_simple,
        {"continue": "update_state", "__end__": END}
    )
    builder.add_edge("update_state", "pure_assistant")
    
    # Compile the graph
    if with_memory:
        # Create memory and compile clean graph (from hld_agent.py lines 294-296)
        memory = MemorySaver()
        graph = builder.compile(checkpointer=memory)
        logger.info("✅ Clean structured graph with memory compiled!")
    else:
        graph = builder.compile()
        logger.info("✅ Clean structured graph compiled (no memory)!")
    
    return graph


def create_execution_config(thread_id: str = "hld-session", recursion_limit: int = None) -> dict:
    """
    Create execution configuration for the graph.
    
    Args:
        thread_id: Unique thread identifier for this session
        recursion_limit: Maximum recursion limit (from config if None)
        
    Returns:
        Configuration dictionary for graph execution
    """
    settings = get_settings()
    
    if recursion_limit is None:
        recursion_limit = settings.graph.recursion_limit
    
    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": recursion_limit
    }
    
    logger.info(f"Created execution config: thread_id={thread_id}, recursion_limit={recursion_limit}")
    return config


def create_initial_state(current_sequence: str, context: str) -> StructuredArchitectureState:
    """
    Create initial state for graph execution.
    
    Extracted from hld_agent.py lines 307-318, maintaining exact structure.
    
    Args:
        current_sequence: Starting architecture sequence
        context: System context description
        
    Returns:
        Initial StructuredArchitectureState
    """
    from langchain_core.messages import HumanMessage
    from ..schemas.models import ArchInputState
    
    initial_state = StructuredArchitectureState(
        messages=[HumanMessage(content=f"Building architecture for: {context}")],
        input_state=ArchInputState(
            current_sequence=current_sequence,
            context=context
        ),
        output_state=None,
        is_complete=False,
        iteration_count=0  # Start iteration counting
    )
    
    logger.info(f"Created initial state: sequence='{current_sequence}', context='{context}'")
    return initial_state