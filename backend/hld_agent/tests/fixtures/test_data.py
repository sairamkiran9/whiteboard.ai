"""Test data for HLD Agent tests."""

from langchain_core.messages import HumanMessage
from hld_agent.schemas.models import ArchInputState, StructuredArchitectureState

# Test input sequences
TEST_SEQUENCES = [
    {
        "sequence": "user req -> load balancer",
        "context": "distributed job scheduler",
        "expected_next": "job-scheduler"
    },
    {
        "sequence": "user req -> load balancer",
        "context": "web application",
        "expected_next": "api-gateway"
    },
    {
        "sequence": "client -> web server",
        "context": "e-commerce platform", 
        "expected_next": "database"
    },
    {
        "sequence": "mobile app -> api gateway -> cache",
        "context": "social media app",
        "expected_next": "database"
    }
]

# Test cases for schema validation
VALID_ARCH_INPUT_CASES = [
    {
        "current_sequence": "user req -> load balancer",
        "context": "job scheduler"
    },
    {
        "current_sequence": "client -> server",
        "context": ""  # Empty context should be valid
    },
    {
        "current_sequence": "a -> b -> c -> d",
        "context": "complex system with multiple components"
    }
]

INVALID_ARCH_INPUT_CASES = [
    {},  # Missing required fields
    {"current_sequence": ""},  # Empty sequence
    {"context": "missing sequence"},  # Missing sequence field
]

VALID_ARCH_OUTPUT_CASES = [
    {
        "explanation": "API Gateway handles routing",
        "next": "api-gateway",
        "current_sequence": "user req -> load balancer -> api-gateway",
        "reasoning": "Provides centralized routing and auth"
    },
    {
        "explanation": "System complete",
        "next": "__end__",
        "current_sequence": "user req -> load balancer -> api-gateway -> database",
        "reasoning": "All necessary components present"
    }
]

INVALID_ARCH_OUTPUT_CASES = [
    {},  # Missing all required fields
    {"next": "database"},  # Missing other required fields
    {
        "explanation": "",  # Empty explanation
        "next": "database",
        "current_sequence": "a -> b",
        "reasoning": "test"
    }
]

# Test state objects
INITIAL_STATE_JOB_SCHEDULER = StructuredArchitectureState(
    messages=[HumanMessage(content="Building distributed job scheduler")],
    input_state=ArchInputState(
        current_sequence="user req -> load balancer",
        context="distributed job scheduler for batch processing"
    ),
    output_state=None,
    is_complete=False,
    iteration_count=0
)

INITIAL_STATE_WEB_APP = StructuredArchitectureState(
    messages=[HumanMessage(content="Building web application")],
    input_state=ArchInputState(
        current_sequence="user req -> load balancer",
        context="high-traffic web application"
    ),
    output_state=None,
    is_complete=False,
    iteration_count=0
)

# Configuration test cases
CONFIG_TEST_CASES = [
    {
        "name": "valid_config",
        "env_vars": {
            "GROQ_API_KEY": "test-key-123",
            "LANGSMITH_API_KEY": "ls-test-key",
        },
        "expected_groq_key": "test-key-123"
    },
    {
        "name": "missing_groq_key",
        "env_vars": {},
        "should_raise": True
    }
]