import os
from typing import Any, Dict, Optional

import httpx


class LLMClient:
    """
    Abstracts communication with Ollama (local), LiteLLM, and OpenRouter APIs.
    """

    def __init__(
        self,
        provider: str = "ollama",
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        """
        provider: "ollama", "litellm", or "openrouter"
        api_url: URL for the LLM API endpoint
        api_key: API key for LiteLLM, OpenRouter, or remote providers
        """
        self.provider = provider
        # Defaults for each provider
        if provider == "ollama":
            self.api_url = api_url or os.getenv(
                "OLLAMA_API_URL", "http://localhost:11434/api/generate"
            )
            self.api_key = None
        elif provider == "openrouter":
            self.api_url = api_url or os.getenv(
                "OPENROUTER_API_URL", "https://openrouter.ai/api/v1/chat/completions"
            )
            self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        elif provider == "litellm":
            self.api_url = api_url or os.getenv(
                "LLM_API_URL", "http://localhost:8001/generate"
            )
            self.api_key = api_key or os.getenv("LLM_API_KEY")
        else:
            self.api_url = api_url
            self.api_key = api_key

    async def send_query(
        self,
        prompt: str,
        context: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Sends a prompt to the configured LLM provider and returns the response.
        """
        if self.provider == "ollama":
            return await self._send_ollama(prompt, context, params)
        elif self.provider == "litellm":
            return await self._send_litellm(prompt, context, params)
        elif self.provider == "openrouter":
            return await self._send_openrouter(prompt, context, params)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    async def _send_ollama(
        self, prompt: str, context: Optional[str], params: Optional[Dict[str, Any]]
    ) -> str:
        # Ollama expects: model, prompt, and optional parameters
        payload = {
            "model": (params or {}).get("model", "llama2"),
            "prompt": prompt,
        }
        payload.update((params or {}))
        async with httpx.AsyncClient() as client:
            resp = await client.post(self.api_url, json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            # Ollama returns 'response' or 'message' or 'text'
            return data.get("response") or data.get("message") or data.get("text") or ""

    async def _send_litellm(
        self, prompt: str, context: Optional[str], params: Optional[Dict[str, Any]]
    ) -> str:
        payload = {"prompt": prompt, "context": context, "params": params or {}}
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                self.api_url, json=payload, headers=headers, timeout=60
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("response") or data.get("text") or ""

    async def _send_openrouter(
        self, prompt: str, context: Optional[str], params: Optional[Dict[str, Any]]
    ) -> str:
        # OpenRouter expects OpenAI-compatible chat/completions API
        payload = {
            "model": (params or {}).get(
                "model", "meta-llama/llama-3.2-3b-instruct:free"
            ),
            "messages": [
                {
                    "role": "system",
                    "content": context
                    or "You are DockerGPT, an AI assistant specialized in Docker container management.",
                },
                {"role": "user", "content": prompt},
            ],
        }
        payload.update((params or {}))
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://dockerdeployer.com",  # For OpenRouter analytics
            "X-Title": "DockerDeployer",
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                self.api_url, json=payload, headers=headers, timeout=60
            )
            resp.raise_for_status()
            data = resp.json()
            # OpenRouter returns OpenAI-style response
            if "choices" in data and data["choices"]:
                return data["choices"][0].get("message", {}).get("content", "")
            return data.get("response") or data.get("text") or ""

    def set_provider(
        self,
        provider: str,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self.provider = provider
        # Reset API URL and key based on provider
        if provider == "ollama":
            self.api_url = api_url or os.getenv(
                "OLLAMA_API_URL", "http://localhost:11434/api/generate"
            )
            self.api_key = None
        elif provider == "openrouter":
            self.api_url = api_url or os.getenv(
                "OPENROUTER_API_URL", "https://openrouter.ai/api/v1/chat/completions"
            )
            self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        elif provider == "litellm":
            self.api_url = api_url or os.getenv(
                "LLM_API_URL", "http://localhost:8001/generate"
            )
            self.api_key = api_key or os.getenv("LLM_API_KEY")
        else:
            if api_url:
                self.api_url = api_url
            if api_key:
                self.api_key = api_key
