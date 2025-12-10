"""
Suggestion endpoint router
Following CLAUDE.md guidelines for structured output and error handling
"""

import uuid
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from models.schema import CanvasRequest, SuggestionResponse, ErrorResponse, Suggestion, Node, Edge
from hld_agent import HLDAgent
from hld_agent.core.exceptions import HLDAgentError, ConfigurationError, LLMError
from services.logger import setup_llm_logger, log_llm_request, log_llm_response

# Set up router and logger
router = APIRouter(prefix="/api/v1", tags=["suggestions"])
logger = setup_llm_logger("suggestion_router")

# Initialize HLD Agent
try:
    hld_agent = HLDAgent()
except ConfigurationError as e:
    logger.error(f"Failed to initialize HLD Agent: {e}")
    raise


def _convert_canvas_to_sequence(canvas_elements, context):
    """
    Convert canvas elements to sequence format expected by HLD Agent.
    
    Extracts component names from canvas elements and builds a simple
    sequence representation for the HLD Agent to analyze.
    """
    components = []
    
    # Extract component names from canvas elements
    for element in canvas_elements:
        if element.get("type") == "rectangle" and element.get("text"):
            component_text = element["text"].strip()
            if component_text and component_text not in components:
                components.append(component_text.lower().replace(" ", "-"))
    
    # Build simple sequence from components
    if len(components) == 0:
        current_sequence = "user req"
    elif len(components) == 1:
        current_sequence = f"user req -> {components[0]}"
    else:
        current_sequence = " -> ".join(["user req"] + components)
    
    # Extract context information
    context_info = ""
    if context:
        if isinstance(context, dict):
            design_type = context.get("design_type", "")
            if design_type:
                context_info = f"{design_type} system"
        elif isinstance(context, str):
            context_info = context
    
    return current_sequence, context_info


def _convert_agent_result_to_response(agent_result):
    """
    Convert HLD Agent result to SuggestionResponse format.
    
    Transforms the structured agent output into the format expected
    by the frontend canvas application.
    """
    if not agent_result.get("success", False):
        return SuggestionResponse(
            suggestion=None,
            reasoning="No architectural suggestions available",
            reference=None
        )
    
    final_sequence = agent_result.get("final_sequence", "")
    
    # Check if agent suggested ending the sequence
    if "__end__" in final_sequence or agent_result.get("output_state", {}).get("next") == "__end__":
        return SuggestionResponse(
            suggestion=None,
            reasoning="Architecture appears complete with current components",
            reference=None
        )
    
    # Extract suggested component from agent output
    output_state = agent_result.get("output_state", {})
    next_component = output_state.get("next", "")
    explanation = output_state.get("explanation", "")
    reasoning = output_state.get("reasoning", "")
    
    if not next_component or next_component == "__end__":
        return SuggestionResponse(
            suggestion=None,
            reasoning=reasoning or "No additional components needed",
            reference=None
        )
    
    # Create node suggestion based on the predicted next component
    suggested_nodes = []
    suggested_edges = []
    
    # Map component to node type and create suggestion
    node_type, node_label = _map_component_to_node(next_component)
    if node_type:
        node_id = f"{next_component}-{uuid.uuid4().hex[:8]}"
        suggested_nodes.append(Node(
            type=node_type,
            label=node_label,
            id=node_id
        ))
        
        # Create edge connecting to the suggested node
        # This is simplified - in a real scenario you'd analyze the sequence better
        suggested_edges.append(Edge(
            **{"from": "previous-component", "to": node_id, "type": "connects-to"}
        ))
    
    suggestion = Suggestion(
        nodes=suggested_nodes,
        edges=suggested_edges
    ) if suggested_nodes else None
    
    return SuggestionResponse(
        suggestion=suggestion,
        reasoning=reasoning or explanation or f"Suggested adding {next_component} to complete the architecture",
        reference=None  # Could be enhanced to include relevant documentation links
    )


def _map_component_to_node(component_name):
    """
    Map HLD Agent component names to schema node types and labels.
    
    This function bridges the gap between the HLD Agent's component
    vocabulary and the frontend's node type system.
    """
    component_mapping = {
        "api-gateway": ("api-gateway", "API Gateway"),
        "api gateway": ("api-gateway", "API Gateway"),
        "gateway": ("api-gateway", "API Gateway"),
        "cache": ("cache", "Cache Layer"),
        "redis": ("cache", "Redis Cache"),
        "database": ("database", "Database"),
        "postgres": ("database", "PostgreSQL Database"),
        "mysql": ("database", "MySQL Database"),
        "db": ("database", "Database"),
        "job-scheduler": ("worker", "Job Scheduler"),
        "scheduler": ("worker", "Job Scheduler"),
        "worker": ("worker", "Worker Service"),
        "queue": ("queue", "Message Queue"),
        "message-queue": ("queue", "Message Queue"),
        "storage": ("storage", "File Storage"),
        "webserver": ("webserver", "Web Server"),
        "web-server": ("webserver", "Web Server"),
        "server": ("webserver", "Web Server"),
        "service-mesh": ("api-gateway", "Service Mesh"),
        "load-balancer": ("api-gateway", "Load Balancer"),
        "auth-service": ("webserver", "Auth Service"),
        "monitoring": ("webserver", "Monitoring Service")
    }
    
    normalized_component = component_name.lower().strip()
    return component_mapping.get(normalized_component, (None, None))


@router.post(
    "/suggest",
    response_model=SuggestionResponse,
    summary="Get AI architectural suggestions",
    description="""
    ## 🎯 Get AI-Powered Architecture Suggestions
    
    Analyze canvas elements and receive intelligent architectural suggestions
    based on system design best practices and common patterns.
    
    ### 🔄 How It Works
    
    1. **Send Canvas State**: Submit current drawing elements and recent changes
    2. **AI Analysis**: Backend analyzes patterns and component relationships  
    3. **Smart Suggestions**: Receive contextual architectural recommendations
    4. **Implementation**: Apply suggestions to improve your system design
    
    ### 📊 Pattern Recognition
    
    The AI recognizes common patterns like:
    - **Basic Web Architecture** (client → server → database)
    - **API Gateway Pattern** (client → gateway → services)
    - **Caching Layer** (server → cache → database)
    - **Message Queue** (producer → queue → consumer)
    - **Load Balancer** (client → balancer → servers)
    
    ### ⚡ Response Format
    
    - **Suggestion**: Up to 2 nodes and 2 edges following strict ontology
    - **Reasoning**: Human-readable explanation of the suggestion
    - **Reference**: Link to relevant documentation or best practices
    
    ### 🛡️ Safety Features
    
    - Input validation with size limits (max 100 elements)
    - Rate limiting and debouncing protection
    - Graceful fallback for analysis failures
    - Structured logging for debugging
    """,
    response_description="AI architectural suggestion with reasoning and references",
    responses={
        200: {
            "description": "Successful AI suggestion",
            "content": {
                "application/json": {
                    "examples": {
                        "caching_suggestion": {
                            "summary": "Cache Layer Suggestion",
                            "description": "Example of AI suggesting a cache layer for performance",
                            "value": {
                                "suggestion": {
                                    "nodes": [
                                        {
                                            "type": "cache",
                                            "label": "Redis Cache",
                                            "id": "redis-cache-1"
                                        }
                                    ],
                                    "edges": [
                                        {
                                            "from": "web-server-1",
                                            "to": "redis-cache-1",
                                            "type": "reads-from"
                                        }
                                    ]
                                },
                                "reasoning": "Added Redis cache to improve database read performance and reduce query latency for frequently accessed data.",
                                "reference": "https://redis.io/docs/about/"
                            }
                        },
                        "no_suggestion": {
                            "summary": "No Suggestion Available", 
                            "description": "Example when no architectural improvements are suggested",
                            "value": {
                                "suggestion": None,
                                "reasoning": "Current architecture appears well-designed with appropriate components and connections.",
                                "reference": None
                            }
                        }
                    }
                }
            }
        },
        413: {
            "description": "Request Entity Too Large",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Canvas too large. Maximum 100 elements allowed."
                    }
                }
            }
        },
        422: {
            "model": ErrorResponse,
            "description": "Validation Error - Invalid request format"
        },
        500: {
            "model": ErrorResponse,
            "description": "Internal Server Error - Analysis failed"
        }
    },
    tags=["suggestions"]
)
async def suggest_architecture(request: CanvasRequest) -> SuggestionResponse:
    """
    Generate AI suggestions for system design based on canvas state
    
    This endpoint:
    1. Validates input using Pydantic models
    2. Analyzes canvas elements for patterns
    3. Returns hardcoded architectural suggestions
    4. Logs all requests/responses for debugging
    """
    request_id = str(uuid.uuid4())
    
    try:
        # Log incoming request
        log_llm_request(
            logger, 
            prompt=f"Canvas analysis request: {len(request.canvas_elements)} elements",
            context={
                "request_id": request_id,
                "element_count": len(request.canvas_elements),
                "has_recent_changes": request.recent_changes is not None,
                "has_context": request.context is not None
            }
        )
        
        # Validate payload size (following CLAUDE.md guidelines)
        if len(request.canvas_elements) > 100:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Canvas too large. Maximum 100 elements allowed."
            )
        
        # Convert canvas elements to sequence format for HLD Agent
        current_sequence, context_info = _convert_canvas_to_sequence(
            request.canvas_elements, request.context
        )
        
        # Generate suggestion using HLD Agent
        agent_result = hld_agent.generate_architecture_suggestion(
            current_sequence=current_sequence,
            context=context_info
        )
        
        # Convert agent result to SuggestionResponse format
        suggestion_response = _convert_agent_result_to_response(agent_result)
        
        # Log successful response
        log_llm_response(
            logger,
            response=str(suggestion_response.dict()),
            valid=True,
            error=None
        )
        
        return suggestion_response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
        
    except (HLDAgentError, LLMError) as e:
        # Handle specific agent errors
        error_msg = f"HLD Agent error: {str(e)}"
        logger.error(error_msg)
        
        log_llm_response(
            logger,
            response="",
            valid=False,
            error=error_msg
        )
        
        # Return safe fallback following CLAUDE.md guidelines
        return SuggestionResponse(
            suggestion=None,
            reasoning="Unable to generate architectural suggestions due to agent error",
            reference=None
        )
        
    except Exception as e:
        # Log error and return safe fallback
        error_msg = f"Internal error processing suggestion request: {str(e)}"
        
        log_llm_response(
            logger,
            response="",
            valid=False,
            error=error_msg
        )
        
        # Return safe fallback following CLAUDE.md guidelines
        return SuggestionResponse(
            suggestion=None,
            reasoning="Unable to process request due to internal error",
            reference=None
        )


@router.get(
    "/providers",
    summary="Get Available LLM Providers",
    description="""
    ## 🤖 Get Available LLM Providers
    
    Return information about available LLM providers and their configuration status.
    
    ### 📊 Provider Information
    
    - **Available Providers**: List of configured providers
    - **Current Provider**: Currently active provider 
    - **Provider Status**: Configuration status for each provider
    """,
    response_description="Available providers and their status",
    responses={
        200: {
            "description": "Provider information retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "available_providers": ["groq", "openai", "anthropic"],
                        "current_provider": "groq",
                        "provider_status": {
                            "groq": True,
                            "openai": False, 
                            "anthropic": False
                        }
                    }
                }
            }
        }
    },
    tags=["providers"]
)
async def get_providers():
    """
    Get information about available LLM providers.
    
    Returns the current provider configuration including which providers
    are available and properly configured.
    """
    try:
        # Get current configuration from HLD Agent
        agent_config = hld_agent.get_configuration()
        current_provider = agent_config.get("llm", {}).get("provider", "groq")
        
        # Get real provider availability status
        provider_status_details = hld_agent.get_all_provider_status()
        
        # Extract available providers and their status
        available_providers = list(provider_status_details.keys())
        provider_status = {
            provider: details["available"] 
            for provider, details in provider_status_details.items()
        }
        
        return {
            "available_providers": available_providers,
            "current_provider": current_provider,
            "provider_status": provider_status
        }
        
    except Exception as e:
        logger.error(f"Failed to get providers: {e}")
        return {
            "available_providers": ["groq"],
            "current_provider": "groq", 
            "provider_status": {"groq": True}
        }


@router.post(
    "/providers/switch",
    summary="Switch LLM Provider",
    description="""
    ## 🔄 Switch Active LLM Provider
    
    Switch the active LLM provider for architecture suggestions.
    
    ### ⚠️ Note
    
    Provider switching is currently not implemented in the HLD Agent.
    This endpoint returns the current provider status.
    """,
    response_description="Provider switch result",
    responses={
        200: {
            "description": "Provider switch completed",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Switched to groq",
                        "current_provider": "groq"
                    }
                }
            }
        },
        400: {
            "description": "Provider switch failed",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": "Provider 'invalid' not available"
                    }
                }
            }
        }
    },
    tags=["providers"]
)
async def switch_provider(request: dict):
    """
    Switch the active LLM provider using HLD Agent.
    
    Dynamically switches between configured providers (groq, openai, anthropic).
    """
    try:
        provider = request.get("provider", "").lower()
        
        # Check if provider is available first
        availability = hld_agent.check_provider_availability(provider)
        if not availability["available"]:
            return {
                "success": False,
                "error": f"Provider '{provider}' not available: {availability['reason']}"
            }
        
        # Attempt to switch provider using HLD Agent
        switch_result = hld_agent.switch_provider(provider)
        
        if switch_result["success"]:
            logger.info(f"Successfully switched to provider: {provider}")
            return {
                "success": True,
                "message": switch_result["message"],
                "current_provider": switch_result["current_provider"],
                "previous_provider": switch_result.get("previous_provider")
            }
        else:
            logger.error(f"Provider switch failed: {switch_result['error']}")
            return {
                "success": False,
                "error": switch_result["error"]
            }
            
    except Exception as e:
        logger.error(f"Provider switch failed: {e}")
        return {
            "success": False,
            "error": f"Internal error: {str(e)}"
        }


@router.get(
    "/health",
    summary="Suggestion Service Health Check",
    description="""
    ## 🏥 Health Check for AI Suggestion Service
    
    Verify that the suggestion service is running properly and
    ready to process architectural analysis requests.
    
    ### ✅ What This Checks
    
    - Service availability and responsiveness
    - Pattern database loading status
    - Internal component health
    
    ### 📊 Response Information
    
    - **Status**: Overall service health (healthy/unhealthy)
    - **Service**: Service identifier  
    - **Patterns Loaded**: Number of architectural patterns available
    """,
    response_description="Service health status and metadata",
    responses={
        200: {
            "description": "Service is healthy and operational",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "service": "suggestion_router", 
                        "patterns_loaded": 5
                    }
                }
            }
        }
    },
    tags=["health"]
)
async def suggestion_health():
    """
    Health check endpoint for the AI suggestion service.
    
    Returns the current status of the suggestion service including
    the number of loaded architectural patterns.
    """
    # Get health status from HLD Agent
    try:
        agent_health = hld_agent.get_health_status()
        return {
            "status": agent_health.get("status", "unknown"),
            "service": "suggestion_router",
            "agent_version": agent_health.get("agent_version", "unknown"),
            "model": agent_health.get("model", "unknown"),
            "last_test_duration": agent_health.get("last_test_duration")
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "suggestion_router",
            "error": str(e)
        }