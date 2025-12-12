#!/usr/bin/env python3
"""
HLD Agent with Excalidraw Canvas Integration

This script integrates the Excalidraw parser with the existing HLD agent
to provide canvas-aware architecture suggestions.
"""
import sys
import json
import hashlib
from pathlib import Path
from typing import Dict, Any

# Add paths
sys.path.insert(0, str(Path(__file__).parent))

from hld_agent.parsers.excalidraw_parser import ExcalidrawParser
from hld_agent.models import ArchitectureGraph, AgentResponse, ComponentSuggestion
from hld_agent.config.settings import load_config

# Import existing HLD agent components
from pydantic import BaseModel, Field
from typing import List, Optional
import os
from dotenv import load_dotenv
from groq import Groq
import instructor
import logging

# Load environment
load_dotenv()

# Configure logger
logger = logging.getLogger(__name__)

# ==================== Structured Output Models (using Instructor) ====================

class ArchitectureSuggestion(BaseModel):
    """Structured output for architecture suggestion using Instructor"""
    next_component: Optional[str] = Field(None, description="The next component to add, or null if architecture is complete")
    explanation: str = Field(..., description="Why this component is needed")
    reasoning: str = Field(..., description="Detailed architectural reasoning")
    is_complete: bool = Field(False, description="Whether the architecture is sufficient")


# ==================== Prompt Constants ====================

SYSTEM_MESSAGE = """You are a distributed systems architect that must return a structured ArchitectureSuggestion object. Follow these constraints:
- Always base analysis only on the provided graph summary and context
- Never invent component names that cannot reasonably exist in a distributed system architecture
- Use the following reasoning order: context analysis, missing element identification, next component justification, trade off evaluation
- Only set is_complete to true if compute tier, persistence tier, networking tier, ingress, auth (if required), caching or queueing (if needed), and observability are sufficiently represented
- If the architecture sequence is empty you must not guess. Set next_component to null and is_complete to false"""


# ==================== LLM Integration with Instructor ====================

# Use Instructor for structured outputs (same as existing hld_agent.py)
client = instructor.from_groq(
    Groq(api_key=os.environ.get("GROQ_API_KEY")),
    mode=instructor.Mode.JSON
)


def get_model_name() -> str:
    """
    Get LLM model name with priority:
    1. Environment variable HLD_AGENT_MODEL (highest priority)
    2. Config file primary model
    3. Safe default fallback (openai/gpt-oss-120b)
    """
    # Check environment variable override
    env_model = os.environ.get("HLD_AGENT_MODEL")
    if env_model:
        logger.info(f"Using model from HLD_AGENT_MODEL: {env_model}")
        return env_model

    # Load from config
    try:
        config = load_config()
        model = config.get("llm", {}).get("models", {}).get("primary", "openai/gpt-oss-120b")
        logger.info(f"Using model from config: {model}")
        return model
    except Exception as e:
        logger.warning(f"Failed to load config, using default model: {e}")
        return "openai/gpt-oss-120b"  # Safe default

def call_groq_structured(
    current_sequence: str,
    context: str,
    graph: ArchitectureGraph
) -> ArchitectureSuggestion:
    """Call Groq LLM with Instructor for structured output"""

    # Build compact prompt with graph summary
    incomplete = graph.get_incomplete_connections()

    user_prompt = f"""Graph summary
Total components count: {len(graph.components)}
Component types: {', '.join(set(c.type for c in graph.components)) if graph.components else 'None'}
Layer count: {len(graph.layers.keys())}
Incomplete connections: {len(incomplete)}
Incomplete from: {[conn.from_component for conn in incomplete] if incomplete else 'None'}
Sequence: {current_sequence or 'Empty'}

Context
{context}

Task
Identify the next required architectural component based strictly on this graph state.
Apply reasoning in the required order.
Do not invent new terminology or imaginary capabilities.
Produce a complete ArchitectureSuggestion object."""

    try:
        response = client.chat.completions.create(
            model=get_model_name(),
            response_model=ArchitectureSuggestion,
            messages=[
                {"role": "system", "content": SYSTEM_MESSAGE},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
        )

        # Duplicate detection: check if suggested component already exists
        if response.next_component:
            existing_names = [c.name.lower() for c in graph.components]
            if response.next_component.lower() in existing_names:
                logger.warning(
                    f"LLM suggested duplicate component: {response.next_component}. "
                    f"Setting next_component to null and is_complete to false."
                )
                response.next_component = None
                response.is_complete = False

        return response
    except Exception as e:
        logger.error(f"LLM call failed: {e}", exc_info=True)
        # Return safe fallback
        return ArchitectureSuggestion(
            next_component=None,
            explanation=f"LLM error: {str(e)}",
            reasoning="Failed to get LLM response",
            is_complete=True
        )


# Removed iteration_prompt - now using Instructor for structured output


# ==================== Canvas-Aware Agent ====================

class CanvasAwareHLDAgent:
    """HLD Agent that understands Excalidraw canvas context"""

    def __init__(self):
        self.parser = ExcalidrawParser()

    def analyze_canvas(self, canvas_path: str, context: str = "") -> AgentResponse:
        """
        Analyze Excalidraw canvas and generate suggestions

        Args:
            canvas_path: Path to .excalidraw file
            context: Optional context about the system being designed

        Returns:
            AgentResponse with suggestions
        """
        print(f"\n{'='*60}")
        print(f"  🎨 Analyzing Canvas: {Path(canvas_path).name}")
        print(f"{'='*60}\n")

        # Step 1: Parse canvas
        print("📄 Step 1: Parsing Excalidraw canvas...")
        graph = self.parser.parse_from_file(canvas_path)

        print(f"   Found: {len(graph.components)} components, {len(graph.connections)} connections")

        # Step 2: Convert to sequence string
        sequence = graph.to_sequence_string()
        print(f"\n📝 Current Sequence:")
        print(f"   {sequence}\n")

        # Step 3: Generate canvas hash
        with open(canvas_path, 'r') as f:
            canvas_hash = hashlib.md5(f.read().encode()).hexdigest()

        # Step 4: Call agent for suggestions using Instructor
        print("🤖 Step 2: Generating AI suggestions...")

        llm_response = call_groq_structured(sequence, context, graph)
        print(f"✅ Received structured response from LLM")

        # Step 5: Build response
        suggestions = []

        if llm_response.next_component:
            # Calculate suggested position (to the right of the last component)
            max_x = max((c.position["x"] for c in graph.components), default=0)
            suggested_position = {"x": max_x + 200, "y": 220}

            # Determine what it should connect to
            connects_to = []
            incomplete = graph.get_incomplete_connections()
            if incomplete:
                # Connect to the component with incomplete arrow
                connects_to = [incomplete[0].from_component]

            suggestion = ComponentSuggestion(
                component_name=llm_response.next_component,
                component_type=self.parser.classifier.classify(llm_response.next_component),
                reasoning=llm_response.explanation,
                confidence=0.8,  # Could be calculated based on context
                priority="high" if incomplete else "medium",
                position_hint=suggested_position,
                connects_to=connects_to,
                trade_offs=llm_response.reasoning
            )

            suggestions.append(suggestion)

        # Build architecture summary
        summary = self._build_summary(graph, llm_response)

        response = AgentResponse(
            canvas_hash=canvas_hash,
            architecture_summary=summary,
            current_sequence=sequence,
            suggestions=suggestions,
            issues=[],  # Could add pattern-based issue detection
            next_steps=[llm_response.explanation] if llm_response.next_component else [],
            metadata={
                "component_count": len(graph.components),
                "connection_count": len(graph.connections),
                "incomplete_connections": len(graph.get_incomplete_connections()),
                "layers": list(graph.layers.keys()),
            }
        )

        # Display results
        self._display_response(response, graph)

        return response

    def _build_summary(self, graph: ArchitectureGraph, agent_output: ArchitectureSuggestion) -> str:
        """Build natural language summary"""
        component_types = {}
        for comp in graph.components:
            component_types[comp.type] = component_types.get(comp.type, 0) + 1

        type_summary = ', '.join([f"{count} {type}" for type, count in component_types.items()])

        return f"Architecture with {len(graph.components)} components ({type_summary}). {agent_output.reasoning}"

    def _display_response(self, response: AgentResponse, graph: ArchitectureGraph):
        """Display formatted response"""
        print(f"\n{'='*60}")
        print(f"  📊 Analysis Results")
        print(f"{'='*60}\n")

        print(f"📋 Summary:")
        print(f"   {response.architecture_summary}\n")

        print(f"🏗️  Current Architecture:")
        print(f"   {response.current_sequence}\n")

        print(f"💡 Suggestions ({len(response.suggestions)}):")
        if response.suggestions:
            for i, sug in enumerate(response.suggestions, 1):
                print(f"\n   {i}. {sug.component_name} ({sug.component_type})")
                print(f"      Priority: {sug.priority}")
                print(f"      Confidence: {sug.confidence:.0%}")
                print(f"      Reasoning: {sug.reasoning}")
                if sug.position_hint:
                    print(f"      Suggested position: ({sug.position_hint['x']:.0f}, {sug.position_hint['y']:.0f})")
                if sug.connects_to:
                    connect_names = [graph.get_component_by_id(cid).name for cid in sug.connects_to]
                    print(f"      Connects to: {', '.join(connect_names)}")
        else:
            print(f"   No suggestions - architecture appears complete!")

        print(f"\n📈 Metadata:")
        for key, value in response.metadata.items():
            print(f"   {key}: {value}")

        print(f"\n{'='*60}\n")


# ==================== Main Demo ====================

def main():
    """Run demo of canvas-aware HLD agent"""

    # Find canvas file
    canvas_path = Path(__file__).parent.parent / "temp.excalidraw"

    if not canvas_path.exists():
        print(f"❌ Canvas file not found: {canvas_path}")
        print(f"   Please ensure temp.excalidraw exists in the root directory")
        return 1

    # Create agent
    agent = CanvasAwareHLDAgent()

    # Analyze with context
    context = "As a senior engineer, building a high level design architecture"

    try:
        response = agent.analyze_canvas(str(canvas_path), context)

        # Save response to file
        output_file = Path(__file__).parent / "canvas_analysis_result.json"
        with open(output_file, 'w') as f:
            json.dump(response.model_dump(), f, indent=2)

        print(f"💾 Full response saved to: {output_file}")

        print(f"\n✅ Analysis complete!")
        return 0

    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
