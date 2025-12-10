"""Configuration settings for HLD Agent."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from functools import lru_cache
from dotenv import load_dotenv


class LLMSettings(BaseModel):
    """LLM configuration settings."""
    provider: str = "groq"
    primary_model: str = Field(alias="models.primary", default="gemma2-9b-it")
    fallback_model: str = Field(alias="models.fallback", default="deepseek-r1-distill-llama-70b")
    temperature: float = 0
    max_iterations: int = 6


class APIKeysSettings(BaseModel):
    """API keys configuration."""
    groq_api_key: str
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    langsmith_api_key: Optional[str] = None
    tavily_api_key: Optional[str] = None


class LangSmithSettings(BaseModel):
    """LangSmith configuration."""
    tracing: bool = True
    project: str = "hld-agent"


class LoggingSettings(BaseModel):
    """Logging configuration."""
    level: str = "INFO"
    format: str = "json"


class GraphSettings(BaseModel):
    """Graph execution configuration."""
    recursion_limit: int = 15
    memory_enabled: bool = True


class HLDSettings(BaseModel):
    """Main configuration settings for HLD Agent."""
    llm: LLMSettings
    api_keys: APIKeysSettings
    langsmith: LangSmithSettings
    logging: LoggingSettings
    graph: GraphSettings


def substitute_env_vars(config_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively substitute environment variables in config values."""
    if isinstance(config_dict, dict):
        return {k: substitute_env_vars(v) for k, v in config_dict.items()}
    elif isinstance(config_dict, list):
        return [substitute_env_vars(item) for item in config_dict]
    elif isinstance(config_dict, str) and config_dict.startswith("${") and config_dict.endswith("}"):
        env_var = config_dict[2:-1]  # Remove ${ and }
        return os.getenv(env_var, config_dict)
    else:
        return config_dict


def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load configuration from YAML file with environment variable substitution."""
    # Load .env file from backend directory first
    env_path = Path(__file__).parent.parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)
    
    if config_path is None:
        config_path = Path(__file__).parent / "config.yaml"
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config_dict = yaml.safe_load(f)
    
    # Substitute environment variables
    config_dict = substitute_env_vars(config_dict)
    
    return config_dict


@lru_cache()
def get_settings(config_path: Optional[Path] = None) -> HLDSettings:
    """Get configuration settings (cached)."""
    config_dict = load_config(config_path)
    
    # Flatten nested config for Pydantic
    flattened_config = {
        "llm": config_dict["llm"],
        "api_keys": config_dict["api_keys"],
        "langsmith": config_dict["langsmith"],
        "logging": config_dict["logging"],
        "graph": config_dict["graph"]
    }
    
    return HLDSettings(**flattened_config)