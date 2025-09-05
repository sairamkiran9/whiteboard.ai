"""
Suggestion endpoint router
Following CLAUDE.md guidelines for structured output and error handling
"""

import uuid
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from models.schema import CanvasRequest, SuggestionResponse, ErrorResponse
from services.suggestion_service import HardcodedSuggestionService
from services.logger import setup_llm_logger, log_llm_request, log_llm_response

# Set up router and logger
router = APIRouter(prefix="/api/v1", tags=["suggestions"])
logger = setup_llm_logger("suggestion_router")
suggestion_service = HardcodedSuggestionService()


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
        
        # Generate suggestion using hardcoded service
        suggestion_response = suggestion_service.get_suggestion(
            canvas_elements=request.canvas_elements,
            context=request.context
        )
        
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
    return {
        "status": "healthy",
        "service": "suggestion_router",
        "patterns_loaded": len(suggestion_service.patterns)
    }