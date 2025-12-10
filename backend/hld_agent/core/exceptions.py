"""Custom exceptions for HLD Agent."""


class HLDAgentError(Exception):
    """Base exception for HLD Agent errors."""
    
    def __init__(self, message: str, error_code: str = None, context: dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}


class ConfigurationError(HLDAgentError):
    """Configuration-related errors."""
    
    def __init__(self, message: str, config_key: str = None):
        super().__init__(message, "CONFIG_ERROR", {"config_key": config_key})


class LLMError(HLDAgentError):
    """LLM integration errors."""
    
    def __init__(self, message: str, llm_provider: str = None, model_name: str = None):
        super().__init__(
            message, 
            "LLM_ERROR", 
            {"llm_provider": llm_provider, "model_name": model_name}
        )


class ValidationError(HLDAgentError):
    """Data validation errors."""
    
    def __init__(self, message: str, schema_name: str = None, invalid_fields: list = None):
        super().__init__(
            message,
            "VALIDATION_ERROR",
            {"schema_name": schema_name, "invalid_fields": invalid_fields or []}
        )


class GraphExecutionError(HLDAgentError):
    """LangGraph execution errors."""
    
    def __init__(self, message: str, node_name: str = None, iteration: int = None, context: dict = None):
        error_context = {"node_name": node_name, "iteration": iteration}
        if context:
            error_context.update(context)
        super().__init__(message, "GRAPH_ERROR", error_context)