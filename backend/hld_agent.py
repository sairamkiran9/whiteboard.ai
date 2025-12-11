# human in loop

import os
import operator
from typing import List, Annotated, Optional, TypedDict, Literal
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from groq import Groq
import instructor
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# Load env variables
load_dotenv()

# --- 1. Setup Models & LLM ---

class ArchitecturePrediction(BaseModel):
    """Output for Option 1: AI Auto-suggest"""
    next_component: str = Field(..., description="The single next component to add.")
    reasoning: str = Field(..., description="Why this component comes next.")

class ValidationResult(BaseModel):
    """Output for Custom Input: Checking user's idea"""
    is_valid: bool = Field(..., description="Is this component technically feasible and logical here?")
    feedback: str = Field(..., description="If valid, why it fits. If invalid, why it fails.")

client = instructor.from_groq(
    Groq(api_key=os.environ["GROQ_API_KEY"]),
    mode=instructor.Mode.JSON
)

# --- 2. Define State ---

class AgentState(TypedDict):
    # The architecture string (e.g., "Client -> Load Balancer")
    current_sequence: str
    context: str
    
    # User interaction data
    user_input: Optional[str]
    system_message: Optional[str] # To hold errors or success messages
    
    # History log
    history: Annotated[List[str], operator.add]

# --- 3. Define Nodes ---

def human_node(state: AgentState):
    """
    This node stops and asks the user for input.
    """
    print("\n" + "="*50)
    print(f"CURRENT ARCHITECTURE:\n{state['current_sequence']}")
    print("="*50)
    
    if state.get("system_message"):
        print(f"System Message: {state['system_message']}")
    
    print("\nOptions:")
    print(" [1] Auto-generate next step (Default)")
    print(" [2] Stop and Finish")
    print(" [Type Name] Enter a custom component (e.g., 'Redis Cache')")
    
    user_choice = input("\nYour choice: ").strip()
    
    # Default to 1 if empty
    if not user_choice:
        user_choice = "1"
        
    return {"user_input": user_choice, "system_message": None}

def ai_generate_node(state: AgentState):
    """
    Option 1: AI predicts the next component.
    """
    print("🤖 AI is thinking...")
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        response_model=ArchitecturePrediction,
        messages=[
            {"role": "system", "content": "You are a distributed systems architect."},
            {"role": "user", "content": f"Context: {state['context']}\nCurrent: {state['current_sequence']}\nTask: Predict next component."}
        ]
    )
    
    new_fragment = f" -> {response.next_component}"
    updated_sequence = state['current_sequence'] + new_fragment
    
    return {
        "current_sequence": updated_sequence,
        "history": [f"AI Added: {response.next_component}"],
        "system_message": f"Auto-added '{response.next_component}' based on: {response.reasoning}"
    }

def validate_input_node(state: AgentState):
    """
    Option Custom: AI checks if user input is valid.
    """
    user_component = state["user_input"]
    print(f"🔍 Validating '{user_component}'...")
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        response_model=ValidationResult,
        messages=[
            {"role": "system", "content": "You are a strict technical reviewer."},
            {"role": "user", "content": f"""
             Context: {state['context']}
             Current Sequence: {state['current_sequence']}
             User Suggestion: {user_component}
             
             Task: Determine if the user suggestion is a valid next step.
             """}
        ]
    )
    
    if response.is_valid:
        new_fragment = f" -> {user_component}"
        return {
            "current_sequence": state['current_sequence'] + new_fragment,
            "history": [f"User Added: {user_component}"],
            "system_message": f"✅ Accepted '{user_component}'. {response.feedback}"
        }
    else:
        # Do not update sequence, just send feedback
        return {
            "system_message": f"❌ Rejected '{user_component}'. {response.feedback}"
        }

# --- 4. Define Logic Branching ---

def router(state: AgentState) -> Literal["ai_generate", "validate_input", "end"]:
    choice = state["user_input"]
    
    if choice == "1":
        return "ai_generate"
    elif choice == "2":
        return "end"
    else:
        return "validate_input"

# --- 5. Build Graph ---

workflow = StateGraph(AgentState)

workflow.add_node("human", human_node)
workflow.add_node("ai_generate", ai_generate_node)
workflow.add_node("validate_input", validate_input_node)

workflow.set_entry_point("human")

workflow.add_conditional_edges(
    "human",
    router,
    {
        "ai_generate": "ai_generate",
        "validate_input": "validate_input",
        "end": END
    }
)

# Loop back to human after processing
workflow.add_edge("ai_generate", "human")
workflow.add_edge("validate_input", "human")

graph = workflow.compile(checkpointer=MemorySaver())

# --- 6. Run ---

initial_state = {
    "current_sequence": "User Request",
    "context": "A high-traffic e-commerce checkout system",
    "history": [],
    "user_input": None,
    "system_message": "Initialization Complete."
}

config = {"configurable": {"thread_id": "session_2"}}

# We use graph.invoke (or stream) here. 
# Since we use input() inside the node, standard recursion limits apply.
try:
    graph.invoke(initial_state, config)
except Exception:
    pass # Handles the "Stop" gracefully if needed, or just let it finish naturally via END