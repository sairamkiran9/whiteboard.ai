"""
Pydantic models for AI System Design Copilot
Following CLAUDE.md strict ontology enforcement
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class NodeType(str, Enum):
    """
    Allowed node types for system architecture components.
    
    Following strict ontology as defined in CLAUDE.md to ensure
    consistent and predictable AI suggestions.
    """
    CLIENT = "client"
    WEBSERVER = "webserver"
    API_GATEWAY = "api-gateway"
    CACHE = "cache"
    DATABASE = "database"
    WORKER = "worker"
    QUEUE = "queue"
    STORAGE = "storage"


class EdgeType(str, Enum):
    """
    Allowed edge types for connections between system components.
    
    Defines the relationship semantics between nodes to enable
    accurate architectural analysis and suggestions.
    """
    REQUESTS = "requests"
    READS_FROM = "reads-from"  
    WRITES_TO = "writes-to"
    SENDS_MESSAGE = "sends-message"
    CONNECTS_TO = "connects-to"
    DEPENDS_ON = "depends-on"


class Node(BaseModel):
    """
    System design node representing a component in the architecture.
    
    Each node has a specific type from the allowed ontology and a
    human-readable label describing its purpose.
    """
    type: NodeType = Field(
        ..., 
        description="Node type from the strict ontology",
        example="database"
    )
    label: str = Field(
        ..., 
        min_length=1, 
        max_length=100, 
        description="Human-readable label describing the component",
        example="PostgreSQL Database"
    )
    id: Optional[str] = Field(
        None, 
        description="Unique identifier for the node",
        example="db-postgres-1"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "type": "database",
                "label": "PostgreSQL Database",
                "id": "db-postgres-1"
            }
        }
    
    @validator('label')
    def validate_label(cls, v):
        """Ensure label is not empty or whitespace only"""
        if not v.strip():
            raise ValueError("Label cannot be empty or whitespace only")
        return v.strip()


class Edge(BaseModel):
    """
    System design edge representing a connection between two components.
    
    Edges define relationships and data flow between nodes using
    semantic edge types from the allowed ontology.
    """
    from_node: str = Field(
        ..., 
        alias="from", 
        description="Source node ID",
        example="web-server-1"
    )
    to_node: str = Field(
        ..., 
        alias="to", 
        description="Target node ID",
        example="db-postgres-1"
    )
    type: EdgeType = Field(
        ..., 
        description="Edge type defining the relationship semantics",
        example="reads-from"
    )
    label: Optional[str] = Field(
        None, 
        max_length=100, 
        description="Optional descriptive label for the connection",
        example="User data queries"
    )
    
    class Config:
        allow_population_by_field_name = True
        schema_extra = {
            "example": {
                "from": "web-server-1",
                "to": "db-postgres-1", 
                "type": "reads-from",
                "label": "User data queries"
            }
        }


class Suggestion(BaseModel):
    """AI suggestion containing nodes and edges"""
    nodes: List[Node] = Field(default_factory=list, description="Suggested nodes to add")
    edges: List[Edge] = Field(default_factory=list, description="Suggested edges to add")
    
    @validator('nodes')
    def validate_nodes_limit(cls, v):
        """Limit suggestion to maximum 2 nodes as per CLAUDE.md"""
        if len(v) > 2:
            raise ValueError("Maximum 2 nodes allowed per suggestion")
        return v
    
    @validator('edges')
    def validate_edges_limit(cls, v):
        """Limit suggestion to maximum 2 edges as per CLAUDE.md"""
        if len(v) > 2:
            raise ValueError("Maximum 2 edges allowed per suggestion")
        return v


class SuggestionResponse(BaseModel):
    """
    Complete AI response containing architectural suggestions and reasoning.

    This is the main response format following CLAUDE.md specifications,
    providing structured suggestions with explanations and references.
    """
    suggestion: Optional[Suggestion] = Field(
        None,
        description="AI-generated architectural suggestion, or null if no suggestion is appropriate"
    )
    reasoning: str = Field(
        ...,
        description="Human-readable explanation for why this suggestion was made",
        example="Added a cache layer to improve database read performance and reduce latency for frequently accessed data."
    )
    reference: Optional[str] = Field(
        None,
        description="URL to documentation or best practices related to this suggestion",
        example="https://aws.amazon.com/caching/"
    )
    excalidraw_elements: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Ready-to-render Excalidraw elements for canvas integration (rectangles with positions and ghost styling)",
        example=[{
            "type": "rectangle",
            "id": "ghost-cache-1",
            "x": 400,
            "y": 220,
            "width": 150,
            "height": 80,
            "strokeColor": "#0066cc",
            "strokeStyle": "dashed",
            "opacity": 60,
            "label": {"text": "Redis Cache?"}
        }]
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional metadata about the analysis (component count, confidence, priority)",
        example={
            "confidence": 0.85,
            "priority": "high",
            "canvas_hash": "abc123",
            "component_count": 5
        }
    )
    
    class Config:
        schema_extra = {
            "example": {
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
                "reasoning": "Added a cache layer to improve database read performance and reduce latency for frequently accessed data.",
                "reference": "https://aws.amazon.com/caching/",
                "excalidraw_elements": [
                    {
                        "type": "rectangle",
                        "id": "ghost-redis-cache-1",
                        "x": 400,
                        "y": 220,
                        "width": 150,
                        "height": 80,
                        "strokeColor": "#0066cc",
                        "strokeStyle": "dashed",
                        "opacity": 60,
                        "label": {"text": "Redis Cache?"}
                    }
                ],
                "metadata": {
                    "confidence": 0.85,
                    "priority": "high",
                    "canvas_hash": "a1b2c3d4",
                    "component_count": 5
                }
            }
        }
    
    @validator('reasoning')
    def validate_reasoning(cls, v):
        """Ensure reasoning is provided"""
        if not v.strip():
            raise ValueError("Reasoning cannot be empty")
        return v.strip()


class CanvasRequest(BaseModel):
    """
    Request payload containing canvas state for AI analysis.
    
    Includes the current state of the drawing canvas along with
    recent changes and contextual information for better suggestions.
    """
    canvas_elements: List[Dict[str, Any]] = Field(
        ..., 
        description="Array of canvas elements (shapes, text, arrows) from the drawing tool",
        example=[
            {
                "id": "rect-1",
                "type": "rectangle", 
                "text": "Web Server",
                "x": 100,
                "y": 100,
                "width": 120,
                "height": 60
            },
            {
                "id": "rect-2",
                "type": "rectangle",
                "text": "Database", 
                "x": 300,
                "y": 200,
                "width": 100,
                "height": 50
            }
        ]
    )
    recent_changes: Optional[List[Dict[str, Any]]] = Field(
        None, 
        description="Recent changes made to the canvas for incremental analysis",
        example=[
            {
                "action": "add",
                "element_id": "rect-2", 
                "timestamp": "2024-01-01T10:30:00Z"
            }
        ]
    )
    context: Optional[Dict[str, Any]] = Field(
        None, 
        description="Additional context information (user preferences, session data, etc.)",
        example={
            "user_id": "demo-user",
            "session_id": "session-123",
            "design_type": "microservices"
        }
    )
    
    class Config:
        schema_extra = {
            "example": {
                "canvas_elements": [
                    {
                        "id": "client-1",
                        "type": "rectangle",
                        "text": "Mobile App",
                        "x": 50,
                        "y": 50,
                        "width": 100,
                        "height": 60
                    },
                    {
                        "id": "server-1", 
                        "type": "rectangle",
                        "text": "API Server",
                        "x": 200,
                        "y": 50,
                        "width": 100,
                        "height": 60
                    }
                ],
                "recent_changes": [
                    {
                        "action": "add",
                        "element_id": "server-1",
                        "timestamp": "2024-01-01T10:30:00Z"
                    }
                ],
                "context": {
                    "user_id": "demo-user",
                    "session_id": "demo-session-123"
                }
            }
        }


class ErrorResponse(BaseModel):
    """Standardized error response"""
    error: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Additional error details")
    request_id: Optional[str] = Field(None, description="Request ID for debugging")