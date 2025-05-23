"""
NLP Intent Parsing Module for DockerDeployer

This module provides real LLM-powered parsing of natural language commands
and extracting actionable intents and parameters for Docker deployment and management.
"""

import asyncio
from typing import Dict, Any, Optional
from llm.client import LLMClient
from llm.prompts.docker_commands import get_parse_command_prompt
from llm.engine.parser import parse_llm_response, ResponseParsingError
from app.config.settings_manager import SettingsManager

class IntentParser:
    def __init__(self):
        """Initialize the intent parser with LLM client."""
        self.settings_manager = SettingsManager()
        self._llm_client = None
        self._initialize_llm_client()

    def _initialize_llm_client(self):
        """Initialize the LLM client with current settings."""
        try:
            settings = self.settings_manager.load()
            self._llm_client = LLMClient(
                provider=settings.get("llm_provider", "ollama"),
                api_url=settings.get("llm_api_url"),
                api_key=settings.get("llm_api_key") or settings.get("openrouter_api_key")
            )
        except Exception as e:
            print(f"Warning: Failed to initialize LLM client: {e}")
            self._llm_client = None

    async def parse(self, command: str) -> Dict[str, Any]:
        """
        Parse a natural language command and extract intent and parameters using LLM.

        Args:
            command (str): The user's natural language input.

        Returns:
            dict: Parsed intent and parameters from LLM.
        """
        if not self._llm_client:
            # Fallback to simple parsing if LLM is not available
            return self._fallback_parse(command)

        try:
            result = await self._parse_with_llm(command)
            return result
        except Exception as e:
            print(f"LLM parsing failed: {e}")
            return self._fallback_parse(command)

    async def _parse_with_llm(self, command: str) -> Dict[str, Any]:
        """Parse command using LLM."""
        # Generate prompt for command parsing
        prompt = get_parse_command_prompt(command)

        # Get model from settings
        settings = self.settings_manager.load()
        model = settings.get("llm_model", "meta-llama/llama-3.2-3b-instruct:free")

        # Send to LLM with model parameter
        response = await self._llm_client.send_query(prompt, params={"model": model})

        # Parse the LLM response
        try:
            parsed_response = parse_llm_response(response, "command")
            return parsed_response
        except ResponseParsingError:
            # If parsing fails, return a structured fallback
            return {
                "is_docker_command": True,
                "command_type": "unknown",
                "operation": "parse",
                "parameters": {"raw_command": command},
                "explanation": f"Processed command: {command}",
                "llm_response": response
            }

    def _fallback_parse(self, command: str) -> Dict[str, Any]:
        """Fallback parsing when LLM is not available."""
        command_lower = command.lower()

        # Simple keyword-based parsing
        if any(word in command_lower for word in ["show", "list", "get", "stats", "status"]):
            if "container" in command_lower:
                return {
                    "is_docker_command": True,
                    "command_type": "container",
                    "operation": "list",
                    "parameters": {"show_stats": "stats" in command_lower},
                    "explanation": "List containers with optional stats"
                }
        elif any(word in command_lower for word in ["deploy", "create", "start", "run"]):
            return {
                "is_docker_command": True,
                "command_type": "container",
                "operation": "create",
                "parameters": {"raw_command": command},
                "explanation": "Deploy or create containers"
            }
        elif any(word in command_lower for word in ["stop", "kill", "remove", "delete"]):
            return {
                "is_docker_command": True,
                "command_type": "container",
                "operation": "stop",
                "parameters": {"raw_command": command},
                "explanation": "Stop or remove containers"
            }

        # Default fallback
        return {
            "is_docker_command": True,
            "command_type": "unknown",
            "operation": "parse",
            "parameters": {"raw_command": command},
            "explanation": f"Processed command: {command} (fallback mode)"
        }
