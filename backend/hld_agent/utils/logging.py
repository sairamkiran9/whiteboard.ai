"""Structured logging setup for HLD Agent."""

import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict
from functools import lru_cache


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record):
        """Format log record as JSON."""
        log_obj = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add extra fields if present
        if hasattr(record, 'correlation_id'):
            log_obj['correlation_id'] = record.correlation_id
            
        if hasattr(record, 'context'):
            log_obj['context'] = record.context
            
        if record.exc_info:
            log_obj['exception'] = self.formatException(record.exc_info)
            
        return json.dumps(log_obj)


def setup_logging(level: str = "INFO", format_type: str = "json"):
    """
    Setup logging configuration for HLD Agent.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        format_type: Format type ("json" or "text")
    """
    log_level = getattr(logging, level.upper())
    
    # Remove existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    
    if format_type.lower() == "json":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        )
    
    # Configure root logger
    root_logger.setLevel(log_level)
    root_logger.addHandler(handler)
    
    # Reduce noise from external libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("langchain").setLevel(logging.INFO)
    logging.getLogger("langgraph").setLevel(logging.INFO)


@lru_cache()
def get_logger(name: str):
    """
    Get a logger instance for the given name.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class LogContext:
    """Context manager for adding correlation IDs and context to logs."""
    
    def __init__(self, correlation_id: str = None, context: Dict[str, Any] = None):
        self.correlation_id = correlation_id
        self.context = context or {}
        self.old_factory = None
    
    def __enter__(self):
        self.old_factory = logging.getLogRecordFactory()
        
        def record_factory(*args, **kwargs):
            record = self.old_factory(*args, **kwargs)
            if self.correlation_id:
                record.correlation_id = self.correlation_id
            if self.context:
                record.context = self.context
            return record
        
        logging.setLogRecordFactory(record_factory)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.setLogRecordFactory(self.old_factory)