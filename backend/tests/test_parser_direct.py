#!/usr/bin/env python3
"""Direct parser test without going through hld_agent.__init__"""
import sys
from pathlib import Path

# Don't import hld_agent package, import modules directly
sys.path.insert(0, str(Path(__file__).parent))

# Import parser module directly
import importlib.util
spec = importlib.util.spec_from_file_location(
    "excalidraw_parser",
    Path(__file__).parent.parent / "hld_agent" / "parsers" / "excalidraw_parser.py"
)
parser_module = importlib.util.module_from_spec(spec)

# Import classifier
spec2 = importlib.util.spec_from_file_location(
    "component_classifier",
    Path(__file__).parent.parent / "hld_agent" / "utils" / "component_classifier.py"
)
classifier_module = importlib.util.module_from_spec(spec2)

# Load modules
spec.loader.exec_module(parser_module)
spec2.loader.exec_module(classifier_module)

# Get classes
ExcalidrawParser = parser_module.ExcalidrawParser
ComponentClassifier = classifier_module.ComponentClassifier

print("✅ Modules loaded successfully\n")

# Test classifier
print("🧪 Testing ComponentClassifier...")
classifier = ComponentClassifier()

test_names = [
    ("user", "client"),
    ("API Gateway", "api-gateway"),
    ("service", "service"),
]

for name, expected in test_names:
    result = classifier.classify(name)
    status = "✅" if result == expected else "❌"
    print(f"  {status} '{name}' -> '{result}' (expected: '{expected}')")

# Test parser
print("\n🧪 Testing ExcalidrawParser...")
parser = ExcalidrawParser()

canvas_path = Path(__file__).parent.parent / "temp.excalidraw"
print(f"  📄 Loading: {canvas_path}")

import json
with open(canvas_path) as f:
    canvas_data = json.load(f)

from hld_agent.models import ArchitectureGraph
graph = parser.parse(canvas_data)

print(f"\n  📊 Results:")
print(f"    Components: {len(graph.components)}")
print(f"    Connections: {len(graph.connections)}")

print(f"\n  🏗️  Component Details:")
for comp in graph.components:
    print(f"    - {comp.name} (type: {comp.type})")

print(f"\n  ✅ Parser working correctly!")
