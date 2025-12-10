"""Unit tests for HLD Agent configuration."""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch

from hld_agent.config.settings import (
    get_settings, 
    load_config, 
    substitute_env_vars, 
    HLDSettings,
    LLMSettings,
    APIKeysSettings
)
from hld_agent.tests.fixtures.mock_responses import MOCK_CONFIG_YAML
from hld_agent.core.exceptions import ConfigurationError


class TestEnvironmentVariableSubstitution:
    """Test environment variable substitution in config."""
    
    def test_substitute_env_vars_with_existing_var(self):
        """Test substitution when environment variable exists."""
        config = {"api_key": "${TEST_API_KEY}"}
        
        with patch.dict(os.environ, {"TEST_API_KEY": "secret-123"}):
            result = substitute_env_vars(config)
        
        assert result["api_key"] == "secret-123"
    
    def test_substitute_env_vars_with_missing_var(self):
        """Test substitution when environment variable is missing."""
        config = {"api_key": "${MISSING_API_KEY}"}
        
        # Clear the environment variable if it exists
        with patch.dict(os.environ, {}, clear=True):
            result = substitute_env_vars(config)
        
        # Should return the original placeholder
        assert result["api_key"] == "${MISSING_API_KEY}"
    
    def test_substitute_env_vars_nested_dict(self):
        """Test substitution in nested dictionary."""
        config = {
            "database": {
                "host": "${DB_HOST}",
                "port": 5432,
                "credentials": {
                    "username": "${DB_USER}",
                    "password": "${DB_PASS}"
                }
            }
        }
        
        with patch.dict(os.environ, {
            "DB_HOST": "localhost",
            "DB_USER": "testuser", 
            "DB_PASS": "testpass"
        }):
            result = substitute_env_vars(config)
        
        assert result["database"]["host"] == "localhost"
        assert result["database"]["port"] == 5432
        assert result["database"]["credentials"]["username"] == "testuser"
        assert result["database"]["credentials"]["password"] == "testpass"
    
    def test_substitute_env_vars_with_list(self):
        """Test substitution in lists."""
        config = {
            "servers": ["${SERVER_1}", "${SERVER_2}", "static-server"]
        }
        
        with patch.dict(os.environ, {
            "SERVER_1": "server1.example.com",
            "SERVER_2": "server2.example.com"
        }):
            result = substitute_env_vars(config)
        
        assert result["servers"] == [
            "server1.example.com",
            "server2.example.com", 
            "static-server"
        ]
    
    def test_substitute_env_vars_non_placeholder_strings(self):
        """Test that non-placeholder strings are unchanged."""
        config = {"message": "Hello World", "url": "https://example.com"}
        
        result = substitute_env_vars(config)
        
        assert result["message"] == "Hello World"
        assert result["url"] == "https://example.com"


class TestConfigLoading:
    """Test configuration loading from YAML files."""
    
    def test_load_config_from_file(self):
        """Test loading configuration from temporary YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(MOCK_CONFIG_YAML)
            f.flush()
            
            config_path = Path(f.name)
        
        try:
            with patch.dict(os.environ, {"GROQ_API_KEY": "test-groq-key"}):
                config = load_config(config_path)
            
            assert config["llm"]["provider"] == "groq"
            assert config["llm"]["models"]["primary"] == "gemma2-9b-it"
            assert config["api_keys"]["groq_api_key"] == "test-groq-key"
            assert config["langsmith"]["tracing"] is False
            
        finally:
            config_path.unlink()  # Clean up temp file
    
    def test_load_config_file_not_found(self):
        """Test error handling when config file doesn't exist."""
        non_existent_path = Path("/tmp/non_existent_config.yaml")
        
        with pytest.raises(FileNotFoundError):
            load_config(non_existent_path)


class TestHLDSettings:
    """Test HLDSettings Pydantic model."""
    
    def test_hld_settings_creation(self):
        """Test creating HLDSettings with valid data."""
        config_data = {
            "llm": {
                "provider": "groq",
                "models": {"primary": "gemma2-9b-it", "fallback": "deepseek"},
                "temperature": 0,
                "max_iterations": 5
            },
            "api_keys": {"groq_api_key": "test-key"},
            "langsmith": {"tracing": True, "project": "test"},
            "logging": {"level": "INFO", "format": "json"},
            "graph": {"recursion_limit": 10, "memory_enabled": True}
        }
        
        settings = HLDSettings(**config_data)
        
        assert settings.llm.provider == "groq"
        assert settings.llm.max_iterations == 5
        assert settings.api_keys.groq_api_key == "test-key"
        assert settings.langsmith.tracing is True
        assert settings.graph.recursion_limit == 10
    
    def test_llm_settings_defaults(self):
        """Test LLMSettings default values."""
        llm_settings = LLMSettings()
        
        assert llm_settings.provider == "groq"
        assert llm_settings.temperature == 0
        assert llm_settings.max_iterations == 6
    
    def test_api_keys_settings_validation(self):
        """Test APIKeysSettings validation."""
        # Valid case
        api_keys = APIKeysSettings(groq_api_key="valid-key")
        assert api_keys.groq_api_key == "valid-key"
        assert api_keys.langsmith_api_key is None
        
        # Missing required key
        with pytest.raises(Exception):
            APIKeysSettings()


class TestGetSettings:
    """Test the get_settings function with caching."""
    
    def test_get_settings_with_temp_config(self):
        """Test get_settings loads from temporary config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(MOCK_CONFIG_YAML)
            f.flush()
            config_path = Path(f.name)
        
        try:
            with patch.dict(os.environ, {
                "GROQ_API_KEY": "test-groq-key",
                "LANGSMITH_API_KEY": "test-ls-key"
            }):
                settings = get_settings(config_path)
            
            assert isinstance(settings, HLDSettings)
            assert settings.llm.max_iterations == 3  # From mock config
            assert settings.api_keys.groq_api_key == "test-groq-key"
            
        finally:
            config_path.unlink()
    
    @patch('hld_agent.config.settings.get_settings.cache_clear')
    def test_get_settings_caching(self, mock_cache_clear):
        """Test that get_settings is properly cached."""
        # The @lru_cache decorator should cache results
        # This test verifies the function has cache_clear method
        assert hasattr(get_settings, 'cache_clear')
        mock_cache_clear.assert_not_called()
        
        # Call cache_clear to verify it exists
        get_settings.cache_clear()
        mock_cache_clear.assert_called_once()