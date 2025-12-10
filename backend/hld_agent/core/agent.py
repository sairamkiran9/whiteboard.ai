"""Main HLD Agent class.

This module provides the main interface for the High-Level Design Agent,
orchestrating all components while maintaining the exact behavior from hld_agent.py.
"""

import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime

from ..config.settings import get_settings, HLDSettings
from ..graph.builder import create_hld_graph, create_execution_config, create_initial_state
from ..schemas.models import ArchInputState, ArchOutputState
from ..core.exceptions import HLDAgentError, GraphExecutionError
from ..utils.logging import get_logger, LogContext, setup_logging

logger = get_logger(__name__)


class HLDAgent:
    """
    High-Level Design Agent for generating system architecture suggestions.
    
    This agent maintains the exact behavior and logic from hld_agent.py while
    providing a clean, production-ready interface.
    """
    
    def __init__(self, settings: HLDSettings = None, enable_memory: bool = True):
        """
        Initialize the HLD Agent.
        
        Args:
            settings: Configuration settings (loads from config if None)
            enable_memory: Whether to enable conversation memory
        """
        self.settings = settings or get_settings()
        self.enable_memory = enable_memory
        
        # Setup logging based on configuration
        setup_logging(
            level=self.settings.logging.level,
            format_type=self.settings.logging.format
        )
        
        # Create the graph
        self.graph = create_hld_graph(with_memory=enable_memory)
        
        logger.info("🚀 HLD Agent initialized successfully")
        logger.info(f"Configuration: max_iterations={self.settings.llm.max_iterations}, "
                   f"model={self.settings.llm.primary_model}, memory={enable_memory}")
    
    def generate_architecture_suggestion(
        self,
        current_sequence: str,
        context: str = "",
        thread_id: Optional[str] = None,
        recursion_limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate architecture suggestions based on current sequence.
        
        This method replicates the exact test flow from hld_agent.py lines 319-358
        while providing proper error handling and logging.
        
        Args:
            current_sequence: Current architecture sequence (e.g., "user req -> load balancer")
            context: System context description
            thread_id: Unique thread ID for conversation memory
            recursion_limit: Custom recursion limit
            
        Returns:
            Dictionary containing the complete architecture suggestion result
            
        Raises:
            HLDAgentError: If generation fails
        """
        # Generate unique correlation ID for this request
        correlation_id = str(uuid.uuid4())[:8]
        
        if thread_id is None:
            thread_id = f"hld-{correlation_id}"
        
        with LogContext(correlation_id=correlation_id, context={"thread_id": thread_id}):
            logger.info("🚀 Starting architecture generation")
            logger.info(f"📋 Initial: {current_sequence}")
            logger.info(f"🎯 Context: {context}")
            
            try:
                # Create execution configuration
                config = create_execution_config(thread_id, recursion_limit)
                
                # Create initial state (exact logic from hld_agent.py)
                initial_state = create_initial_state(current_sequence, context)
                
                start_time = datetime.utcnow()
                
                # Run the graph (exact logic from hld_agent.py line 326)
                result = self.graph.invoke(initial_state, config)
                
                end_time = datetime.utcnow()
                duration = (end_time - start_time).total_seconds()
                
                # Extract results (exact logic from hld_agent.py lines 328-351)
                final_sequence = result['output_state'].current_sequence if result['output_state'] else 'No output'
                final_iterations = result.get('iteration_count', 0)
                
                logger.info("✅ Architecture generation SUCCESSFUL!")
                logger.info(f"🏁 Final sequence: {final_sequence}")
                logger.info(f"🔢 Total iterations: {final_iterations}")
                logger.info(f"⏱️ Duration: {duration:.2f}s")
                
                # Build response (structured like hld_agent.py output)
                response = {
                    "success": True,
                    "final_sequence": final_sequence,
                    "iterations": final_iterations,
                    "duration_seconds": duration,
                    "output_state": result["output_state"].dict() if result["output_state"] else None,
                    "messages": [
                        {
                            "type": msg.type,
                            "content": msg.content
                        }
                        for msg in result["messages"]
                        if hasattr(msg, 'type') and not msg.content.startswith("❌")
                    ],
                    "thread_id": thread_id,
                    "correlation_id": correlation_id
                }
                
                logger.info("🏆 SUCCESS: Proper recursion handling implemented!")
                return response
                
            except Exception as e:
                logger.error(f"❌ Error during architecture generation: {str(e)}")
                
                # Create error response
                error_response = {
                    "success": False,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "final_sequence": current_sequence,  # Return original sequence
                    "iterations": 0,
                    "thread_id": thread_id,
                    "correlation_id": correlation_id
                }
                
                raise GraphExecutionError(
                    f"Failed to generate architecture: {str(e)}",
                    context=error_response
                )
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get health status of the HLD Agent.
        
        Returns:
            Health status dictionary
        """
        try:
            # Test basic functionality
            test_result = self.generate_architecture_suggestion(
                current_sequence="test -> component",
                context="health check",
                thread_id="health-check"
            )
            
            return {
                "status": "healthy",
                "agent_version": "1.0.0",
                "model": self.settings.llm.primary_model,
                "max_iterations": self.settings.llm.max_iterations,
                "memory_enabled": self.enable_memory,
                "last_test_duration": test_result.get("duration_seconds", 0)
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "agent_version": "1.0.0"
            }
    
    def switch_provider(self, provider: str) -> Dict[str, Any]:
        """
        Switch the LLM provider dynamically.
        
        Args:
            provider: Provider name ('groq', 'openai', 'anthropic')
            
        Returns:
            Success status and updated configuration
        """
        supported_providers = ["groq", "openai", "anthropic"]
        
        if provider not in supported_providers:
            return {
                "success": False,
                "error": f"Provider '{provider}' not supported. Available: {supported_providers}"
            }
        
        try:
            # Update the settings
            old_provider = self.settings.llm.provider
            
            if old_provider == provider:
                return {
                    "success": True,
                    "message": f"Already using {provider} provider",
                    "current_provider": provider,
                    "previous_provider": old_provider
                }
            
            self.settings.llm.provider = provider
            
            # Recreate the graph with new provider settings
            self.graph = create_hld_graph(with_memory=self.enable_memory)
            
            logger.info(f"Successfully switched from {old_provider} to {provider}")
            
            return {
                "success": True,
                "message": f"Switched from {old_provider} to {provider}",
                "current_provider": provider,
                "previous_provider": old_provider
            }
            
        except Exception as e:
            logger.error(f"Failed to switch provider to {provider}: {str(e)}")
            # Revert the settings change
            self.settings.llm.provider = old_provider if 'old_provider' in locals() else provider
            return {
                "success": False,
                "error": f"Failed to switch provider: {str(e)}"
            }
    
    def check_provider_availability(self, provider: str) -> Dict[str, Any]:
        """
        Check if a provider is available (has valid API key).
        
        Args:
            provider: Provider name to check
            
        Returns:
            Availability status and details
        """
        api_key_mapping = {
            "groq": self.settings.api_keys.groq_api_key,
            "openai": self.settings.api_keys.openai_api_key, 
            "anthropic": self.settings.api_keys.anthropic_api_key
        }
        
        if provider not in api_key_mapping:
            return {
                "available": False,
                "reason": f"Unknown provider: {provider}"
            }
        
        api_key = api_key_mapping[provider]
        if not api_key or api_key.startswith("your_") or api_key == "":
            return {
                "available": False,
                "reason": f"API key not configured for {provider}"
            }
        
        return {
            "available": True,
            "reason": f"API key configured for {provider}"
        }
    
    def get_all_provider_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get availability status for all supported providers.
        
        Returns:
            Dictionary with provider status information
        """
        providers = ["groq", "openai", "anthropic"]
        status = {}
        
        for provider in providers:
            status[provider] = self.check_provider_availability(provider)
        
        return status
    
    def get_configuration(self) -> Dict[str, Any]:
        """
        Get current configuration (safe for logging - no API keys).
        
        Returns:
            Configuration dictionary without sensitive data
        """
        return {
            "llm": {
                "provider": self.settings.llm.provider,
                "primary_model": self.settings.llm.primary_model,
                "fallback_model": self.settings.llm.fallback_model,
                "temperature": self.settings.llm.temperature,
                "max_iterations": self.settings.llm.max_iterations
            },
            "langsmith": {
                "tracing": self.settings.langsmith.tracing,
                "project": self.settings.langsmith.project
            },
            "graph": {
                "recursion_limit": self.settings.graph.recursion_limit,
                "memory_enabled": self.enable_memory
            },
            "logging": {
                "level": self.settings.logging.level,
                "format": self.settings.logging.format
            }
        }