"""
Structured logging service for AI Design Copilot
Following CLAUDE.md guidelines for JSON-formatted logs
"""

import logging
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


def setup_llm_logger(name: str) -> logging.Logger:
    """
    Set up a structured JSON logger for LLM operations.

    Creates a logger that writes to both console and file with
    JSON-formatted structured logs for easy querying and debugging.
    """
    logger = logging.getLogger(name)

    # Avoid duplicate handlers if logger already configured
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # Create logs directory if it doesn't exist
    log_dir = Path("logs/llm")
    log_dir.mkdir(parents=True, exist_ok=True)

    # Console handler - human-readable format
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)

    # File handler - JSON format
    log_file = log_dir / f"{name}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)

    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


def log_llm_request(
    logger: logging.Logger,
    prompt: str,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log an LLM request with structured data.

    Args:
        logger: Logger instance
        prompt: The prompt being sent to the LLM
        context: Additional context information
    """
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": "llm_request",
        "prompt": prompt[:200] if prompt else "",  # Truncate for brevity
        "prompt_length": len(prompt) if prompt else 0,
        "context": context or {}
    }

    logger.info(
        f"LLM Request: {prompt[:100]}...",
        extra={"structured_data": log_data}
    )


def log_llm_response(
    logger: logging.Logger,
    response: str,
    valid: bool,
    error: Optional[str] = None
) -> None:
    """
    Log an LLM response with validation status.

    Args:
        logger: Logger instance
        response: The LLM response
        valid: Whether the response passed validation
        error: Error message if validation failed
    """
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": "llm_response",
        "response_preview": response[:200] if response else "",
        "response_length": len(response) if response else 0,
        "valid": valid,
        "error": error
    }

    if valid:
        logger.info(
            "LLM Response: Valid",
            extra={"structured_data": log_data}
        )
    else:
        logger.error(
            f"LLM Response: Invalid - {error}",
            extra={"structured_data": log_data}
        )


def log_api_request(
    logger: logging.Logger,
    endpoint: str,
    method: str,
    request_id: str,
    payload_size: int
) -> None:
    """
    Log an API request.

    Args:
        logger: Logger instance
        endpoint: API endpoint path
        method: HTTP method
        request_id: Unique request identifier
        payload_size: Size of request payload in bytes
    """
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": "api_request",
        "endpoint": endpoint,
        "method": method,
        "request_id": request_id,
        "payload_size": payload_size
    }

    logger.info(
        f"API Request: {method} {endpoint}",
        extra={"structured_data": log_data}
    )
