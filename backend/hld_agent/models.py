"""
Data models for Excalidraw HLD Agent
"""
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


# ==================== Excalidraw Models ====================

class ExcalidrawElement(BaseModel):
    """Base Excalidraw element"""
    id: str
    type: str
    x: float
    y: float
    width: Optional[float] = None
    height: Optional[float] = None
    angle: float = 0
    strokeColor: str = "#1e1e1e"
    backgroundColor: str = "transparent"
    boundElements: Optional[List[Dict[str, Any]]] = None
    isDeleted: bool = False


class ExcalidrawText(ExcalidrawElement):
    """Text element in Excalidraw"""
    text: str
    fontSize: int = 20
    fontFamily: int = 1
    textAlign: str = "left"
    containerId: Optional[str] = None  # If text is bound to a shape


class ExcalidrawRectangle(ExcalidrawElement):
    """Rectangle/Shape element"""
    type: Literal["rectangle", "ellipse", "diamond"] = "rectangle"


class ExcalidrawArrow(ExcalidrawElement):
    """Arrow/Connection element"""
    type: Literal["arrow"] = "arrow"
    points: List[List[float]]
    startBinding: Optional[Dict[str, Any]] = None
    endBinding: Optional[Dict[str, Any]] = None
    startArrowhead: Optional[str] = None
    endArrowhead: Optional[str] = "arrow"


class ExcalidrawCanvas(BaseModel):
    """Complete Excalidraw canvas"""
    type: str = "excalidraw"
    version: int
    elements: List[Dict[str, Any]]  # Raw elements
    appState: Dict[str, Any]
    files: Dict[str, Any] = {}


# ==================== Architecture Models ====================

class ComponentNode(BaseModel):
    """Represents an architectural component"""
    id: str = Field(..., description="Unique identifier from Excalidraw")
    name: str = Field(..., description="Component name (e.g., 'API Gateway', 'Database')")
    type: str = Field(..., description="Component type (e.g., 'api-gateway', 'database', 'cache')")
    position: Dict[str, float] = Field(..., description="X, Y coordinates")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    def __hash__(self):
        return hash(self.id)


class ConnectionEdge(BaseModel):
    """Represents a connection between components"""
    id: str = Field(..., description="Arrow ID from Excalidraw")
    from_component: str = Field(..., description="Source component ID")
    to_component: Optional[str] = Field(None, description="Target component ID (None if incomplete)")
    connection_type: str = Field(default="data-flow", description="Type of connection")
    is_bidirectional: bool = Field(default=False, description="Is this a two-way connection")

    def __hash__(self):
        return hash(self.id)


class ArchitectureGraph(BaseModel):
    """Structured representation of the architecture"""
    components: List[ComponentNode] = Field(default_factory=list)
    connections: List[ConnectionEdge] = Field(default_factory=list)
    layers: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Components grouped by layer (frontend, backend, data)"
    )
    patterns_detected: List[str] = Field(
        default_factory=list,
        description="Detected architecture patterns"
    )

    def get_component_by_id(self, component_id: str) -> Optional[ComponentNode]:
        """Find component by ID"""
        for comp in self.components:
            if comp.id == component_id:
                return comp
        return None

    def get_component_names(self) -> List[str]:
        """Get all component names"""
        return [comp.name for comp in self.components]

    def get_incomplete_connections(self) -> List[ConnectionEdge]:
        """Find arrows pointing to nowhere"""
        return [conn for conn in self.connections if conn.to_component is None]

    def get_outgoing_connections(self, component_id: str) -> List[ConnectionEdge]:
        """Get all connections going out from a component"""
        return [conn for conn in self.connections if conn.from_component == component_id]

    def get_incoming_connections(self, component_id: str) -> List[ConnectionEdge]:
        """Get all connections coming into a component"""
        return [conn for conn in self.connections if conn.to_component == component_id]

    def to_sequence_string(self) -> str:
        """Convert graph to sequence string for existing HLD agent"""
        if not self.components:
            return "user request"

        # Build sequence from connections
        sequence_parts = []
        visited = set()

        # Find starting component (no incoming connections)
        start_components = [
            comp for comp in self.components
            if not self.get_incoming_connections(comp.id)
        ]

        if not start_components and self.components:
            # If no clear start, use first component
            start_components = [self.components[0]]

        # Build sequence by following connections
        for start in start_components:
            current = start
            visited.add(current.id)
            sequence_parts.append(current.name)

            # Follow outgoing connections
            outgoing = self.get_outgoing_connections(current.id)
            while outgoing:
                # Take first unvisited connection
                next_conn = None
                for conn in outgoing:
                    if conn.to_component and conn.to_component not in visited:
                        next_conn = conn
                        break

                if not next_conn:
                    break

                next_comp = self.get_component_by_id(next_conn.to_component)
                if next_comp:
                    visited.add(next_comp.id)
                    sequence_parts.append(next_comp.name)
                    outgoing = self.get_outgoing_connections(next_comp.id)
                else:
                    break

        # Add any unvisited components
        for comp in self.components:
            if comp.id not in visited:
                sequence_parts.append(comp.name)

        return " -> ".join(sequence_parts) if sequence_parts else "user request"


# ==================== Suggestion Models (for existing agent integration) ====================

class ComponentSuggestion(BaseModel):
    """A suggested component to add to the architecture"""
    component_name: str = Field(..., description="Name of suggested component")
    component_type: str = Field(..., description="Type classification")
    reasoning: str = Field(..., description="Why this component is suggested")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0-1")
    priority: Literal["high", "medium", "low"] = Field(..., description="Priority level")
    position_hint: Optional[Dict[str, float]] = Field(
        None,
        description="Suggested X, Y position on canvas"
    )
    connects_to: List[str] = Field(
        default_factory=list,
        description="IDs of components this should connect to"
    )
    trade_offs: Optional[str] = Field(None, description="Trade-offs of adding this component")


class ArchitectureIssue(BaseModel):
    """An identified issue in the current architecture"""
    issue_type: Literal["security", "scalability", "reliability", "performance", "best-practice"] = Field(
        ..., description="Category of issue"
    )
    severity: Literal["critical", "warning", "info"] = Field(..., description="Severity level")
    description: str = Field(..., description="What the issue is")
    affected_components: List[str] = Field(
        default_factory=list,
        description="Component IDs affected by this issue"
    )
    recommendation: str = Field(..., description="How to fix it")


class AgentResponse(BaseModel):
    """Complete response from the HLD Agent"""
    canvas_hash: str = Field(..., description="Hash of canvas state for change detection")
    architecture_summary: str = Field(..., description="Natural language summary of current architecture")
    current_sequence: str = Field(..., description="Current architecture as sequence string")
    suggestions: List[ComponentSuggestion] = Field(
        default_factory=list,
        description="Suggested next components"
    )
    issues: List[ArchitectureIssue] = Field(
        default_factory=list,
        description="Identified problems"
    )
    next_steps: List[str] = Field(
        default_factory=list,
        description="Recommended next steps in plain English"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context (component count, etc.)"
    )
