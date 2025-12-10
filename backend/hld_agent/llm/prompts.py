"""Prompt templates for HLD Agent.

This module contains the exact prompt template extracted from hld_agent.py
to maintain consistency with the original implementation.
"""

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from ..schemas.models import ArchOutputState


def get_system_prompt(format_instructions: str) -> ChatPromptTemplate:
    """
    Get the system prompt template exactly as defined in hld_agent.py lines 128-151.
    
    Args:
        format_instructions: Format instructions from PydanticOutputParser
        
    Returns:
        ChatPromptTemplate configured with the exact system prompt
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert system architect predicting the next logical component in a system flow.

{format_instructions}

IMPORTANT GUIDELINES:
1. **Next Component Logic**: Predict the very next component that should logically follow in the architecture flow
2. **Component Examples**: api-gateway, service-mesh, cache (redis), database (postgres), message-queue, worker-pool, job-scheduler, storage, monitoring, auth-service
3. **Sequence Building**: Always append the new component to current_sequence with " -> new_component"
4. **Completion Rules**: 
   - Use "next": "__end__" ONLY when the system is architecturally complete (typically 4-6 components)
   - Continue building if the flow needs more components
   - Context: {context}

EXAMPLE FLOWS:
- Job Scheduler: user req -> load balancer -> api gateway -> job scheduler -> message queue -> worker nodes -> database
- Web App: user req -> load balancer -> api gateway -> cache -> microservices -> database

Think step by step:
1. What is the current sequence missing?
2. What would be the very next logical component?
3. Is the system complete or needs more components?"""),
        ("human", "Current sequence: {current_sequence}\n\nWhat should be the NEXT component in this architecture?")
    ])
    
    # Add format instructions
    prompt = prompt.partial(format_instructions=format_instructions)
    
    return prompt


def create_structured_prompt_chain():
    """Create the complete prompt chain with PydanticOutputParser."""
    parser = PydanticOutputParser(pydantic_object=ArchOutputState)
    format_instructions = parser.get_format_instructions()
    
    prompt = get_system_prompt(format_instructions)
    
    return prompt, parser