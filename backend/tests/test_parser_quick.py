#!/usr/bin/env python3
"""
Quick test script for parser without pytest framework
"""
import sys
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from hld_agent.parsers.excalidraw_parser import ExcalidrawParser
from hld_agent.utils.component_classifier import ComponentClassifier


def test_component_classifier():
    """Test component classifier"""
    print("\n🧪 Testing ComponentClassifier...")

    classifier = ComponentClassifier()

    # Test cases
    tests = [
        ("user", "client"),
        ("API Gateway", "api-gateway"),
        ("redis", "cache"),
        ("postgres", "database"),
        ("service", "service"),
        ("load balancer", "load-balancer"),
    ]

    passed = 0
    for input_name, expected_type in tests:
        result = classifier.classify(input_name)
        status = "✅" if result == expected_type else "❌"
        print(f"  {status} '{input_name}' -> '{result}' (expected: '{expected_type}')")
        if result == expected_type:
            passed += 1

    print(f"\n  Result: {passed}/{len(tests)} tests passed\n")
    return passed == len(tests)


def test_excalidraw_parser():
    """Test Excalidraw parser with temp.excalidraw"""
    print("🧪 Testing ExcalidrawParser...")

    parser = ExcalidrawParser()

    # Load sample canvas
    canvas_path = Path(__file__).parent.parent / "temp.excalidraw"

    if not canvas_path.exists():
        print(f"  ❌ Sample canvas not found at: {canvas_path}")
        return False

    print(f"  📄 Loading canvas from: {canvas_path}")

    graph = parser.parse_from_file(str(canvas_path))

    print(f"\n  📊 Parse Results:")
    print(f"    Components: {len(graph.components)}")
    print(f"    Connections: {len(graph.connections)}")
    print(f"    Layers: {list(graph.layers.keys())}")

    print(f"\n  🏗️  Components:")
    for comp in graph.components:
        print(f"    - {comp.name} (type: {comp.type}, pos: x={comp.position['x']:.0f}, y={comp.position['y']:.0f})")

    print(f"\n  🔗 Connections:")
    for conn in graph.connections:
        from_comp = graph.get_component_by_id(conn.from_component)
        to_comp = graph.get_component_by_id(conn.to_component) if conn.to_component else None

        from_name = from_comp.name if from_comp else "Unknown"
        to_name = to_comp.name if to_comp else "???"

        print(f"    - {from_name} → {to_name}")

    print(f"\n  📐 Layers:")
    for layer, comp_ids in graph.layers.items():
        comp_names = [graph.get_component_by_id(cid).name for cid in comp_ids]
        print(f"    - {layer}: {', '.join(comp_names)}")

    print(f"\n  📝 Sequence String:")
    sequence = graph.to_sequence_string()
    print(f"    {sequence}")

    print(f"\n  🔍 Incomplete Connections:")
    incomplete = graph.get_incomplete_connections()
    if incomplete:
        for conn in incomplete:
            from_comp = graph.get_component_by_id(conn.from_component)
            print(f"    - {from_comp.name if from_comp else 'Unknown'} → ???")
    else:
        print(f"    None")

    # Validation
    success = True
    if len(graph.components) < 3:
        print(f"\n  ❌ Expected at least 3 components, got {len(graph.components)}")
        success = False
    else:
        print(f"\n  ✅ Found {len(graph.components)} components")

    if len(graph.connections) < 2:
        print(f"  ❌ Expected at least 2 connections, got {len(graph.connections)}")
        success = False
    else:
        print(f"  ✅ Found {len(graph.connections)} connections")

    print()
    return success


def main():
    """Run all tests"""
    print("=" * 60)
    print("  HLD Agent Parser - Quick Test Suite")
    print("=" * 60)

    results = []

    # Test 1: Component Classifier
    results.append(("ComponentClassifier", test_component_classifier()))

    # Test 2: Excalidraw Parser
    results.append(("ExcalidrawParser", test_excalidraw_parser()))

    # Summary
    print("=" * 60)
    print("  Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {name}")

    print()
    print(f"  Total: {passed}/{total} test suites passed")
    print("=" * 60)

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
