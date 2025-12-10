"""Integration tests for complete HLD Agent flow.

These tests verify the end-to-end functionality of the HLD Agent,
including real LLM interactions (when API keys are available).
"""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from hld_agent.core.agent import HLDAgent
from hld_agent.config.settings import get_settings, HLDSettings
from hld_agent.core.exceptions import HLDAgentError, ConfigurationError
from hld_agent.tests.fixtures.mock_responses import MOCK_CONFIG_YAML, MOCK_JOB_SCHEDULER_FLOW


class TestHLDAgentInitialization:
    """Test HLD Agent initialization and configuration."""
    
    def test_agent_initialization_with_default_config(self):
        """Test agent initializes with default configuration."""
        # Mock environment variables
        with patch.dict(os.environ, {"GROQ_API_KEY": "test-key"}):
            agent = HLDAgent()
            
            assert agent is not None
            assert agent.settings is not None
            assert agent.graph is not None
            assert agent.enable_memory is True
    
    def test_agent_initialization_without_memory(self):
        """Test agent initialization without memory."""
        with patch.dict(os.environ, {"GROQ_API_KEY": "test-key"}):
            agent = HLDAgent(enable_memory=False)
            
            assert agent.enable_memory is False
    
    def test_agent_initialization_with_custom_settings(self):
        """Test agent initialization with custom settings."""
        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(MOCK_CONFIG_YAML)
            f.flush()
            config_path = Path(f.name)
        
        try:
            with patch.dict(os.environ, {"GROQ_API_KEY": "test-custom-key"}):
                settings = get_settings(config_path)
                agent = HLDAgent(settings=settings)
                
                assert agent.settings.llm.max_iterations == 3  # From mock config
                assert agent.settings.langsmith.tracing is False
                
        finally:
            config_path.unlink()
    
    def test_agent_initialization_missing_api_key(self):
        """Test that configuration loading works with missing environment variables.""" 
        # Create a config that has an undefined environment variable
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
llm:
  provider: "groq"
  models:
    primary: "gemma2-9b-it"
    fallback: "deepseek-r1-distill-llama-70b"
  temperature: 0
  max_iterations: 3
  
api_keys:
  groq_api_key: "${UNDEFINED_GROQ_API_KEY}"
  
langsmith:
  tracing: false
  project: "test-hld-agent"
  
logging:
  level: "INFO" 
  format: "json"
  
graph:
  recursion_limit: 10
  memory_enabled: true
            """)
            f.flush()
            config_path = Path(f.name)
        
        try:
            # Clear environment so env var substitution returns placeholder
            with patch.dict(os.environ, {}, clear=True):
                from hld_agent.config.settings import get_settings
                get_settings.cache_clear()  # Clear cache
                
                settings = get_settings(config_path)
                # Should get placeholder since env var doesn't exist
                assert settings.api_keys.groq_api_key == "${UNDEFINED_GROQ_API_KEY}"
                
                # Configuration loading should work, but the key is clearly a placeholder
                assert settings.llm.provider == "groq"
                assert settings.llm.max_iterations == 3
        finally:
            config_path.unlink()


class TestHLDAgentHealthCheck:
    """Test HLD Agent health checking functionality."""
    
    @patch('hld_agent.core.agent.HLDAgent.generate_architecture_suggestion')
    def test_health_status_healthy(self, mock_generate):
        """Test health status when agent is working."""
        mock_generate.return_value = {
            "success": True,
            "duration_seconds": 1.5,
            "final_sequence": "test -> component -> result"
        }
        
        with patch.dict(os.environ, {"GROQ_API_KEY": "test-key"}):
            agent = HLDAgent()
            status = agent.get_health_status()
            
            assert status["status"] == "healthy"
            assert status["agent_version"] == "1.0.0"
            assert "last_test_duration" in status
            assert status["model"] == "gemma2-9b-it"
    
    @patch('hld_agent.core.agent.HLDAgent.generate_architecture_suggestion')
    def test_health_status_unhealthy(self, mock_generate):
        """Test health status when agent has errors."""
        mock_generate.side_effect = Exception("LLM connection failed")
        
        with patch.dict(os.environ, {"GROQ_API_KEY": "test-key"}):
            agent = HLDAgent()
            status = agent.get_health_status()
            
            assert status["status"] == "unhealthy"
            assert "error" in status
            assert "LLM connection failed" in status["error"]


class TestHLDAgentConfiguration:
    """Test HLD Agent configuration management."""
    
    def test_get_configuration_excludes_sensitive_data(self):
        """Test that configuration excludes API keys."""
        with patch.dict(os.environ, {"GROQ_API_KEY": "secret-key-123"}):
            agent = HLDAgent()
            config = agent.get_configuration()
            
            # Should include non-sensitive configuration
            assert "llm" in config
            assert config["llm"]["provider"] == "groq"
            assert "langsmith" in config
            assert "graph" in config
            assert "logging" in config
            
            # Should not include sensitive data
            assert "api_keys" not in config
            assert "secret-key-123" not in str(config)


class TestHLDAgentArchitectureGeneration:
    """Test architecture generation with mocked LLM responses."""
    
    def test_architecture_generation_single_iteration(self):
        """Test single iteration architecture generation."""
        with patch.dict(os.environ, {"GROQ_API_KEY": "test-key"}):
            agent = HLDAgent()
            
            # Mock the graph.invoke method directly
            with patch.object(agent, 'graph') as mock_graph:
                mock_graph.invoke.return_value = {
                    "output_state": MOCK_JOB_SCHEDULER_FLOW[0],
                    "iteration_count": 1,
                    "messages": []
                }
                
                result = agent.generate_architecture_suggestion(
                    current_sequence="user req -> load balancer",
                    context="distributed job scheduler"
                )
                
                assert result["success"] is True
                assert "job-scheduler" in result["final_sequence"]
                assert result["iterations"] == 1
                assert "correlation_id" in result
    
    def test_architecture_generation_multiple_iterations(self):
        """Test multiple iteration architecture generation."""
        from langchain_core.messages import HumanMessage
        
        with patch.dict(os.environ, {"GROQ_API_KEY": "test-key"}):
            agent = HLDAgent()
            
            # Mock the graph.invoke method directly
            with patch.object(agent, 'graph') as mock_graph:
                # Create proper message objects
                test_messages = [
                    HumanMessage(content="Message 1"),
                    HumanMessage(content="Message 2"), 
                    HumanMessage(content="Message 3")
                ]
                
                mock_graph.invoke.return_value = {
                    "output_state": MOCK_JOB_SCHEDULER_FLOW[2],  # 3rd iteration
                    "iteration_count": 3,
                    "messages": test_messages
                }
                
                result = agent.generate_architecture_suggestion(
                    current_sequence="user req -> load balancer",
                    context="distributed job scheduler"
                )
                
                assert result["success"] is True
                assert result["iterations"] == 3
                assert len(result["messages"]) == 3
    
    def test_architecture_generation_custom_thread_id(self):
        """Test architecture generation with custom thread ID."""
        with patch.dict(os.environ, {"GROQ_API_KEY": "test-key"}):
            agent = HLDAgent()
            
            # Mock the graph.invoke method directly
            with patch.object(agent, 'graph') as mock_graph:
                mock_graph.invoke.return_value = {
                    "output_state": MOCK_JOB_SCHEDULER_FLOW[0],
                    "iteration_count": 1,
                    "messages": []
                }
                
                result = agent.generate_architecture_suggestion(
                    current_sequence="user req -> load balancer",
                    context="test",
                    thread_id="custom-thread-123"
                )
                
                assert result["thread_id"] == "custom-thread-123"
    
    def test_architecture_generation_with_recursion_limit(self):
        """Test architecture generation with custom recursion limit."""
        with patch.dict(os.environ, {"GROQ_API_KEY": "test-key"}):
            agent = HLDAgent()
            
            # Mock the graph.invoke method directly
            with patch.object(agent, 'graph') as mock_graph:
                mock_graph.invoke.return_value = {
                    "output_state": MOCK_JOB_SCHEDULER_FLOW[0],
                    "iteration_count": 1,
                    "messages": []
                }
                
                result = agent.generate_architecture_suggestion(
                    current_sequence="user req -> load balancer",
                    context="test",
                    recursion_limit=5
                )
                
                # Should execute successfully with custom recursion limit
                assert result["success"] is True


class TestHLDAgentErrorHandling:
    """Test error handling in HLD Agent."""
    
    def test_architecture_generation_graph_error(self):
        """Test handling of graph execution errors."""
        with patch.dict(os.environ, {"GROQ_API_KEY": "test-key"}):
            agent = HLDAgent()
            
            # Mock the graph.invoke method to raise an error
            with patch.object(agent, 'graph') as mock_graph:
                mock_graph.invoke.side_effect = Exception("Graph execution failed")
                
                with pytest.raises(Exception):
                    agent.generate_architecture_suggestion(
                        current_sequence="user req -> load balancer",
                        context="test"
                    )
    
    def test_architecture_generation_invalid_input(self):
        """Test handling of invalid input."""
        with patch.dict(os.environ, {"GROQ_API_KEY": "test-key"}):
            agent = HLDAgent()
            
            # Test with empty sequence - should raise validation error now due to min_length=1
            with pytest.raises(Exception):
                agent.generate_architecture_suggestion(
                    current_sequence="",  # Invalid empty sequence
                    context="test"
                )