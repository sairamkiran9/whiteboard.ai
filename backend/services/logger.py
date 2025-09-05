"""
Structured JSON logging configuration for LLM requests/responses
Following CLAUDE.md guidelines for audit and debugging
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict


class JSONFormatter(logging.Formatter):
    """Custom formatter for structured JSON logs"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.name,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, 'extra'):
            log_entry.update(record.extra)
            
        return json.dumps(log_entry)


def setup_llm_logger(name: str = "llm_logger") -> logging.Logger:
    """
    Set up structured JSON logger for LLM requests/responses
    Saves logs to logs/llm/ directory with timestamps
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Create logs directory if it doesn't exist
    os.makedirs("logs/llm", exist_ok=True)
    
    # File handler with timestamped filename
    date_str = datetime.now().strftime("%Y-%m-%d")
    file_handler = logging.FileHandler(
        f"logs/llm/{date_str}.json", 
        mode='a'
    )
    file_handler.setFormatter(JSONFormatter())
    
    # Console handler for development
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JSONFormatter())
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def log_llm_request(logger: logging.Logger, prompt: str, context: Dict[str, Any] = None):
    """Log LLM request with structured format"""
    logger.info(
        "LLM Request",
        extra={
            "event_type": "llm_request",
            "prompt_length": len(prompt),
            "prompt_preview": prompt[:200] + "..." if len(prompt) > 200 else prompt,
            "context": context or {}
        }
    )


def log_llm_response(logger: logging.Logger, response: str, valid: bool, error: str = None):
    """Log LLM response with validation status"""
    logger.info(
        "LLM Response",
        extra={
            "event_type": "llm_response",
            "response_length": len(response),
            "response_preview": response[:200] + "..." if len(response) > 200 else response,
            "validation_passed": valid,
            "error": error
        }
    )