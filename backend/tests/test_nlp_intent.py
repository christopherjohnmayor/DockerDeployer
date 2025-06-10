"""
Tests for the NLP Intent Parser module.
"""

from unittest.mock import AsyncMock, MagicMock, patch
import pytest
import json

from nlp.intent import IntentParser
from llm.engine.parser import ResponseParsingError


class TestIntentParser:
    """Test suite for IntentParser class."""

    @pytest.fixture
    def mock_settings_manager(self):
        """Create a mock settings manager."""
        mock_manager = MagicMock()
        mock_manager.load.return_value = {
            "llm_provider": "openrouter",
            "llm_api_url": "https://openrouter.ai/api/v1/chat/completions",
            "llm_api_key": "test_api_key",
            "llm_model": "meta-llama/llama-3.2-3b-instruct:free"
        }
        return mock_manager

    @pytest.fixture
    def mock_llm_client(self):
        """Create a mock LLM client."""
        mock_client = AsyncMock()
        mock_client.send_query.return_value = json.dumps({
            "is_docker_command": True,
            "command_type": "container",
            "operation": "list",
            "parameters": {},
            "missing_info": [],
            "docker_command": "docker ps",
            "explanation": "List all running containers"
        })
        return mock_client

    @patch('nlp.intent.SettingsManager')
    @patch('nlp.intent.LLMClient')
    def test_init_success(self, mock_llm_client_class, mock_settings_manager_class):
        """Test successful initialization of IntentParser."""
        mock_settings_manager_class.return_value.load.return_value = {
            "llm_provider": "openrouter",
            "llm_api_key": "test_key"
        }
        
        parser = IntentParser()
        
        assert parser.settings_manager is not None
        assert parser._llm_client is not None
        mock_llm_client_class.assert_called_once()

    @patch('nlp.intent.SettingsManager')
    @patch('nlp.intent.LLMClient')
    def test_init_llm_client_failure(self, mock_llm_client_class, mock_settings_manager_class):
        """Test initialization when LLM client creation fails."""
        mock_settings_manager_class.return_value.load.side_effect = Exception("Settings error")
        
        parser = IntentParser()
        
        assert parser._llm_client is None

    @patch('nlp.intent.SettingsManager')
    @patch('nlp.intent.LLMClient')
    @pytest.mark.asyncio
    async def test_parse_with_llm_success(self, mock_llm_client_class, mock_settings_manager_class):
        """Test successful parsing with LLM."""
        # Setup mocks
        mock_settings = {
            "llm_provider": "openrouter",
            "llm_api_key": "test_key",
            "llm_model": "meta-llama/llama-3.2-3b-instruct:free"
        }
        mock_settings_manager_class.return_value.load.return_value = mock_settings
        
        mock_llm_response = json.dumps({
            "is_docker_command": True,
            "command_type": "container",
            "operation": "list",
            "parameters": {},
            "missing_info": [],
            "docker_command": "docker ps",
            "explanation": "List all running containers"
        })
        
        mock_client = AsyncMock()
        mock_client.send_query.return_value = mock_llm_response
        mock_llm_client_class.return_value = mock_client
        
        parser = IntentParser()
        result = await parser.parse("list all containers")
        
        assert result["is_docker_command"] is True
        assert result["command_type"] == "container"
        assert result["operation"] == "list"
        mock_client.send_query.assert_called_once()

    @patch('nlp.intent.SettingsManager')
    @patch('nlp.intent.LLMClient')
    @pytest.mark.asyncio
    async def test_parse_llm_failure_fallback(self, mock_llm_client_class, mock_settings_manager_class):
        """Test fallback parsing when LLM fails."""
        # Setup mocks
        mock_settings_manager_class.return_value.load.return_value = {
            "llm_provider": "openrouter",
            "llm_api_key": "test_key"
        }
        
        mock_client = AsyncMock()
        mock_client.send_query.side_effect = Exception("LLM API error")
        mock_llm_client_class.return_value = mock_client
        
        parser = IntentParser()
        result = await parser.parse("list containers")
        
        # Should fallback to simple parsing
        assert "command_type" in result
        assert result["command_type"] == "container"

    @patch('nlp.intent.SettingsManager')
    @pytest.mark.asyncio
    async def test_parse_no_llm_client(self, mock_settings_manager_class):
        """Test parsing when no LLM client is available."""
        mock_settings_manager_class.return_value.load.side_effect = Exception("No settings")
        
        parser = IntentParser()
        result = await parser.parse("list containers")
        
        # Should use fallback parsing
        assert "command_type" in result
        assert result["command_type"] == "container"

    @patch('nlp.intent.SettingsManager')
    @patch('nlp.intent.LLMClient')
    @pytest.mark.asyncio
    async def test_parse_with_llm_invalid_json(self, mock_llm_client_class, mock_settings_manager_class):
        """Test parsing when LLM returns invalid JSON."""
        # Setup mocks
        mock_settings_manager_class.return_value.load.return_value = {
            "llm_provider": "openrouter",
            "llm_api_key": "test_key"
        }
        
        mock_client = AsyncMock()
        mock_client.send_query.return_value = "invalid json response"
        mock_llm_client_class.return_value = mock_client
        
        parser = IntentParser()
        result = await parser.parse("create container")
        
        # Should fallback to simple parsing
        assert "command_type" in result
        assert result["command_type"] == "unknown"

    def test_fallback_parse_list_containers(self):
        """Test fallback parsing for list containers command."""
        parser = IntentParser()
        result = parser._fallback_parse("list all containers")

        assert result["command_type"] == "container"
        assert result["operation"] == "list"
        assert result["is_docker_command"] is True

    def test_fallback_parse_create_container(self):
        """Test fallback parsing for create container command."""
        parser = IntentParser()
        result = parser._fallback_parse("create nginx container")

        assert result["command_type"] == "container"
        assert result["operation"] == "create"
        assert "create nginx container" in result["parameters"]["raw_command"]

    def test_fallback_parse_stop_container(self):
        """Test fallback parsing for stop container command."""
        parser = IntentParser()
        result = parser._fallback_parse("stop container myapp")

        assert result["command_type"] == "container"
        assert result["operation"] == "stop"
        assert "stop container myapp" in result["parameters"]["raw_command"]

    def test_fallback_parse_remove_container(self):
        """Test fallback parsing for remove container command."""
        parser = IntentParser()
        result = parser._fallback_parse("remove container test123")

        assert result["command_type"] == "container"
        assert result["operation"] == "stop"
        assert "remove container test123" in result["parameters"]["raw_command"]

    def test_fallback_parse_unknown_command(self):
        """Test fallback parsing for unknown command."""
        parser = IntentParser()
        result = parser._fallback_parse("do something weird")

        assert result["command_type"] == "unknown"
        assert result["operation"] == "parse"
        assert "do something weird" in result["parameters"]["raw_command"]

    @patch('nlp.intent.SettingsManager')
    @patch('nlp.intent.LLMClient')
    @pytest.mark.asyncio
    async def test_parse_with_custom_model(self, mock_llm_client_class, mock_settings_manager_class):
        """Test parsing with custom model specified in settings."""
        # Setup mocks with custom model
        mock_settings = {
            "llm_provider": "openrouter",
            "llm_api_key": "test_key",
            "llm_model": "custom/model:latest"
        }
        mock_settings_manager_class.return_value.load.return_value = mock_settings
        
        mock_llm_response = json.dumps({
            "is_docker_command": True,
            "command_type": "container",
            "operation": "start",
            "parameters": {"name": "webapp"},
            "missing_info": [],
            "docker_command": "docker start webapp",
            "explanation": "Start the webapp container"
        })
        
        mock_client = AsyncMock()
        mock_client.send_query.return_value = mock_llm_response
        mock_llm_client_class.return_value = mock_client
        
        parser = IntentParser()
        result = await parser.parse("start webapp container")
        
        # Verify custom model was used
        call_args = mock_client.send_query.call_args
        assert call_args[1]["params"]["model"] == "custom/model:latest"
        
        assert result["command_type"] == "container"
        assert result["operation"] == "start"

    @patch('nlp.intent.SettingsManager')
    @patch('nlp.intent.LLMClient')
    @pytest.mark.asyncio
    async def test_parse_with_default_model(self, mock_llm_client_class, mock_settings_manager_class):
        """Test parsing with default model when none specified."""
        # Setup mocks without model setting
        mock_settings = {
            "llm_provider": "openrouter",
            "llm_api_key": "test_key"
        }
        mock_settings_manager_class.return_value.load.return_value = mock_settings
        
        mock_llm_response = json.dumps({
            "is_docker_command": True,
            "command_type": "container",
            "operation": "restart",
            "parameters": {},
            "missing_info": [],
            "docker_command": "docker restart",
            "explanation": "Restart containers"
        })
        
        mock_client = AsyncMock()
        mock_client.send_query.return_value = mock_llm_response
        mock_llm_client_class.return_value = mock_client
        
        parser = IntentParser()
        result = await parser.parse("restart all containers")
        
        # Verify default model was used
        call_args = mock_client.send_query.call_args
        assert call_args[1]["params"]["model"] == "meta-llama/llama-3.2-3b-instruct:free"
        
        assert result["command_type"] == "container"
        assert result["operation"] == "restart"

    def test_fallback_parse_edge_cases(self):
        """Test fallback parsing for edge cases."""
        parser = IntentParser()

        # Empty command
        result = parser._fallback_parse("")
        assert result["command_type"] == "unknown"
        assert result["operation"] == "parse"

        # Very long command
        long_command = "create a very complex container with many parameters " * 10
        result = parser._fallback_parse(long_command)
        assert result["command_type"] == "container"
        assert result["operation"] == "create"

        # Command with special characters
        result = parser._fallback_parse("list containers @#$%")
        assert result["command_type"] == "container"
        assert result["operation"] == "list"
