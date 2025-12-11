"""
Tests for ExcalidrawParser
"""
import pytest
import json
import os
from pathlib import Path

from hld_agent.parsers.excalidraw_parser import ExcalidrawParser
from hld_agent.models import ArchitectureGraph, ComponentNode, ConnectionEdge


class TestExcalidrawParser:
    """Test Excalidraw canvas parsing"""

    @pytest.fixture
    def parser(self):
        """Create parser instance"""
        return ExcalidrawParser()

    @pytest.fixture
    def sample_canvas_path(self):
        """Path to sample canvas file"""
        return Path(__file__).parent / "fixtures" / "sample_canvases" / "simple_three_tier.excalidraw"

    @pytest.fixture
    def sample_canvas_data(self, sample_canvas_path):
        """Load sample canvas data"""
        with open(sample_canvas_path, "r") as f:
            return json.load(f)

    def test_parse_simple_canvas(self, parser, sample_canvas_data):
        """Test parsing simple three-tier architecture"""
        graph = parser.parse(sample_canvas_data)

        # Should have 3 components
        assert len(graph.components) == 3

        # Check component names
        component_names = graph.get_component_names()
        assert "user" in component_names
        assert "API\nGateway" in component_names or "API Gateway" in [c.name for c in graph.components]
        assert "service" in component_names

    def test_parse_components_have_types(self, parser, sample_canvas_data):
        """Test that components are classified into types"""
        graph = parser.parse(sample_canvas_data)

        # All components should have a type
        for comp in graph.components:
            assert comp.type is not None
            assert comp.type != ""

        # Check specific types
        component_types = {comp.name: comp.type for comp in graph.components}
        assert component_types.get("user") == "client"
        # API Gateway might be "API\nGateway" due to newline
        assert any(comp.type == "api-gateway" for comp in graph.components)

    def test_parse_connections(self, parser, sample_canvas_data):
        """Test that connections are extracted"""
        graph = parser.parse(sample_canvas_data)

        # Should have at least 2 connections based on temp.excalidraw
        assert len(graph.connections) >= 2

        # Check connections have from_component
        for conn in graph.connections:
            assert conn.from_component is not None

    def test_parse_incomplete_connections(self, parser, sample_canvas_data):
        """Test detection of incomplete arrows"""
        graph = parser.parse(sample_canvas_data)

        incomplete = graph.get_incomplete_connections()

        # temp.excalidraw has arrows, some may be incomplete
        # Just verify the method works
        assert isinstance(incomplete, list)

    def test_parse_spatial_layers(self, parser, sample_canvas_data):
        """Test spatial layer detection"""
        graph = parser.parse(sample_canvas_data)

        # Should detect some layers
        assert len(graph.layers) > 0

        # Layers should be frontend, backend, or data
        for layer_name in graph.layers.keys():
            assert layer_name in ["frontend", "backend", "data"]

    def test_parse_positions(self, parser, sample_canvas_data):
        """Test that component positions are captured"""
        graph = parser.parse(sample_canvas_data)

        for comp in graph.components:
            assert "x" in comp.position
            assert "y" in comp.position
            assert isinstance(comp.position["x"], (int, float))
            assert isinstance(comp.position["y"], (int, float))

    def test_to_sequence_string(self, parser, sample_canvas_data):
        """Test conversion to sequence string for existing agent"""
        graph = parser.parse(sample_canvas_data)

        sequence = graph.to_sequence_string()

        # Should be a string
        assert isinstance(sequence, str)

        # Should contain component names connected by ->
        assert "->" in sequence or len(graph.components) <= 1

        # Should include component names
        for comp in graph.components:
            # Component name should appear in sequence
            assert comp.name in sequence

    def test_parse_from_file(self, parser, sample_canvas_path):
        """Test parsing directly from file"""
        graph = parser.parse_from_file(str(sample_canvas_path))

        # Should successfully parse
        assert len(graph.components) >= 3

    def test_parse_empty_canvas(self, parser):
        """Test parsing empty canvas"""
        empty_canvas = {
            "type": "excalidraw",
            "version": 2,
            "elements": [],
            "appState": {},
            "files": {}
        }

        graph = parser.parse(empty_canvas)

        # Should return empty graph
        assert len(graph.components) == 0
        assert len(graph.connections) == 0

    def test_parse_invalid_data_returns_empty(self, parser):
        """Test that invalid data returns empty graph instead of crashing"""
        invalid_data = {"invalid": "data"}

        graph = parser.parse(invalid_data)

        # Should return empty graph (fail-safe)
        assert isinstance(graph, ArchitectureGraph)
        assert len(graph.components) == 0

    def test_get_component_by_id(self, parser, sample_canvas_data):
        """Test finding component by ID"""
        graph = parser.parse(sample_canvas_data)

        if graph.components:
            first_comp = graph.components[0]
            found = graph.get_component_by_id(first_comp.id)
            assert found is not None
            assert found.id == first_comp.id

    def test_get_outgoing_connections(self, parser, sample_canvas_data):
        """Test getting outgoing connections for a component"""
        graph = parser.parse(sample_canvas_data)

        if graph.components and graph.connections:
            # Get first component that has outgoing connections
            for comp in graph.components:
                outgoing = graph.get_outgoing_connections(comp.id)
                if outgoing:
                    # Verify all connections start from this component
                    for conn in outgoing:
                        assert conn.from_component == comp.id
                    break

    def test_get_incoming_connections(self, parser, sample_canvas_data):
        """Test getting incoming connections for a component"""
        graph = parser.parse(sample_canvas_data)

        if graph.components and graph.connections:
            # Get first component that has incoming connections
            for comp in graph.components:
                incoming = graph.get_incoming_connections(comp.id)
                if incoming:
                    # Verify all connections end at this component
                    for conn in incoming:
                        assert conn.to_component == comp.id
                    break

    def test_metadata_captured(self, parser, sample_canvas_data):
        """Test that metadata like width, height is captured"""
        graph = parser.parse(sample_canvas_data)

        for comp in graph.components:
            assert "width" in comp.metadata
            assert "height" in comp.metadata
            assert "shape_type" in comp.metadata
