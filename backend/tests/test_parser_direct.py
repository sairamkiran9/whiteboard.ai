#!/usr/bin/env python3
"""Direct parser test using proper imports"""
import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import using proper package imports
from hld_agent.parsers.excalidraw_parser import ExcalidrawParser
from hld_agent.utils.component_classifier import ComponentClassifier

def test_component_classifier_direct():
    """Test component classifier directly"""
    classifier = ComponentClassifier()
    
    test_cases = [
        ("user", "client"),
        ("API Gateway", "api-gateway"),
        ("service", "service"),
    ]
    
    for name, expected in test_cases:
        result = classifier.classify(name)
        assert result == expected, f"Expected '{expected}' but got '{result}' for '{name}'"

def test_excalidraw_parser_direct():
    """Test excalidraw parser directly"""
    import json
    from hld_agent.models import ArchitectureGraph
    
    parser = ExcalidrawParser()
    canvas_path = Path(__file__).parent.parent.parent / "temp.excalidraw"
    
    with open(canvas_path) as f:
        canvas_data = json.load(f)
    
    graph = parser.parse(canvas_data)
    
    assert isinstance(graph, ArchitectureGraph)
    assert len(graph.components) > 0
    print(f"Found {len(graph.components)} components and {len(graph.connections)} connections")
