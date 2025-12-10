"""Unit tests for HLD Agent schemas."""

import pytest
from pydantic import ValidationError
from hld_agent.schemas.models import ArchInputState, ArchOutputState, StructuredArchitectureState
from hld_agent.tests.fixtures.test_data import (
    VALID_ARCH_INPUT_CASES, 
    INVALID_ARCH_INPUT_CASES,
    VALID_ARCH_OUTPUT_CASES,
    INVALID_ARCH_OUTPUT_CASES
)


class TestArchInputState:
    """Test cases for ArchInputState schema validation."""
    
    @pytest.mark.parametrize("valid_input", VALID_ARCH_INPUT_CASES)
    def test_valid_arch_input_state(self, valid_input):
        """Test that valid input creates ArchInputState successfully."""
        state = ArchInputState(**valid_input)
        assert state.current_sequence == valid_input["current_sequence"]
        assert state.context == valid_input.get("context", "")
    
    @pytest.mark.parametrize("invalid_input", INVALID_ARCH_INPUT_CASES)
    def test_invalid_arch_input_state(self, invalid_input):
        """Test that invalid input raises ValidationError."""
        with pytest.raises(ValidationError):
            ArchInputState(**invalid_input)
    
    def test_arch_input_state_defaults(self):
        """Test that context has proper default value."""
        state = ArchInputState(current_sequence="test -> sequence")
        assert state.context == ""
    
    def test_arch_input_state_serialization(self):
        """Test serialization/deserialization of ArchInputState."""
        original = ArchInputState(
            current_sequence="user req -> load balancer",
            context="test context"
        )
        
        # Test dict conversion
        data = original.model_dump()
        assert data["current_sequence"] == "user req -> load balancer"
        assert data["context"] == "test context"
        
        # Test reconstruction
        reconstructed = ArchInputState(**data)
        assert reconstructed.current_sequence == original.current_sequence
        assert reconstructed.context == original.context


class TestArchOutputState:
    """Test cases for ArchOutputState schema validation."""
    
    @pytest.mark.parametrize("valid_output", VALID_ARCH_OUTPUT_CASES)
    def test_valid_arch_output_state(self, valid_output):
        """Test that valid output creates ArchOutputState successfully."""
        state = ArchOutputState(**valid_output)
        assert state.explanation == valid_output["explanation"]
        assert state.next == valid_output["next"]
        assert state.current_sequence == valid_output["current_sequence"]
        assert state.reasoning == valid_output["reasoning"]
    
    @pytest.mark.parametrize("invalid_output", INVALID_ARCH_OUTPUT_CASES)
    def test_invalid_arch_output_state(self, invalid_output):
        """Test that invalid output raises ValidationError."""
        with pytest.raises(ValidationError):
            ArchOutputState(**invalid_output)
    
    def test_arch_output_state_end_condition(self):
        """Test __end__ condition handling."""
        end_state = ArchOutputState(
            explanation="Architecture complete",
            next="__end__",
            current_sequence="user req -> load balancer -> database",
            reasoning="All components present"
        )
        assert end_state.next == "__end__"
    
    def test_arch_output_state_serialization(self):
        """Test serialization/deserialization of ArchOutputState."""
        original = ArchOutputState(
            explanation="Test explanation", 
            next="database",
            current_sequence="user req -> load balancer -> database",
            reasoning="Test reasoning"
        )
        
        # Test dict conversion
        data = original.model_dump()
        assert len(data) == 4
        assert all(key in data for key in ["explanation", "next", "current_sequence", "reasoning"])
        
        # Test reconstruction
        reconstructed = ArchOutputState(**data)
        assert reconstructed.explanation == original.explanation
        assert reconstructed.next == original.next


class TestStructuredArchitectureState:
    """Test cases for StructuredArchitectureState TypedDict."""
    
    def test_structured_architecture_state_creation(self):
        """Test creation of StructuredArchitectureState."""
        from langchain_core.messages import HumanMessage
        
        state = StructuredArchitectureState(
            messages=[HumanMessage(content="test")],
            input_state=ArchInputState(current_sequence="test", context="test"),
            output_state=None,
            is_complete=False,
            iteration_count=0
        )
        
        assert len(state["messages"]) == 1
        assert state["input_state"].current_sequence == "test"
        assert state["output_state"] is None
        assert state["is_complete"] is False
        assert state["iteration_count"] == 0
    
    def test_structured_architecture_state_with_output(self):
        """Test StructuredArchitectureState with output_state."""
        from langchain_core.messages import HumanMessage
        
        input_state = ArchInputState(current_sequence="a -> b", context="test")
        output_state = ArchOutputState(
            explanation="test",
            next="c", 
            current_sequence="a -> b -> c",
            reasoning="test reasoning"
        )
        
        state = StructuredArchitectureState(
            messages=[HumanMessage(content="test")],
            input_state=input_state,
            output_state=output_state,
            is_complete=True,
            iteration_count=3
        )
        
        assert state["output_state"].next == "c"
        assert state["is_complete"] is True
        assert state["iteration_count"] == 3


class TestSampleData:
    """Test the sample data provided in schemas module."""
    
    def test_sample_input_validation(self):
        """Test that SAMPLE_INPUT is valid."""
        from hld_agent.schemas.models import SAMPLE_INPUT
        
        assert isinstance(SAMPLE_INPUT, ArchInputState)
        assert SAMPLE_INPUT.current_sequence == "user req -> load balancer"
        assert SAMPLE_INPUT.context == "distributed job scheduler"
    
    def test_sample_output_validation(self):
        """Test that SAMPLE_OUTPUT is valid."""
        from hld_agent.schemas.models import SAMPLE_OUTPUT
        
        assert isinstance(SAMPLE_OUTPUT, ArchOutputState)
        assert SAMPLE_OUTPUT.next == "api gateway"
        assert "load balancer -> api gateway" in SAMPLE_OUTPUT.current_sequence