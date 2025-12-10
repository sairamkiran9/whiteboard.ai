# HLD Agent - High-Level Design AI Agent

A production-ready, modular AI agent for generating system architecture suggestions using LangGraph and LangChain.

## 🏗️ Architecture Overview

The HLD Agent is a complete refactor of the original `hld_agent.py` monolithic file into a clean, modular Python package that maintains exact functionality while providing:

- **Modular Design**: Clean separation of concerns across multiple modules
- **Configuration Management**: YAML-based configuration with environment variable support
- **Comprehensive Testing**: Full unit and integration test coverage
- **Structured Logging**: JSON-formatted logs with correlation IDs
- **Error Handling**: Proper exception hierarchy and graceful fallbacks
- **FastAPI Integration**: Drop-in replacement for existing suggestion services

## 📁 Package Structure

```
hld_agent/
├── __init__.py                     # Package exports
├── config/
│   ├── __init__.py
│   ├── config.yaml                 # Configuration file
│   └── settings.py                 # Settings management
├── core/
│   ├── __init__.py
│   ├── agent.py                    # Main HLD Agent class
│   └── exceptions.py               # Custom exceptions
├── graph/
│   ├── __init__.py
│   ├── builder.py                  # LangGraph construction
│   └── nodes.py                    # Graph node functions
├── llm/
│   ├── __init__.py
│   ├── models.py                   # LLM initialization
│   └── prompts.py                  # Prompt templates
├── schemas/
│   ├── __init__.py
│   └── models.py                   # Pydantic data models
├── utils/
│   ├── __init__.py
│   └── logging.py                  # Structured logging
└── tests/
    ├── __init__.py
    ├── fixtures/
    │   ├── __init__.py
    │   ├── mock_responses.py       # Mock LLM responses
    │   └── test_data.py            # Test data
    ├── integration/
    │   ├── __init__.py
    │   └── test_agent_flow.py      # End-to-end tests
    └── unit/
        ├── __init__.py
        ├── test_config.py          # Configuration tests
        └── test_schemas.py         # Schema validation tests
```

## 🚀 Quick Start

### Installation

```bash
# Install dependencies
uv pip install -r requirements.txt

# Set environment variables
export GROQ_API_KEY="your-groq-api-key"
export LANGSMITH_API_KEY="your-langsmith-key"  # Optional
```

### Basic Usage

```python
from hld_agent import HLDAgent

# Initialize agent
agent = HLDAgent()

# Generate architecture suggestion
result = agent.generate_architecture_suggestion(
    current_sequence="user req -> load balancer",
    context="distributed job scheduler"
)

print(f"Success: {result['success']}")
print(f"Final sequence: {result['final_sequence']}")
print(f"Iterations: {result['iterations']}")
```

## ⚙️ Configuration

### YAML Configuration

The agent uses a YAML configuration file with environment variable substitution:

```yaml
# config/config.yaml
llm:
  provider: "groq"
  models:
    primary: "gemma2-9b-it"
    fallback: "deepseek-r1-distill-llama-70b"
  temperature: 0
  max_iterations: 6

api_keys:
  groq_api_key: "${GROQ_API_KEY}"
  langsmith_api_key: "${LANGSMITH_API_KEY}"

langsmith:
  tracing: false
  project: "hld-agent"

logging:
  level: "INFO"
  format: "json"

graph:
  recursion_limit: 12
  memory_enabled: true
```

### Environment Variables

- `GROQ_API_KEY`: Required - Your Groq API key
- `LANGSMITH_API_KEY`: Optional - For LangSmith tracing

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest hld_agent/tests/

# Run unit tests only
pytest hld_agent/tests/unit/

# Run integration tests only
pytest hld_agent/tests/integration/

# Run with coverage
pytest --cov=hld_agent hld_agent/tests/
```

### Test Categories

1. **Unit Tests**: Test individual components in isolation
   - Configuration loading and validation
   - Schema validation and serialization
   - LLM model initialization
   - Graph node functions

2. **Integration Tests**: Test complete workflows
   - Agent initialization with different configurations
   - End-to-end architecture generation
   - Health checking functionality
   - Error handling scenarios

## 📊 FastAPI Integration

The HLD Agent serves as a drop-in replacement for the existing hardcoded suggestion service:

```python
# In your FastAPI router
from hld_agent import HLDAgent
from hld_agent.core.exceptions import HLDAgentError

# Initialize agent
hld_agent = HLDAgent()

@router.post("/suggest")
async def suggest_architecture(request: CanvasRequest):
    try:
        # Convert canvas to sequence format
        current_sequence, context = convert_canvas_to_sequence(
            request.canvas_elements, request.context
        )
        
        # Generate suggestion
        result = hld_agent.generate_architecture_suggestion(
            current_sequence=current_sequence,
            context=context
        )
        
        # Convert to response format
        return convert_agent_result_to_response(result)
        
    except HLDAgentError as e:
        return SuggestionResponse(
            suggestion=None,
            reasoning=f"Agent error: {str(e)}",
            reference=None
        )
```

## 🔍 Key Features

### Exact Logic Preservation

- **Prompts**: All prompts from `hld_agent.py` lines 128-151 preserved exactly
- **Node Functions**: Graph nodes from lines 160-253 maintain identical logic
- **State Management**: Exact state handling and iteration counting
- **Output Format**: Maintains same response structure

### Production-Ready Features

- **Structured Logging**: JSON logs with correlation IDs and context
- **Configuration Management**: YAML config with environment variable substitution
- **Error Handling**: Custom exception hierarchy with proper error propagation
- **Health Monitoring**: Built-in health checks and status reporting
- **Memory Management**: Optional conversation memory with LangGraph checkpointing

### Performance & Reliability

- **Caching**: LRU caching for settings and logger instances
- **Recursion Protection**: Proactive iteration limits to prevent infinite loops
- **Graceful Fallbacks**: Safe error handling with meaningful error messages
- **Resource Management**: Proper cleanup and resource management

## 🏥 Health Monitoring

```python
# Check agent health
health_status = agent.get_health_status()

print(f"Status: {health_status['status']}")
print(f"Model: {health_status['model']}")
print(f"Test Duration: {health_status['last_test_duration']}s")
```

## 🔧 Advanced Usage

### Custom Configuration

```python
from pathlib import Path
from hld_agent.config.settings import get_settings

# Load custom config
custom_config = get_settings(Path("my_config.yaml"))
agent = HLDAgent(settings=custom_config)
```

### Memory Management

```python
# Enable conversation memory
agent = HLDAgent(enable_memory=True)

# Use thread IDs for conversation continuity
result1 = agent.generate_architecture_suggestion(
    current_sequence="user req",
    thread_id="session-123"
)

result2 = agent.generate_architecture_suggestion(
    current_sequence=result1['final_sequence'],
    thread_id="session-123"  # Same thread for memory
)
```

### Structured Logging

```python
from hld_agent.utils.logging import LogContext

# Add correlation IDs and context to logs
with LogContext(correlation_id="req-123", context={"user": "demo"}):
    result = agent.generate_architecture_suggestion(
        current_sequence="user req -> load balancer"
    )
```

## 🔄 Migration from Monolithic Version

The modular HLD Agent is designed as a drop-in replacement:

1. **Same API**: The `generate_architecture_suggestion()` method maintains the same signature
2. **Same Output**: Response format is identical to original implementation
3. **Same Logic**: All prompt templates and graph logic preserved exactly
4. **Enhanced Features**: Adds logging, configuration, and testing without changing behavior

## 📚 API Reference

### HLDAgent Class

#### `__init__(settings=None, enable_memory=True)`
Initialize the HLD Agent with optional custom settings and memory configuration.

#### `generate_architecture_suggestion(current_sequence, context="", thread_id=None, recursion_limit=None)`
Generate architecture suggestions based on current sequence and context.

**Returns**: Dictionary with success status, final sequence, iterations, and detailed results.

#### `get_health_status()`
Get current health status of the agent including model information and test results.

#### `get_configuration()`
Get current configuration (excludes sensitive API keys for security).

### Exceptions

- `HLDAgentError`: Base exception for all agent-related errors
- `ConfigurationError`: Configuration loading or validation errors  
- `LLMError`: LLM-related errors (API failures, parsing errors)
- `GraphExecutionError`: Graph execution and state management errors

## 🤝 Contributing

1. Run tests before submitting changes: `pytest`
2. Follow existing code style and patterns
3. Add tests for new functionality
4. Update documentation for API changes

## 📝 License

This project follows the same license as the parent whiteboard-ai project.