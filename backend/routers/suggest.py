"""
Suggestion endpoint router using Canvas-Aware HLD Agent
Following CLAUDE.md guidelines for structured output and error handling
"""

import uuid
import json
import tempfile
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from models.schema import CanvasRequest, SuggestionResponse, ErrorResponse, Suggestion, Node, Edge
from hld_agent_canvas_integration import CanvasAwareHLDAgent
from hld_agent.models import AgentResponse, ComponentSuggestion
from services.logger import setup_llm_logger, log_llm_request, log_llm_response

# Set up router and logger
router = APIRouter(prefix="/api/v1", tags=["suggestions"])
logger = setup_llm_logger("suggestion_router")

# Initialize Canvas-Aware HLD Agent
try:
    canvas_agent = CanvasAwareHLDAgent()
    logger.info("Canvas-Aware HLD Agent initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Canvas-Aware HLD Agent: {e}")
    raise


def _convert_to_excalidraw_canvas(canvas_elements: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Convert API canvas elements to full Excalidraw canvas format.

    The CanvasAwareHLDAgent expects a complete Excalidraw JSON structure.
    """
    return {
        "type": "excalidraw",
        "version": 2,
        "source": "https://excalidraw.com",
        "elements": canvas_elements,
        "appState": {
            "gridSize": None,
            "viewBackgroundColor": "#ffffff"
        },
        "files": {}
    }


def _create_ghost_excalidraw_elements(suggestions: List[ComponentSuggestion]) -> List[Dict[str, Any]]:
    """
    Create Excalidraw-compatible ghost elements from ComponentSuggestions.

    Generates semi-transparent dashed rectangles with labels at suggested positions.
    """
    ghost_elements = []

    for suggestion in suggestions:
        if not suggestion.position_hint:
            continue

        # Create ghost rectangle
        element_id = f"ghost-{uuid.uuid4().hex[:8]}"

        # Rectangle element
        ghost_rect = {
            "id": element_id,
            "type": "rectangle",
            "x": suggestion.position_hint.get("x", 400),
            "y": suggestion.position_hint.get("y", 220),
            "width": 150,
            "height": 80,
            "angle": 0,
            "strokeColor": "#0066cc",
            "backgroundColor": "#e7f3ff",
            "fillStyle": "hachure",
            "strokeWidth": 2,
            "strokeStyle": "dashed",
            "roughness": 1,
            "opacity": 60,
            "groupIds": [],
            "roundness": {"type": 3},
            "seed": 12345,
            "version": 1,
            "versionNonce": 1,
            "isDeleted": False,
            "boundElements": [{"type": "text", "id": f"{element_id}-text"}],
            "updated": 1,
            "link": None,
            "locked": False
        }

        # Text label
        ghost_text = {
            "id": f"{element_id}-text",
            "type": "text",
            "x": suggestion.position_hint.get("x", 400) + 10,
            "y": suggestion.position_hint.get("y", 220) + 25,
            "width": 130,
            "height": 30,
            "angle": 0,
            "strokeColor": "#0066cc",
            "backgroundColor": "transparent",
            "fillStyle": "hachure",
            "strokeWidth": 2,
            "strokeStyle": "solid",
            "roughness": 1,
            "opacity": 100,
            "groupIds": [],
            "roundness": None,
            "seed": 12346,
            "version": 1,
            "versionNonce": 1,
            "isDeleted": False,
            "boundElements": None,
            "updated": 1,
            "link": None,
            "locked": False,
            "text": f"{suggestion.component_name}?",
            "fontSize": 16,
            "fontFamily": 1,
            "textAlign": "center",
            "verticalAlign": "middle",
            "baseline": 24,
            "containerId": element_id,
            "originalText": f"{suggestion.component_name}?",
            "lineHeight": 1.25
        }

        ghost_elements.append(ghost_rect)
        ghost_elements.append(ghost_text)

    return ghost_elements


def _convert_agent_response_to_suggestion(agent_response: AgentResponse) -> SuggestionResponse:
    """
    Convert CanvasAwareHLDAgent's AgentResponse to API SuggestionResponse.

    Transforms ComponentSuggestion objects into simplified Node/Edge format
    and generates Excalidraw-ready ghost elements.
    """
    # Check if we have any suggestions
    if not agent_response.suggestions or len(agent_response.suggestions) == 0:
        return SuggestionResponse(
            suggestion=None,
            reasoning=agent_response.architecture_summary or "Architecture appears complete with current components",
            reference=None,
            excalidraw_elements=None,
            metadata=agent_response.metadata
        )

    # Take the first suggestion (highest priority)
    primary_suggestion = agent_response.suggestions[0]

    # Create simplified Node
    suggested_nodes = []
    suggested_edges = []

    node = Node(
        type=primary_suggestion.component_type,
        label=primary_suggestion.component_name,
        id=f"{primary_suggestion.component_type}-{uuid.uuid4().hex[:8]}"
    )
    suggested_nodes.append(node)

    # Create edges if connects_to is specified
    if primary_suggestion.connects_to:
        for target_id in primary_suggestion.connects_to:
            edge = Edge(
                **{
                    "from": target_id,
                    "to": node.id,
                    "type": "connects-to",
                    "label": None
                }
            )
            suggested_edges.append(edge)

    # Create Suggestion object
    suggestion = Suggestion(
        nodes=suggested_nodes,
        edges=suggested_edges
    )

    # Generate Excalidraw ghost elements
    excalidraw_elements = _create_ghost_excalidraw_elements(agent_response.suggestions[:2])  # Max 2 suggestions

    # Build metadata
    metadata = {
        **agent_response.metadata,
        "confidence": primary_suggestion.confidence,
        "priority": primary_suggestion.priority,
        "canvas_hash": agent_response.canvas_hash,
        "suggestion_count": len(agent_response.suggestions)
    }

    return SuggestionResponse(
        suggestion=suggestion,
        reasoning=primary_suggestion.reasoning,
        reference=None,  # Could be enhanced with reference links
        excalidraw_elements=excalidraw_elements,
        metadata=metadata
    )


@router.post(
    "/suggest",
    response_model=SuggestionResponse,
    summary="Get AI architectural suggestions",
    description="""
    ## 🎯 Get AI-Powered Architecture Suggestions

    Analyze canvas elements using the Canvas-Aware HLD Agent and receive
    intelligent architectural suggestions with ready-to-render ghost elements.

    ### 🔄 How It Works

    1. **Send Canvas State**: Submit current Excalidraw elements
    2. **Canvas Analysis**: Backend parses spatial layout, detects incomplete connections
    3. **AI Suggestions**: Multi-agent system suggests next components
    4. **Ghost Elements**: Returns Excalidraw-ready elements for preview

    ### 📊 Pattern Recognition

    - **Spatial Context**: Understands canvas layers (frontend, backend, data)
    - **Incomplete Flows**: Detects arrows pointing nowhere
    - **Best Practices**: Suggests caching, load balancing, queueing patterns

    ### ⚡ Response Format

    - **Suggestion**: Simplified nodes and edges
    - **Excalidraw Elements**: Ready-to-render ghost rectangles
    - **Reasoning**: AI explanation with confidence score
    - **Metadata**: Canvas hash, component count, priority

    ### 📖 OpenAPI 3.0 Specification

    This endpoint conforms to OpenAPI 3.0 standards with:
    - Structured request/response schemas
    - Comprehensive examples for all scenarios
    - Detailed error responses with status codes
    - Type-safe Pydantic models
    """,
    response_description="AI architectural suggestion with Excalidraw elements",
    responses={
        200: {
            "description": "Successful AI suggestion with components",
            "content": {
                "application/json": {
                    "examples": {
                        "cache_suggestion": {
                            "summary": "Cache Layer Suggestion",
                            "description": "AI suggests adding Redis cache between API and database",
                            "value": {
                                "suggestion": {
                                    "nodes": [
                                        {
                                            "type": "cache",
                                            "label": "Redis Cache",
                                            "id": "cache-redis-a1b2c3d4"
                                        }
                                    ],
                                    "edges": [
                                        {
                                            "from": "api-gateway-1",
                                            "to": "cache-redis-a1b2c3d4",
                                            "type": "reads-from",
                                            "label": "Cache queries"
                                        }
                                    ]
                                },
                                "reasoning": "Added Redis cache to improve database read performance and reduce query latency for frequently accessed data. This will help handle high traffic loads.",
                                "reference": None,
                                "excalidraw_elements": [
                                    {
                                        "id": "ghost-a1b2c3d4",
                                        "type": "rectangle",
                                        "x": 400,
                                        "y": 220,
                                        "width": 150,
                                        "height": 80,
                                        "strokeColor": "#0066cc",
                                        "strokeStyle": "dashed",
                                        "opacity": 60
                                    },
                                    {
                                        "id": "ghost-a1b2c3d4-text",
                                        "type": "text",
                                        "text": "Redis Cache?",
                                        "x": 410,
                                        "y": 245,
                                        "containerId": "ghost-a1b2c3d4"
                                    }
                                ],
                                "metadata": {
                                    "confidence": 0.87,
                                    "priority": "high",
                                    "canvas_hash": "f8e9a1b2c3d4e5f6",
                                    "component_count": 3,
                                    "suggestion_count": 1
                                }
                            }
                        },
                        "load_balancer_suggestion": {
                            "summary": "Load Balancer Suggestion",
                            "description": "AI suggests adding load balancer for high availability",
                            "value": {
                                "suggestion": {
                                    "nodes": [
                                        {
                                            "type": "api-gateway",
                                            "label": "Load Balancer",
                                            "id": "lb-nginx-x9y8z7"
                                        }
                                    ],
                                    "edges": [
                                        {
                                            "from": "client-1",
                                            "to": "lb-nginx-x9y8z7",
                                            "type": "requests"
                                        }
                                    ]
                                },
                                "reasoning": "Load balancer will distribute traffic across multiple backend servers, improving reliability and handling traffic spikes.",
                                "reference": None,
                                "excalidraw_elements": [
                                    {
                                        "id": "ghost-x9y8z7",
                                        "type": "rectangle",
                                        "x": 250,
                                        "y": 180,
                                        "width": 150,
                                        "height": 80,
                                        "strokeColor": "#0066cc",
                                        "strokeStyle": "dashed"
                                    }
                                ],
                                "metadata": {
                                    "confidence": 0.92,
                                    "priority": "high",
                                    "canvas_hash": "a1b2c3d4e5f6g7h8",
                                    "component_count": 2
                                }
                            }
                        },
                        "no_suggestion": {
                            "summary": "Architecture Complete",
                            "description": "No additional components needed - architecture is sufficient",
                            "value": {
                                "suggestion": None,
                                "reasoning": "Architecture appears complete with all necessary components for a production-ready distributed system. No additional suggestions at this time.",
                                "reference": None,
                                "excalidraw_elements": None,
                                "metadata": {
                                    "canvas_hash": "complete123",
                                    "component_count": 8,
                                    "suggestion_count": 0
                                }
                            }
                        }
                    }
                }
            }
        },
        413: {
            "description": "Request Entity Too Large - Canvas has too many elements",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Canvas too large. Maximum 100 elements allowed."
                    }
                }
            }
        },
        422: {
            "description": "Validation Error - Invalid request format",
            "content": {
                "application/json": {
                    "example": {
                        "error": "Validation Error",
                        "details": "Field 'canvas_elements' is required and must be an array"
                    }
                }
            }
        },
        500: {
            "description": "Internal Server Error - Analysis failed",
            "content": {
                "application/json": {
                    "example": {
                        "suggestion": None,
                        "reasoning": "Unable to process request due to internal error",
                        "reference": None,
                        "excalidraw_elements": None,
                        "metadata": {
                            "error": "LLM timeout or parsing failure"
                        }
                    }
                }
            }
        }
    },
    tags=["suggestions"],
    operation_id="getSuggestion",
    openapi_extra={
        "x-code-samples": [
            {
                "lang": "JavaScript",
                "source": """
const response = await fetch('http://localhost:8000/api/v1/suggest', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    canvas_elements: [
      { id: '1', type: 'rectangle', text: 'API Gateway', x: 100, y: 100 },
      { id: '2', type: 'rectangle', text: 'Database', x: 300, y: 100 }
    ],
    context: { design_type: 'microservices' }
  })
});
const data = await response.json();
console.log(data.suggestion);
                """
            },
            {
                "lang": "Python",
                "source": """
import requests

response = requests.post(
    'http://localhost:8000/api/v1/suggest',
    json={
        'canvas_elements': [
            {'id': '1', 'type': 'rectangle', 'text': 'API Gateway', 'x': 100, 'y': 100},
            {'id': '2', 'type': 'rectangle', 'text': 'Database', 'x': 300, 'y': 100}
        ],
        'context': {'design_type': 'microservices'}
    }
)
data = response.json()
print(data['suggestion'])
                """
            },
            {
                "lang": "cURL",
                "source": """
curl -X POST http://localhost:8000/api/v1/suggest \\
  -H "Content-Type: application/json" \\
  -d '{
    "canvas_elements": [
      {"id": "1", "type": "rectangle", "text": "API Gateway", "x": 100, "y": 100}
    ],
    "context": {"design_type": "distributed-system"}
  }'
                """
            }
        ]
    }
)
async def suggest_architecture(request: CanvasRequest) -> SuggestionResponse:
    """
    Generate AI suggestions using Canvas-Aware HLD Agent.

    This endpoint:
    1. Validates input using Pydantic models
    2. Converts canvas elements to Excalidraw format
    3. Saves to temp file for parser
    4. Runs Canvas-Aware HLD Agent analysis
    5. Returns suggestions with Excalidraw ghost elements
    """
    request_id = str(uuid.uuid4())
    temp_file_path = None

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

        # Validate payload size
        if len(request.canvas_elements) > 100:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Canvas too large. Maximum 100 elements allowed."
            )

        # Convert to Excalidraw canvas format
        excalidraw_canvas = _convert_to_excalidraw_canvas(request.canvas_elements)

        # Save to temporary file (CanvasAwareHLDAgent expects file path)
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.excalidraw',
            delete=False,
            encoding='utf-8'
        ) as temp_file:
            json.dump(excalidraw_canvas, temp_file, indent=2)
            temp_file_path = temp_file.name

        logger.info(f"Saved canvas to temp file: {temp_file_path}")

        # Extract context for agent
        context_str = ""
        if request.context:
            design_type = request.context.get("design_type", "")
            if design_type:
                context_str = f"{design_type} system architecture"
            else:
                context_str = "distributed system architecture"
        else:
            context_str = "system architecture design"

        # Analyze using Canvas-Aware HLD Agent
        logger.info(f"Analyzing canvas with context: {context_str}")
        agent_response = canvas_agent.analyze_canvas(temp_file_path, context_str)

        # Convert to API response format
        suggestion_response = _convert_agent_response_to_suggestion(agent_response)

        # Log successful response
        log_llm_response(
            logger,
            response=f"Suggestions: {len(agent_response.suggestions)}",
            valid=True,
            error=None
        )

        logger.info(f"Successfully generated {len(agent_response.suggestions)} suggestions")

        return suggestion_response

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        # Log error and return safe fallback
        error_msg = f"Internal error processing suggestion request: {str(e)}"
        logger.error(error_msg, exc_info=True)

        log_llm_response(
            logger,
            response="",
            valid=False,
            error=error_msg
        )

        # Return safe fallback
        return SuggestionResponse(
            suggestion=None,
            reasoning="Unable to process request due to internal error",
            reference=None,
            excalidraw_elements=None,
            metadata={"error": str(e)}
        )

    finally:
        # Clean up temp file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                logger.debug(f"Cleaned up temp file: {temp_file_path}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup temp file: {cleanup_error}")


@router.get(
    "/health",
    summary="Suggestion Service Health Check",
    description="Verify that the Canvas-Aware HLD Agent is operational",
    tags=["health"]
)
async def suggestion_health():
    """Health check for the AI suggestion service."""
    try:
        return {
            "status": "healthy",
            "service": "canvas_aware_suggestion_router",
            "agent_type": "CanvasAwareHLDAgent"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "canvas_aware_suggestion_router",
            "error": str(e)
        }
