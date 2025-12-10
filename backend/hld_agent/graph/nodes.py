"""LangGraph nodes for HLD Agent.

This module contains the exact node implementations from hld_agent.py 
lines 160-253, preserving all logic and behavior.
"""

from langchain_core.messages import HumanMessage, AIMessage
from ..schemas.models import StructuredArchitectureState, ArchInputState, ArchOutputState
from ..llm.models import get_llm_chain
from ..config.settings import get_settings
from ..core.exceptions import LLMError, GraphExecutionError
from ..utils.logging import get_logger

logger = get_logger(__name__)


def pure_structured_assistant(state: StructuredArchitectureState) -> dict:
    """
    Pure structured output assistant with recursion limit handling.
    
    Extracted exactly from hld_agent.py lines 160-222, maintaining all logic.
    
    Args:
        state: Current graph state
        
    Returns:
        Updated state dictionary
    """
    try:
        # Get configuration
        settings = get_settings()
        
        # Check if we've hit reasonable iteration limits (before running out of recursion limit)
        max_iterations = settings.llm.max_iterations  # Configurable now instead of hardcoded 6
        current_iteration = state.get("iteration_count", 0) + 1
        
        logger.info(f"Processing iteration {current_iteration}/{max_iterations}")
        
        if current_iteration >= max_iterations:
            # Force completion when approaching limit
            completion_output = ArchOutputState(
                explanation=f"Architecture complete after {current_iteration} components",
                next="__end__",
                current_sequence=state["input_state"].current_sequence,
                reasoning=f"Reached maximum iteration limit ({max_iterations}), system architecture is sufficiently complete"
            )
            
            logger.info(f"🏁 Architecture complete after {current_iteration} iterations")
            return {
                "messages": [AIMessage(content=f"🏁 Architecture complete after {current_iteration} iterations")],
                "output_state": completion_output,
                "is_complete": True,
                "iteration_count": current_iteration
            }
        
        # Build input for structured chain
        chain_input = {
            "current_sequence": state["input_state"].current_sequence,
            "context": state["input_state"].context
        }
        
        logger.debug(f"Chain input: {chain_input}")
        
        # Get LLM chain
        llm_structured, structured_prompt = get_llm_chain(settings)
        
        # Direct structured output call - no tool complexity  
        chain = structured_prompt | llm_structured
        output: ArchOutputState = chain.invoke(chain_input)
        
        logger.info(f"LLM prediction: {output.next}")
        
        # Create AI message
        ai_message = AIMessage(
            content=f"Added: {output.next} | Sequence: {output.current_sequence} | Iteration: {current_iteration}"
        )
        
        # Determine completion
        is_complete = output.next == "__end__"
        
        return {
            "messages": [ai_message],
            "output_state": output,  # Store parsed object directly
            "is_complete": is_complete,
            "iteration_count": current_iteration
        }
        
    except Exception as e:
        # Error handling with fallback (exact logic from hld_agent.py lines 208-222)
        logger.error(f"Error in pure_structured_assistant: {str(e)}")
        
        error_output = ArchOutputState(
            explanation=f"Error: {str(e)}",
            next="__end__",
            current_sequence=state["input_state"].current_sequence,
            reasoning="Stopping due to error"
        )
        
        return {
            "messages": [AIMessage(content=f"❌ Error: {str(e)}")],
            "output_state": error_output,
            "is_complete": True,
            "iteration_count": state.get("iteration_count", 0) + 1
        }


def update_state_node(state: StructuredArchitectureState) -> dict:
    """
    Update state node - preserves iteration count and handles completion properly.
    
    Extracted exactly from hld_agent.py lines 227-251, maintaining all logic.
    
    Args:
        state: Current graph state
        
    Returns:
        Updated state dictionary
    """
    logger.debug("Updating state node")
    
    if not state["output_state"] or state["is_complete"]:
        logger.info("Marking state as complete")
        return {"is_complete": True}
    
    output_state = state["output_state"]
    current_iteration = state.get("iteration_count", 0)
    
    # Continue if we haven't reached the end
    if output_state.next != "__end__" and not state["is_complete"]:
        # Create new input state for next iteration using parsed object
        new_input = ArchInputState(
            current_sequence=output_state.current_sequence,  # From parsed object
            context=state["input_state"].context
        )
        
        logger.info(f"Continuing with sequence: {output_state.current_sequence}")
        
        return {
            "input_state": new_input,
            "is_complete": False,
            "iteration_count": current_iteration  # Preserve count
        }
    
    # Mark complete
    logger.info("Sequence complete")
    return {"is_complete": True}


def should_continue_simple(state: StructuredArchitectureState) -> str:
    """
    Simple conditional function to determine graph flow.
    
    Extracted from hld_agent.py lines 267-273, maintaining exact logic.
    
    Args:
        state: Current graph state
        
    Returns:
        Next step in the graph ("continue" or "__end__")
    """
    if state["is_complete"]:
        logger.debug("Graph flow: ending due to completion flag")
        return "__end__"
    
    if state["output_state"] and state["output_state"].next == "__end__":
        logger.debug("Graph flow: ending due to output state")
        return "__end__"
    
    logger.debug("Graph flow: continuing")
    return "continue"