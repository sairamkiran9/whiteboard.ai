"""LLM model setup and configuration.

This module contains the exact LLM setup logic from hld_agent.py 
with configuration-driven model selection.
"""

import os
from langchain_groq import ChatGroq
from langchain_core.output_parsers import PydanticOutputParser
from ..config.settings import get_settings, HLDSettings
from ..schemas.models import ArchOutputState
from ..core.exceptions import LLMError, ConfigurationError
from ..utils.logging import get_logger
from .prompts import create_structured_prompt_chain

logger = get_logger(__name__)


def setup_environment_variables(settings: HLDSettings) -> None:
    """Setup environment variables for LangSmith and API keys."""
    # Set API keys
    if settings.api_keys.groq_api_key:
        os.environ["GROQ_API_KEY"] = settings.api_keys.groq_api_key
    else:
        raise ConfigurationError("GROQ_API_KEY is required")
        
    if settings.api_keys.langsmith_api_key:
        os.environ["LANGSMITH_API_KEY"] = settings.api_keys.langsmith_api_key
        
    if settings.api_keys.tavily_api_key:
        os.environ["TAVILY_API_KEY"] = settings.api_keys.tavily_api_key
    
    # Set LangSmith configuration
    if settings.langsmith.tracing:
        os.environ["LANGSMITH_TRACING"] = "true"
        os.environ["LANGSMITH_PROJECT"] = settings.langsmith.project


def create_groq_model(model_name: str, temperature: float = 0) -> ChatGroq:
    """
    Create a ChatGroq model instance.
    
    Args:
        model_name: Name of the Groq model
        temperature: Temperature for generation
        
    Returns:
        Configured ChatGroq instance
        
    Raises:
        LLMError: If model creation fails
    """
    try:
        logger.info(f"Creating ChatGroq model: {model_name}")
        model = ChatGroq(model=model_name, temperature=temperature)
        return model
    except Exception as e:
        raise LLMError(
            f"Failed to create ChatGroq model: {str(e)}", 
            llm_provider="groq", 
            model_name=model_name
        )


def get_available_models(settings: HLDSettings) -> dict:
    """Get available model configurations."""
    models = {
        "primary": settings.llm.primary_model,
        "fallback": settings.llm.fallback_model
    }
    
    logger.info(f"Available models: {models}")
    return models


def get_llm_chain(settings: HLDSettings = None, use_fallback: bool = False):
    """
    Create the complete LLM chain exactly as in hld_agent.py lines 119-123.
    
    Args:
        settings: Configuration settings
        use_fallback: Whether to use fallback model
        
    Returns:
        Tuple of (llm_structured, structured_prompt)
    """
    if settings is None:
        settings = get_settings()
    
    # Setup environment variables
    setup_environment_variables(settings)
    
    # Select model
    models = get_available_models(settings)
    model_name = models["fallback"] if use_fallback else models["primary"]
    
    # Create the base model
    chat_model = create_groq_model(model_name, settings.llm.temperature)
    
    # Create structured prompt and parser (exact logic from hld_agent.py)
    logger.info("📦 Using PydanticOutputParser for Groq model")
    structured_prompt, parser = create_structured_prompt_chain()
    
    # Create the structured LLM chain (from hld_agent.py line 123)
    llm_structured = chat_model | parser
    
    logger.info("🎯 Improved structured prompt with better next component guidance!")
    
    return llm_structured, structured_prompt