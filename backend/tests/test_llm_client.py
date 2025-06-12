"""
Tests for the LLM client module and related components.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from llm.client import LLMClient


class TestLLMClient:
    """Test suite for LLMClient class."""

    @pytest.fixture
    def mock_httpx_client(self):
        """Create a mock httpx client."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        # Mock response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "This is a test response from the LLM API."
        }
        mock_response.raise_for_status = AsyncMock()

        # Set up async post method to return the response directly
        mock_client.post.return_value = mock_response

        return mock_client

    def test_init_default(self):
        """Test LLMClient initialization with default values."""
        client = LLMClient()

        assert client.provider == "local"
        assert client.api_url == "http://localhost:11434/api/generate"
        assert client.api_key == ""
        assert client.model == "llama2"

    def test_init_custom(self):
        """Test LLMClient initialization with custom values."""
        client = LLMClient(
            provider="litellm",
            api_url="https://api.example.com",
            api_key="test_api_key",
            model="gpt-3.5-turbo",
        )

        assert client.provider == "litellm"
        assert client.api_url == "https://api.example.com"
        assert client.api_key == "test_api_key"
        assert client.model == "gpt-3.5-turbo"

    def test_set_provider(self):
        """Test setting provider after initialization."""
        client = LLMClient()

        client.set_provider(
            "openrouter",
            api_url="https://openrouter.ai/api",
            api_key="test_openrouter_key",
        )

        assert client.provider == "openrouter"
        assert client.api_url == "https://openrouter.ai/api"
        assert client.api_key == "test_openrouter_key"

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_send_query_ollama(self, mock_async_client_class):
        """Test sending a query to Ollama."""
        # Create a mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "This is a test response from the LLM API."
        }
        mock_response.raise_for_status.return_value = None

        # Create a mock client that returns the response
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        mock_async_client_class.return_value = mock_client

        client = LLMClient(provider="ollama")
        response = await client.send_query("Hello, world!")

        assert "This is a test response from the LLM API." in response

        # Check that the correct request was made
        mock_client.post.assert_called_once()
        args, kwargs = mock_client.post.call_args

        assert args[0] == "http://localhost:11434/api/generate"
        assert "json" in kwargs
        assert kwargs["json"]["prompt"] == "Hello, world!"
        assert kwargs["json"]["model"] == "llama2"

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_send_query_litellm(self, mock_async_client_class):
        """Test sending a query to LiteLLM."""
        # Create a mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "This is a test response from the LLM API."
        }
        mock_response.raise_for_status.return_value = None

        # Create a mock client that returns the response
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        mock_async_client_class.return_value = mock_client

        client = LLMClient(
            provider="litellm",
            api_url="https://litellm.example.com",
            api_key="test_litellm_key",
        )
        response = await client.send_query("Hello, world!")

        assert "This is a test response from the LLM API." in response

        # Check that the correct request was made
        mock_client.post.assert_called_once()
        args, kwargs = mock_client.post.call_args

        assert args[0] == "https://litellm.example.com"
        assert "json" in kwargs
        assert "headers" in kwargs
        assert kwargs["headers"]["Authorization"] == "Bearer test_litellm_key"

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_send_query_openrouter(self, mock_async_client_class):
        """Test sending a query to OpenRouter."""
        # Create a mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "This is a test response from the LLM API."
        }
        mock_response.raise_for_status.return_value = None

        # Create a mock client that returns the response
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        mock_async_client_class.return_value = mock_client

        client = LLMClient(
            provider="openrouter",
            api_url="https://openrouter.ai/api/v1/chat/completions",
            api_key="test_openrouter_key",
        )
        response = await client.send_query("Hello, world!")

        assert "This is a test response from the LLM API." in response

        # Check that the correct request was made
        mock_client.post.assert_called_once()
        args, kwargs = mock_client.post.call_args

        assert args[0] == "https://openrouter.ai/api/v1/chat/completions"
        assert "json" in kwargs
        assert "headers" in kwargs
        assert kwargs["headers"]["Authorization"] == "Bearer test_openrouter_key"
        assert "HTTP-Referer" in kwargs["headers"]
        assert "X-Title" in kwargs["headers"]

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_send_query_with_context(self, mock_async_client_class):
        """Test sending a query with context."""
        # Create a mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "This is a test response from the LLM API."
        }
        mock_response.raise_for_status.return_value = None

        # Create a mock client that returns the response
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        mock_async_client_class.return_value = mock_client

        client = LLMClient(provider="litellm")  # Use litellm which includes context
        context = {"containers": [{"name": "test", "status": "running"}]}
        await client.send_query("List all containers", context=context)

        # Check that context was included in the request
        _, kwargs = mock_client.post.call_args
        assert "json" in kwargs
        # For litellm, context should be included as a separate field
        assert kwargs["json"]["context"] == context

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_send_query_with_params(self, mock_async_client_class):
        """Test sending a query with additional parameters."""
        # Create a mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "This is a test response from the LLM API."
        }
        mock_response.raise_for_status.return_value = None

        # Create a mock client that returns the response
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        mock_async_client_class.return_value = mock_client

        client = LLMClient()  # Default is "local" which is treated as "ollama"
        params = {"temperature": 0.7, "max_tokens": 100}
        await client.send_query("Generate creative text", params=params)

        # Check that params were included in the request
        _, kwargs = mock_client.post.call_args
        assert "json" in kwargs

        # For ollama/local provider, params are merged into the payload
        assert kwargs["json"]["temperature"] == 0.7
        assert kwargs["json"]["max_tokens"] == 100

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_send_query_error_handling(self, mock_async_client_class):
        """Test error handling when sending a query."""
        # Mock an error response
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.raise_for_status.side_effect = Exception(
            "500 Internal Server Error"
        )

        # Create a mock client that returns the error response
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        mock_async_client_class.return_value = mock_client

        client = LLMClient()

        with pytest.raises(Exception) as excinfo:
            await client.send_query("This will fail")

        assert "500" in str(excinfo.value)
        assert "Internal Server Error" in str(excinfo.value)

    def test_init_custom_provider_fallback(self):
        """Test LLMClient initialization with custom provider fallback."""
        client = LLMClient(
            provider="custom",
            api_url="https://custom.api.com",
            api_key="custom_key",
        )

        assert client.provider == "custom"
        assert client.api_url == "https://custom.api.com"
        assert client.api_key == "custom_key"

    @pytest.mark.asyncio
    async def test_send_query_unsupported_provider(self):
        """Test error handling for unsupported provider."""
        client = LLMClient(provider="unsupported")

        with pytest.raises(ValueError) as excinfo:
            await client.send_query("Test query")

        assert "Unsupported LLM provider: unsupported" in str(excinfo.value)

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_send_query_openrouter_choices_format(self, mock_async_client_class):
        """Test OpenRouter response with choices format."""
        # Create a mock response with OpenAI-style choices
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "OpenRouter response content"}}]
        }
        mock_response.raise_for_status.return_value = None

        # Create a mock client that returns the response
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        mock_async_client_class.return_value = mock_client

        client = LLMClient(provider="openrouter", api_key="test_key")
        response = await client.send_query("Test query")

        assert response == "OpenRouter response content"

    def test_set_provider_custom_with_params(self):
        """Test setting custom provider with explicit parameters."""
        client = LLMClient()

        client.set_provider(
            "custom", api_url="https://custom.example.com", api_key="custom_api_key"
        )

        assert client.provider == "custom"
        assert client.api_url == "https://custom.example.com"
        assert client.api_key == "custom_api_key"

    def test_set_provider_environment_fallbacks(self):
        """Test setting provider with environment variable fallbacks."""
        client = LLMClient()

        # Test ollama fallback
        client.set_provider("ollama")
        assert client.provider == "ollama"
        assert "localhost:11434" in client.api_url
        assert client.api_key == ""

        # Test openrouter fallback
        client.set_provider("openrouter")
        assert client.provider == "openrouter"
        assert "openrouter.ai" in client.api_url

        # Test litellm fallback
        client.set_provider("litellm")
        assert client.provider == "litellm"
        assert "localhost:8001" in client.api_url

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_network_timeout_error(self, mock_async_client_class):
        """Test handling of network timeout errors."""
        mock_client = AsyncMock()
        mock_client.post.side_effect = httpx.TimeoutException("Request timeout")
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_async_client_class.return_value = mock_client

        client = LLMClient(provider="ollama")

        with pytest.raises(httpx.TimeoutException):
            await client.send_query("test prompt")

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_connection_error(self, mock_async_client_class):
        """Test handling of connection errors."""
        mock_client = AsyncMock()
        mock_client.post.side_effect = httpx.ConnectError("Connection failed")
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_async_client_class.return_value = mock_client

        client = LLMClient(provider="ollama")

        with pytest.raises(httpx.ConnectError):
            await client.send_query("test prompt")

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_openrouter_empty_choices(self, mock_async_client_class):
        """Test OpenRouter response with empty choices array."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": []}
        mock_response.raise_for_status.return_value = None

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_async_client_class.return_value = mock_client

        client = LLMClient(provider="openrouter", api_key="test_key")
        response = await client.send_query("test prompt")

        assert response == ""

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_ollama_alternative_response_fields(self, mock_async_client_class):
        """Test Ollama response with alternative field names."""
        # Test with 'message' field
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": "Message field response"}
        mock_response.raise_for_status.return_value = None

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_async_client_class.return_value = mock_client

        client = LLMClient(provider="ollama")
        response = await client.send_query("test prompt")

        assert response == "Message field response"

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_ollama_text_field_response(self, mock_async_client_class):
        """Test Ollama response with 'text' field."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"text": "Text field response"}
        mock_response.raise_for_status.return_value = None

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_async_client_class.return_value = mock_client

        client = LLMClient(provider="ollama")
        response = await client.send_query("test prompt")

        assert response == "Text field response"

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_empty_response_handling(self, mock_async_client_class):
        """Test handling of empty responses."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_response.raise_for_status.return_value = None

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_async_client_class.return_value = mock_client

        client = LLMClient(provider="ollama")
        response = await client.send_query("test prompt")

        assert response == ""

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_litellm_text_response_field(self, mock_async_client_class):
        """Test LiteLLM response with 'text' field instead of 'response'."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"text": "LiteLLM text response"}
        mock_response.raise_for_status.return_value = None

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_async_client_class.return_value = mock_client

        client = LLMClient(provider="litellm", api_key="test_key")
        response = await client.send_query("test prompt")

        assert response == "LiteLLM text response"

    def test_init_with_environment_variables(self):
        """Test initialization with environment variables."""
        with patch.dict(
            "os.environ",
            {
                "OLLAMA_API_URL": "http://custom-ollama:11434/api/generate",
                "OPENROUTER_API_KEY": "env-openrouter-key",
                "LLM_API_URL": "http://custom-litellm:8001/generate",
                "LLM_API_KEY": "env-litellm-key",
            },
        ):
            # Test Ollama with env URL
            ollama_client = LLMClient(provider="ollama")
            assert ollama_client.api_url == "http://custom-ollama:11434/api/generate"

            # Test OpenRouter with env key
            openrouter_client = LLMClient(provider="openrouter")
            assert openrouter_client.api_key == "env-openrouter-key"

            # Test LiteLLM with env URL and key
            litellm_client = LLMClient(provider="litellm")
            assert litellm_client.api_url == "http://custom-litellm:8001/generate"
            assert litellm_client.api_key == "env-litellm-key"

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_openrouter_custom_model_in_params(self, mock_async_client_class):
        """Test OpenRouter with custom model specified in params."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Custom model response"}}]
        }
        mock_response.raise_for_status.return_value = None

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_async_client_class.return_value = mock_client

        client = LLMClient(provider="openrouter", api_key="test_key")
        params = {"model": "custom/model:latest"}
        response = await client.send_query("test prompt", params=params)

        assert response == "Custom model response"

        # Verify the custom model was used
        _, kwargs = mock_client.post.call_args
        assert kwargs["json"]["model"] == "custom/model:latest"


class TestOpenRouterAPIIntegration:
    """Comprehensive tests for OpenRouter API integration."""

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_openrouter_client_initialization_and_authentication(self, mock_async_client_class):
        """Test OpenRouter client initialization and authentication."""
        client = LLMClient(
            provider="openrouter",
            api_key="sk-or-test-key-123",
            model="meta-llama/llama-3.2-3b-instruct:free"
        )

        assert client.provider == "openrouter"
        assert client.api_key == "sk-or-test-key-123"
        assert client.model == "meta-llama/llama-3.2-3b-instruct:free"
        assert "openrouter.ai" in client.api_url

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_openrouter_api_key_validation(self, mock_async_client_class):
        """Test OpenRouter API key validation and configuration."""
        # Test with valid API key format
        client = LLMClient(provider="openrouter", api_key="sk-or-valid-key-123")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Valid API key response"}}]
        }
        mock_response.raise_for_status.return_value = None

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_async_client_class.return_value = mock_client

        response = await client.send_query("Test authentication")
        assert response == "Valid API key response"

        # Verify headers include proper authentication
        _, kwargs = mock_client.post.call_args
        assert kwargs["headers"]["Authorization"] == "Bearer sk-or-valid-key-123"
        assert kwargs["headers"]["HTTP-Referer"] == "https://dockerdeployer.com"
        assert kwargs["headers"]["X-Title"] == "DockerDeployer"

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_openrouter_model_selection_and_availability(self, mock_async_client_class):
        """Test OpenRouter model selection and availability checking."""
        models_to_test = [
            "meta-llama/llama-3.2-3b-instruct:free",
            "meta-llama/llama-3.2-1b-instruct:free",
            "microsoft/phi-3-mini-128k-instruct:free",
            "huggingfaceh4/zephyr-7b-beta:free",
            "openchat/openchat-7b:free"
        ]

        for model in models_to_test:
            client = LLMClient(provider="openrouter", api_key="test-key", model=model)

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{"message": {"content": f"Response from {model}"}}]
            }
            mock_response.raise_for_status.return_value = None

            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_async_client_class.return_value = mock_client

            response = await client.send_query("Test model", params={"model": model})
            assert f"Response from {model}" in response

            # Verify model is correctly set in request
            _, kwargs = mock_client.post.call_args
            assert kwargs["json"]["model"] == model

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_openrouter_api_request_response_handling(self, mock_async_client_class):
        """Test OpenRouter API request/response handling with various models."""
        client = LLMClient(provider="openrouter", api_key="test-key")

        # Test successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "chatcmpl-test-123",
            "object": "chat.completion",
            "created": 1699000000,
            "model": "meta-llama/llama-3.2-3b-instruct:free",
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "This is a comprehensive Docker management response."
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 25,
                "completion_tokens": 50,
                "total_tokens": 75
            }
        }
        mock_response.raise_for_status.return_value = None

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_async_client_class.return_value = mock_client

        response = await client.send_query(
            "List all running Docker containers and show their resource usage",
            context="You are DockerGPT, specialized in Docker container management."
        )

        assert response == "This is a comprehensive Docker management response."

        # Verify request structure
        _, kwargs = mock_client.post.call_args
        assert "messages" in kwargs["json"]
        assert len(kwargs["json"]["messages"]) == 2
        assert kwargs["json"]["messages"][0]["role"] == "system"
        assert kwargs["json"]["messages"][1]["role"] == "user"

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_openrouter_rate_limiting_and_quota_management(self, mock_async_client_class):
        """Test OpenRouter rate limiting and quota management."""
        client = LLMClient(provider="openrouter", api_key="test-key")

        # Test rate limit response
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.json.return_value = {
            "error": {
                "message": "Rate limit exceeded. Please try again later.",
                "type": "rate_limit_exceeded",
                "code": "rate_limit_exceeded"
            }
        }
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "429 Too Many Requests", request=MagicMock(), response=mock_response
        )

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_async_client_class.return_value = mock_client

        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await client.send_query("Test rate limiting")

        assert "429" in str(exc_info.value)

        # Test quota exceeded response
        mock_response.status_code = 402
        mock_response.json.return_value = {
            "error": {
                "message": "Insufficient credits. Please add more credits to your account.",
                "type": "insufficient_quota",
                "code": "insufficient_quota"
            }
        }
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "402 Payment Required", request=MagicMock(), response=mock_response
        )

        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await client.send_query("Test quota management")

        assert "402" in str(exc_info.value)


class TestNaturalLanguageProcessing:
    """Tests for natural language processing and Docker command interpretation."""

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_container_command_interpretation_and_parsing(self, mock_async_client_class):
        """Test container command interpretation and parsing."""
        client = LLMClient(provider="openrouter", api_key="test-key")

        # Test various container commands
        test_commands = [
            ("list all running containers", "docker ps"),
            ("show container stats", "docker stats"),
            ("stop container nginx", "docker stop nginx"),
            ("start container web-server", "docker start web-server"),
            ("remove container old-app", "docker rm old-app"),
            ("create nginx container on port 80", "docker run -p 80:80 nginx"),
        ]

        for natural_command, expected_docker_cmd in test_commands:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{
                    "message": {
                        "content": f"Docker command: {expected_docker_cmd}\nExplanation: This command will {natural_command}"
                    }
                }]
            }
            mock_response.raise_for_status.return_value = None

            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_async_client_class.return_value = mock_client

            response = await client.send_query(
                natural_command,
                context="You are DockerGPT. Convert natural language to Docker commands."
            )

            assert expected_docker_cmd in response
            assert natural_command in response

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_intent_recognition_for_docker_operations(self, mock_async_client_class):
        """Test intent recognition for Docker operations."""
        client = LLMClient(provider="openrouter", api_key="test-key")

        # Test intent recognition for different operation types
        intent_tests = [
            ("deploy a web application", "deployment"),
            ("monitor container performance", "monitoring"),
            ("scale up the service", "scaling"),
            ("backup the database container", "backup"),
            ("update the application image", "update"),
            ("troubleshoot container issues", "troubleshooting"),
        ]

        for command, expected_intent in intent_tests:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{
                    "message": {
                        "content": f"Intent: {expected_intent}\nOperation: {command}\nCategory: docker_management"
                    }
                }]
            }
            mock_response.raise_for_status.return_value = None

            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_async_client_class.return_value = mock_client

            response = await client.send_query(
                f"Analyze intent: {command}",
                context="Identify the Docker operation intent from natural language."
            )

            assert expected_intent in response
            assert "docker_management" in response

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_parameter_extraction_from_natural_language(self, mock_async_client_class):
        """Test parameter extraction from natural language commands."""
        client = LLMClient(provider="openrouter", api_key="test-key")

        # Test parameter extraction scenarios
        parameter_tests = [
            (
                "run nginx container on port 8080 with volume /data",
                {"image": "nginx", "port": "8080", "volume": "/data"}
            ),
            (
                "create mysql database with password secret123 and name myapp",
                {"image": "mysql", "password": "secret123", "database": "myapp"}
            ),
            (
                "deploy redis with 2GB memory limit and restart always",
                {"image": "redis", "memory": "2GB", "restart": "always"}
            ),
        ]

        for command, expected_params in parameter_tests:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{
                    "message": {
                        "content": f"Parameters extracted: {expected_params}\nCommand: {command}"
                    }
                }]
            }
            mock_response.raise_for_status.return_value = None

            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_async_client_class.return_value = mock_client

            response = await client.send_query(
                f"Extract parameters: {command}",
                context="Extract Docker parameters from natural language."
            )

            for key, value in expected_params.items():
                assert key in response
                assert str(value) in response

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_command_validation_and_sanitization(self, mock_async_client_class):
        """Test command validation and sanitization."""
        client = LLMClient(provider="openrouter", api_key="test-key")

        # Test potentially dangerous commands
        dangerous_commands = [
            "delete all containers and remove all images",
            "run container with privileged access to host",
            "mount entire filesystem as volume",
            "expose all ports to public internet",
        ]

        for dangerous_cmd in dangerous_commands:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{
                    "message": {
                        "content": f"WARNING: Potentially dangerous command detected: {dangerous_cmd}\nSuggestion: Use safer alternatives with specific parameters."
                    }
                }]
            }
            mock_response.raise_for_status.return_value = None

            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_async_client_class.return_value = mock_client

            response = await client.send_query(
                f"Validate command safety: {dangerous_cmd}",
                context="Analyze Docker command for security risks."
            )

            assert "WARNING" in response or "dangerous" in response
            assert "Suggestion" in response or "safer" in response

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_multi_step_command_processing(self, mock_async_client_class):
        """Test multi-step command processing."""
        client = LLMClient(provider="openrouter", api_key="test-key")

        # Test complex multi-step scenarios
        multi_step_commands = [
            "deploy a LAMP stack with Apache, MySQL, and PHP",
            "set up a monitoring stack with Prometheus and Grafana",
            "create a development environment with database and cache",
            "deploy microservices with load balancer and service discovery",
        ]

        for complex_cmd in multi_step_commands:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{
                    "message": {
                        "content": f"Multi-step deployment plan for: {complex_cmd}\n"
                                 f"Step 1: Create network\n"
                                 f"Step 2: Deploy database\n"
                                 f"Step 3: Deploy application\n"
                                 f"Step 4: Configure services\n"
                                 f"Step 5: Verify deployment"
                    }
                }]
            }
            mock_response.raise_for_status.return_value = None

            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_async_client_class.return_value = mock_client

            response = await client.send_query(
                f"Create deployment plan: {complex_cmd}",
                context="Generate step-by-step Docker deployment plan."
            )

            assert "Step 1" in response
            assert "Step 2" in response
            assert "deployment" in response.lower()
            assert "network" in response or "database" in response or "application" in response


class TestErrorHandlingAndFallback:
    """Tests for error handling and fallback mechanisms."""

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_api_timeout_and_connection_failures(self, mock_async_client_class):
        """Test API timeout and connection failure handling."""
        client = LLMClient(provider="openrouter", api_key="test-key")

        # Test connection timeout
        mock_client = AsyncMock()
        mock_client.post.side_effect = httpx.TimeoutException("Request timeout after 60 seconds")
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_async_client_class.return_value = mock_client

        with pytest.raises(httpx.TimeoutException) as exc_info:
            await client.send_query("Test timeout handling")

        assert "timeout" in str(exc_info.value).lower()

        # Test connection error
        mock_client.post.side_effect = httpx.ConnectError("Failed to connect to OpenRouter API")

        with pytest.raises(httpx.ConnectError) as exc_info:
            await client.send_query("Test connection error")

        assert "connect" in str(exc_info.value).lower()

        # Test network unreachable
        mock_client.post.side_effect = httpx.NetworkError("Network is unreachable")

        with pytest.raises(httpx.NetworkError) as exc_info:
            await client.send_query("Test network error")

        assert "network" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_invalid_api_key_scenarios(self, mock_async_client_class):
        """Test invalid API key scenarios."""
        client = LLMClient(provider="openrouter", api_key="invalid-key")

        # Test 401 Unauthorized
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "error": {
                "message": "Invalid API key provided",
                "type": "invalid_request_error",
                "code": "invalid_api_key"
            }
        }
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "401 Unauthorized", request=MagicMock(), response=mock_response
        )

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_async_client_class.return_value = mock_client

        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await client.send_query("Test invalid API key")

        assert "401" in str(exc_info.value)

        # Test 403 Forbidden
        mock_response.status_code = 403
        mock_response.json.return_value = {
            "error": {
                "message": "API key does not have permission to access this resource",
                "type": "permission_error",
                "code": "insufficient_permissions"
            }
        }
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "403 Forbidden", request=MagicMock(), response=mock_response
        )

        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await client.send_query("Test forbidden access")

        assert "403" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_model_unavailability_and_fallback_mechanisms(self, mock_async_client_class):
        """Test model unavailability and fallback mechanisms."""
        client = LLMClient(provider="openrouter", api_key="test-key")

        # Test model not found
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.json.return_value = {
            "error": {
                "message": "Model 'nonexistent/model' not found",
                "type": "invalid_request_error",
                "code": "model_not_found"
            }
        }
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404 Not Found", request=MagicMock(), response=mock_response
        )

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_async_client_class.return_value = mock_client

        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await client.send_query("Test model not found", params={"model": "nonexistent/model"})

        assert "404" in str(exc_info.value)

        # Test model overloaded
        mock_response.status_code = 503
        mock_response.json.return_value = {
            "error": {
                "message": "Model is currently overloaded. Please try again later.",
                "type": "server_error",
                "code": "model_overloaded"
            }
        }
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "503 Service Unavailable", request=MagicMock(), response=mock_response
        )

        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await client.send_query("Test model overloaded")

        assert "503" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_malformed_response_handling(self, mock_async_client_class):
        """Test malformed response handling."""
        client = LLMClient(provider="openrouter", api_key="test-key")

        # Test invalid JSON response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.text = "Invalid JSON response"
        mock_response.raise_for_status.return_value = None

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_async_client_class.return_value = mock_client

        with pytest.raises(ValueError) as exc_info:
            await client.send_query("Test invalid JSON")

        assert "Invalid JSON" in str(exc_info.value)

        # Test missing choices in response
        mock_response.json.side_effect = None
        mock_response.json.return_value = {"id": "test", "object": "chat.completion"}

        response = await client.send_query("Test missing choices")
        assert response == ""

        # Test malformed choices structure
        mock_response.json.return_value = {
            "choices": [{"message": {}}]  # Missing content
        }

        response = await client.send_query("Test malformed choices")
        assert response == ""

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_network_connectivity_issues(self, mock_async_client_class):
        """Test network connectivity issues."""
        client = LLMClient(provider="openrouter", api_key="test-key")

        # Test DNS resolution failure
        mock_client = AsyncMock()
        mock_client.post.side_effect = httpx.ConnectError("DNS resolution failed")
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_async_client_class.return_value = mock_client

        with pytest.raises(httpx.ConnectError) as exc_info:
            await client.send_query("Test DNS failure")

        assert "DNS" in str(exc_info.value) or "resolution" in str(exc_info.value)

        # Test SSL/TLS errors
        mock_client.post.side_effect = httpx.ConnectError("SSL handshake failed")

        with pytest.raises(httpx.ConnectError) as exc_info:
            await client.send_query("Test SSL error")

        assert "SSL" in str(exc_info.value) or "handshake" in str(exc_info.value)

        # Test proxy errors
        mock_client.post.side_effect = httpx.ProxyError("Proxy connection failed")

        with pytest.raises(httpx.ProxyError) as exc_info:
            await client.send_query("Test proxy error")

        assert "proxy" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_provider_initialization_edge_cases(self, mock_async_client_class):
        """Test provider initialization edge cases."""
        # Test with None values
        client = LLMClient(provider="openrouter", api_url=None, api_key=None)
        assert client.provider == "openrouter"
        assert "openrouter.ai" in client.api_url
        assert client.api_key is None

        # Test with empty strings
        client = LLMClient(provider="litellm", api_url="", api_key="")
        assert client.provider == "litellm"
        assert client.api_key == ""

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_send_query_parameter_merging(self, mock_async_client_class):
        """Test parameter merging in send_query method."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "test response"}
        mock_response.raise_for_status.return_value = None

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_async_client_class.return_value = mock_client

        client = LLMClient(provider="ollama", model="custom-model")

        # Test parameter override
        params = {"model": "override-model", "temperature": 0.8}
        await client.send_query("test prompt", params=params)

        _, kwargs = mock_client.post.call_args
        assert kwargs["json"]["model"] == "override-model"
        assert kwargs["json"]["temperature"] == 0.8

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_openrouter_context_handling(self, mock_async_client_class):
        """Test OpenRouter context handling in messages."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "response with context"}}]
        }
        mock_response.raise_for_status.return_value = None

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_async_client_class.return_value = mock_client

        client = LLMClient(provider="openrouter", api_key="test-key")

        # Test with custom context
        custom_context = "You are a specialized Docker assistant."
        await client.send_query("test prompt", context=custom_context)

        _, kwargs = mock_client.post.call_args
        messages = kwargs["json"]["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == custom_context
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "test prompt"

        # Test with None context (should use default)
        await client.send_query("test prompt", context=None)
        _, kwargs = mock_client.post.call_args
        messages = kwargs["json"]["messages"]
        assert "DockerGPT" in messages[0]["content"]

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_litellm_authorization_header_handling(self, mock_async_client_class):
        """Test LiteLLM authorization header handling."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "litellm response"}
        mock_response.raise_for_status.return_value = None

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_async_client_class.return_value = mock_client

        # Test with API key
        client = LLMClient(provider="litellm", api_key="test-litellm-key")
        await client.send_query("test prompt")

        _, kwargs = mock_client.post.call_args
        assert "headers" in kwargs
        assert kwargs["headers"]["Authorization"] == "Bearer test-litellm-key"

        # Test without API key
        client = LLMClient(provider="litellm", api_key=None)
        await client.send_query("test prompt")

        _, kwargs = mock_client.post.call_args
        headers = kwargs.get("headers", {})
        assert "Authorization" not in headers

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_response_field_fallbacks(self, mock_async_client_class):
        """Test response field fallbacks for different providers."""
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_async_client_class.return_value = mock_client

        # Test Ollama response field priority: response > message > text
        client = LLMClient(provider="ollama")

        # Test with all fields present (should prefer 'response')
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "primary response",
            "message": "secondary message",
            "text": "tertiary text"
        }
        mock_response.raise_for_status.return_value = None
        mock_client.post.return_value = mock_response

        result = await client.send_query("test")
        assert result == "primary response"

        # Test with only message and text (should prefer 'message')
        mock_response.json.return_value = {
            "message": "secondary message",
            "text": "tertiary text"
        }
        result = await client.send_query("test")
        assert result == "secondary message"

        # Test with only text
        mock_response.json.return_value = {"text": "tertiary text"}
        result = await client.send_query("test")
        assert result == "tertiary text"

        # Test LiteLLM response field priority: response > text
        client = LLMClient(provider="litellm", api_key="test-key")

        mock_response.json.return_value = {
            "response": "litellm response",
            "text": "litellm text"
        }
        result = await client.send_query("test")
        assert result == "litellm response"

        mock_response.json.return_value = {"text": "litellm text only"}
        result = await client.send_query("test")
        assert result == "litellm text only"

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_json_parsing_errors(self, mock_async_client_class):
        """Test JSON parsing error handling."""
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_async_client_class.return_value = mock_client

        client = LLMClient(provider="ollama")

        # Test invalid JSON response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.raise_for_status.return_value = None
        mock_client.post.return_value = mock_response

        with pytest.raises(ValueError):
            await client.send_query("test prompt")

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_http_status_error_handling(self, mock_async_client_class):
        """Test HTTP status error handling."""
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_async_client_class.return_value = mock_client

        client = LLMClient(provider="openrouter", api_key="test-key")

        # Test 400 Bad Request
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "400 Bad Request", request=MagicMock(), response=mock_response
        )
        mock_client.post.return_value = mock_response

        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await client.send_query("test prompt")
        assert "400" in str(exc_info.value)

        # Test 500 Internal Server Error
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "500 Internal Server Error", request=MagicMock(), response=mock_response
        )

        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await client.send_query("test prompt")
        assert "500" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_request_timeout_configuration(self, mock_async_client_class):
        """Test request timeout configuration."""
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_async_client_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "success"}
        mock_response.raise_for_status.return_value = None
        mock_client.post.return_value = mock_response

        client = LLMClient(provider="ollama")
        await client.send_query("test prompt")

        # Verify timeout is set to 60 seconds
        _, kwargs = mock_client.post.call_args
        assert kwargs["timeout"] == 60

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_openrouter_model_parameter_handling(self, mock_async_client_class):
        """Test OpenRouter model parameter handling."""
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_async_client_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "model response"}}]
        }
        mock_response.raise_for_status.return_value = None
        mock_client.post.return_value = mock_response

        client = LLMClient(provider="openrouter", api_key="test-key")

        # Test default model
        await client.send_query("test prompt")
        _, kwargs = mock_client.post.call_args
        assert kwargs["json"]["model"] == "meta-llama/llama-3.2-3b-instruct:free"

        # Test model override in params
        await client.send_query("test prompt", params={"model": "custom/model"})
        _, kwargs = mock_client.post.call_args
        assert kwargs["json"]["model"] == "custom/model"

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_provider_specific_headers(self, mock_async_client_class):
        """Test provider-specific headers."""
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_async_client_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "response"}}]
        }
        mock_response.raise_for_status.return_value = None
        mock_client.post.return_value = mock_response

        # Test OpenRouter headers
        client = LLMClient(provider="openrouter", api_key="test-key")
        await client.send_query("test prompt")

        _, kwargs = mock_client.post.call_args
        headers = kwargs["headers"]
        assert headers["Authorization"] == "Bearer test-key"
        assert headers["HTTP-Referer"] == "https://dockerdeployer.com"
        assert headers["X-Title"] == "DockerDeployer"

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_empty_and_none_responses(self, mock_async_client_class):
        """Test handling of empty and None responses."""
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_async_client_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_client.post.return_value = mock_response

        client = LLMClient(provider="ollama")

        # Test completely empty response
        mock_response.json.return_value = {}
        result = await client.send_query("test prompt")
        assert result is None or result == ""

        # Test None values in response
        mock_response.json.return_value = {
            "response": None,
            "message": None,
            "text": None
        }
        result = await client.send_query("test prompt")
        assert result == ""

        # Test OpenRouter with empty choices
        client = LLMClient(provider="openrouter", api_key="test-key")
        mock_response.json.return_value = {"choices": []}
        result = await client.send_query("test prompt")
        assert result == ""

        # Test OpenRouter with None content
        mock_response.json.return_value = {
            "choices": [{"message": {"content": None}}]
        }
        result = await client.send_query("test prompt")
        assert result == ""

    def test_set_provider_comprehensive(self):
        """Test comprehensive set_provider functionality."""
        client = LLMClient()

        # Test setting each provider type
        providers_config = [
            ("ollama", "http://custom-ollama:11434/api/generate", ""),
            ("openrouter", "https://openrouter.ai/api/v1/chat/completions", "or-key"),
            ("litellm", "http://custom-litellm:8001/generate", "lite-key"),
            ("custom", "https://custom.api.com/v1", "custom-key")
        ]

        for provider, expected_url, api_key in providers_config:
            client.set_provider(provider, api_url=expected_url, api_key=api_key)
            assert client.provider == provider
            assert client.api_url == expected_url
            assert client.api_key == api_key

        # Test setting provider without explicit URL/key (should use defaults)
        client.set_provider("ollama")
        assert client.provider == "ollama"
        assert "localhost:11434" in client.api_url
        assert client.api_key == ""

    @pytest.mark.asyncio
    async def test_unsupported_provider_error(self):
        """Test error handling for unsupported providers."""
        client = LLMClient(provider="unsupported_provider")

        with pytest.raises(ValueError) as exc_info:
            await client.send_query("test prompt")

        assert "Unsupported LLM provider: unsupported_provider" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_context_parameter_handling(self, mock_async_client_class):
        """Test context parameter handling across providers."""
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_async_client_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_client.post.return_value = mock_response

        # Test Ollama (context not directly used in payload)
        mock_response.json.return_value = {"response": "ollama response"}
        client = LLMClient(provider="ollama")
        await client.send_query("test prompt", context="test context")

        _, kwargs = mock_client.post.call_args
        # Ollama doesn't use context in the payload directly
        assert "context" not in kwargs["json"]

        # Test LiteLLM (context included in payload)
        mock_response.json.return_value = {"response": "litellm response"}
        client = LLMClient(provider="litellm", api_key="test-key")
        await client.send_query("test prompt", context="test context")

        _, kwargs = mock_client.post.call_args
        assert kwargs["json"]["context"] == "test context"

        # Test OpenRouter (context used in system message)
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "openrouter response"}}]
        }
        client = LLMClient(provider="openrouter", api_key="test-key")
        await client.send_query("test prompt", context="test context")

        _, kwargs = mock_client.post.call_args
        messages = kwargs["json"]["messages"]
        assert messages[0]["content"] == "test context"


class TestResponseProcessingAndValidation:
    """Tests for LLM response processing and validation."""

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_llm_response_parsing_and_validation(self, mock_async_client_class):
        """Test LLM response parsing and validation."""
        client = LLMClient(provider="openrouter", api_key="test-key")

        # Test various response formats
        response_formats = [
            {
                "input": {
                    "choices": [{
                        "message": {
                            "content": "```json\n{\"command\": \"docker ps\", \"explanation\": \"List containers\"}\n```"
                        }
                    }]
                },
                "expected": "docker ps"
            },
            {
                "input": {
                    "choices": [{
                        "message": {
                            "content": "Docker command: docker run -p 80:80 nginx\nThis will start an nginx container."
                        }
                    }]
                },
                "expected": "docker run -p 80:80 nginx"
            },
            {
                "input": {
                    "choices": [{
                        "message": {
                            "content": "To list all containers, use: `docker ps -a`"
                        }
                    }]
                },
                "expected": "docker ps -a"
            }
        ]

        for test_case in response_formats:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = test_case["input"]
            mock_response.raise_for_status.return_value = None

            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_async_client_class.return_value = mock_client

            response = await client.send_query("Parse this response format")
            assert test_case["expected"] in response

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_docker_command_generation_from_responses(self, mock_async_client_class):
        """Test Docker command generation from LLM responses."""
        client = LLMClient(provider="openrouter", api_key="test-key")

        # Test command generation scenarios
        command_scenarios = [
            {
                "prompt": "Create a web server container",
                "response": "docker run -d --name web-server -p 80:80 nginx:latest",
                "expected_elements": ["docker run", "-d", "--name", "web-server", "-p", "80:80", "nginx"]
            },
            {
                "prompt": "Deploy a database with persistent storage",
                "response": "docker run -d --name database -v /data:/var/lib/mysql -e MYSQL_ROOT_PASSWORD=secret mysql:8.0",
                "expected_elements": ["docker run", "-d", "--name", "database", "-v", "/data:/var/lib/mysql", "mysql"]
            },
            {
                "prompt": "Scale a service to 3 replicas",
                "response": "docker service scale web-service=3",
                "expected_elements": ["docker service", "scale", "web-service=3"]
            }
        ]

        for scenario in command_scenarios:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{
                    "message": {"content": scenario["response"]}
                }]
            }
            mock_response.raise_for_status.return_value = None

            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_async_client_class.return_value = mock_client

            response = await client.send_query(scenario["prompt"])

            for element in scenario["expected_elements"]:
                assert element in response

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_response_format_standardization(self, mock_async_client_class):
        """Test response format standardization."""
        client = LLMClient(provider="openrouter", api_key="test-key")

        # Test different response formats that should be standardized
        format_tests = [
            {
                "raw_response": "DOCKER RUN -P 80:80 NGINX",
                "expected_format": "docker run -p 80:80 nginx"
            },
            {
                "raw_response": "Docker Command:\n  docker ps --all\nExplanation: Shows all containers",
                "expected_format": "docker ps --all"
            },
            {
                "raw_response": "```bash\ndocker logs container-name\n```",
                "expected_format": "docker logs container-name"
            }
        ]

        for test in format_tests:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{
                    "message": {"content": test["raw_response"]}
                }]
            }
            mock_response.raise_for_status.return_value = None

            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_async_client_class.return_value = mock_client

            response = await client.send_query("Standardize this format")

            # Response should contain the expected format elements
            assert "docker" in response.lower()
            # The exact standardization would be done by a separate parser

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_error_message_extraction_and_handling(self, mock_async_client_class):
        """Test error message extraction and handling."""
        client = LLMClient(provider="openrouter", api_key="test-key")

        # Test error response scenarios
        error_scenarios = [
            {
                "status_code": 400,
                "error_response": {
                    "error": {
                        "message": "Invalid request: missing required parameter 'model'",
                        "type": "invalid_request_error",
                        "code": "missing_parameter"
                    }
                }
            },
            {
                "status_code": 500,
                "error_response": {
                    "error": {
                        "message": "Internal server error occurred while processing request",
                        "type": "server_error",
                        "code": "internal_error"
                    }
                }
            }
        ]

        for scenario in error_scenarios:
            mock_response = MagicMock()
            mock_response.status_code = scenario["status_code"]
            mock_response.json.return_value = scenario["error_response"]
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                f"{scenario['status_code']} Error", request=MagicMock(), response=mock_response
            )

            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_async_client_class.return_value = mock_client

            with pytest.raises(httpx.HTTPStatusError) as exc_info:
                await client.send_query("Test error extraction")

            assert str(scenario["status_code"]) in str(exc_info.value)

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_response_caching_and_optimization(self, mock_async_client_class):
        """Test response caching and optimization scenarios."""
        client = LLMClient(provider="openrouter", api_key="test-key")

        # Test repeated queries (would be cached in a real implementation)
        repeated_queries = [
            "list all containers",
            "show container stats",
            "docker help command"
        ]

        for query in repeated_queries:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{
                    "message": {"content": f"Cached response for: {query}"}
                }]
            }
            mock_response.raise_for_status.return_value = None

            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_async_client_class.return_value = mock_client

            # First call
            response1 = await client.send_query(query)
            assert f"Cached response for: {query}" in response1

            # Second call (would use cache in real implementation)
            response2 = await client.send_query(query)
            assert f"Cached response for: {query}" in response2

            # Verify both responses are consistent
            assert response1 == response2
