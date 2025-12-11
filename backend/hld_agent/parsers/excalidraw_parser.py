"""
Excalidraw JSON Parser

Parses Excalidraw canvas JSON and extracts architectural components and connections.
"""
from typing import Dict, List, Any, Optional
import logging

from ..models import (
    ExcalidrawCanvas,
    ComponentNode,
    ConnectionEdge,
    ArchitectureGraph,
)
from ..utils.component_classifier import ComponentClassifier

logger = logging.getLogger(__name__)


class ExcalidrawParser:
    """Parse Excalidraw JSON into ArchitectureGraph"""

    def __init__(self):
        self.classifier = ComponentClassifier()

    def parse(self, canvas_data: Dict[str, Any]) -> ArchitectureGraph:
        """
        Parse Excalidraw canvas JSON into structured ArchitectureGraph

        Args:
            canvas_data: Raw Excalidraw JSON dict

        Returns:
            ArchitectureGraph with components and connections
        """
        try:
            # Validate input
            canvas = ExcalidrawCanvas(**canvas_data)

            # Extract components and text labels
            components = self._extract_components(canvas.elements)

            # Extract connections (arrows)
            connections = self._extract_connections(canvas.elements, components)

            # Detect spatial layers
            layers = self._detect_layers(components)

            # Build graph
            graph = ArchitectureGraph(
                components=list(components.values()),
                connections=connections,
                layers=layers,
            )

            logger.info(
                f"Parsed Excalidraw canvas: {len(graph.components)} components, "
                f"{len(graph.connections)} connections"
            )

            return graph

        except Exception as e:
            logger.error(f"Failed to parse Excalidraw canvas: {e}", exc_info=True)
            # Return empty graph on failure (fail-safe)
            return ArchitectureGraph()

    def _extract_components(self, elements: List[Dict[str, Any]]) -> Dict[str, ComponentNode]:
        """
        Extract components from Excalidraw elements

        Strategy:
        1. Find all rectangles/ellipses/diamonds (these are components)
        2. Find text elements with containerId (these are labels)
        3. Match labels to shapes
        """
        components: Dict[str, ComponentNode] = {}
        text_labels: Dict[str, str] = {}  # containerId -> text

        # First pass: collect text labels
        for elem in elements:
            if elem.get("type") == "text" and elem.get("containerId"):
                container_id = elem["containerId"]
                text = elem.get("text", "").strip()
                # Normalize text: replace newlines with spaces
                text = " ".join(text.split())
                if text:
                    text_labels[container_id] = text

        # Second pass: create components from shapes
        for elem in elements:
            elem_type = elem.get("type")
            elem_id = elem.get("id")

            # Check if this is a shape (potential component)
            if elem_type in ["rectangle", "ellipse", "diamond"] and not elem.get("isDeleted", False):
                # Get label from text
                label = text_labels.get(elem_id, f"Component-{elem_id[:8]}")

                # Classify component type
                component_type = self.classifier.classify(label)

                # Create component
                component = ComponentNode(
                    id=elem_id,
                    name=label,
                    type=component_type,
                    position={
                        "x": elem.get("x", 0),
                        "y": elem.get("y", 0),
                    },
                    metadata={
                        "width": elem.get("width", 0),
                        "height": elem.get("height", 0),
                        "shape_type": elem_type,
                    },
                )

                components[elem_id] = component

        logger.debug(f"Extracted {len(components)} components: {[c.name for c in components.values()]}")

        return components

    def _extract_connections(
        self, elements: List[Dict[str, Any]], components: Dict[str, ComponentNode]
    ) -> List[ConnectionEdge]:
        """
        Extract connections (arrows) between components

        Strategy:
        1. Find all arrow elements
        2. Check startBinding and endBinding
        3. Create ConnectionEdge for each arrow
        """
        connections: List[ConnectionEdge] = []

        for elem in elements:
            if elem.get("type") == "arrow" and not elem.get("isDeleted", False):
                elem_id = elem.get("id")
                start_binding = elem.get("startBinding")
                end_binding = elem.get("endBinding")

                # Extract source component
                from_component_id = None
                if start_binding and "elementId" in start_binding:
                    from_component_id = start_binding["elementId"]

                # Extract target component (may be None if arrow is incomplete)
                to_component_id = None
                if end_binding and "elementId" in end_binding:
                    to_component_id = end_binding["elementId"]

                # Only create connection if source exists in our components
                if from_component_id and from_component_id in components:
                    # Check if target exists (could be None for incomplete arrows)
                    if to_component_id and to_component_id not in components:
                        to_component_id = None  # Target not a component, mark incomplete

                    connection = ConnectionEdge(
                        id=elem_id,
                        from_component=from_component_id,
                        to_component=to_component_id,
                        connection_type="data-flow",
                        is_bidirectional=False,  # Could detect based on arrow heads
                    )

                    connections.append(connection)

        logger.debug(
            f"Extracted {len(connections)} connections, "
            f"{len([c for c in connections if c.to_component is None])} incomplete"
        )

        return connections

    def _detect_layers(self, components: Dict[str, ComponentNode]) -> Dict[str, List[str]]:
        """
        Detect architectural layers based on spatial positioning

        Strategy: Use x-coordinates to infer layers
        - x < 200: frontend/client layer
        - 200 <= x < 400: middle/backend layer
        - x >= 400: data/storage layer
        """
        layers: Dict[str, List[str]] = {
            "frontend": [],
            "backend": [],
            "data": [],
        }

        for comp_id, comp in components.items():
            x = comp.position["x"]

            if x < 200:
                layers["frontend"].append(comp_id)
            elif 200 <= x < 400:
                layers["backend"].append(comp_id)
            else:
                layers["data"].append(comp_id)

        # Remove empty layers
        layers = {k: v for k, v in layers.items() if v}

        logger.debug(f"Detected layers: {[(k, len(v)) for k, v in layers.items()]}")

        return layers

    def parse_from_file(self, file_path: str) -> ArchitectureGraph:
        """
        Parse Excalidraw file from disk

        Args:
            file_path: Path to .excalidraw JSON file

        Returns:
            ArchitectureGraph
        """
        import json

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                canvas_data = json.load(f)
            return self.parse(canvas_data)
        except Exception as e:
            logger.error(f"Failed to read Excalidraw file {file_path}: {e}")
            return ArchitectureGraph()
