"""Test configuration and fixtures for HLD Agent tests."""

import pytest
from dotenv import load_dotenv


@pytest.fixture(scope="session", autouse=True)
def load_env():
    """Automatically load .env file for all tests."""
    load_dotenv()


@pytest.fixture
def sample_agent_config():
    """Sample configuration for testing."""
    return {
        "llm": {
            "provider": "groq",
            "models": {
                "primary": "gemma2-9b-it",
                "fallback": "deepseek-r1-distill-llama-70b"
            },
            "temperature": 0,
            "max_iterations": 6
        },
        "api_keys": {
            "groq_api_key": "test-key",
            "langsmith_api_key": "test-langsmith-key"
        },
        "langsmith": {
            "tracing": False,
            "project": "hld-agent-test"
        },
        "logging": {
            "level": "INFO",
            "format": "json"
        },
        "graph": {
            "recursion_limit": 12,
            "memory_enabled": True
        }
    }