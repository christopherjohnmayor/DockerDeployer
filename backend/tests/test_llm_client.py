"""
Tests for the LLM client module.
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
