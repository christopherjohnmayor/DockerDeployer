"""
Parser module for LLM responses related to Docker operations.
This module handles parsing, validation, and transformation of LLM responses
into actionable Docker commands and operations.
"""

import json
import re
from typing import Any, Dict, List, Optional, Tuple, Union


class ResponseParsingError(Exception):
    """Exception raised when parsing an LLM response fails."""

    pass


class DockerCommandParser:
    """
    Parser for LLM responses related to Docker commands.
    Extracts structured data from LLM responses and validates them.
    """

    def __init__(self):
        # Command type to operation mapping for validation
        self.valid_operations = {
            "container": [
                "create",
                "start",
                "stop",
                "restart",
                "remove",
                "list",
                "inspect",
                "logs",
                "exec",
                "stats",
            ],
            "image": ["pull", "build", "list", "remove", "inspect", "tag", "push"],
            "network": ["create", "list", "remove", "inspect", "connect", "disconnect"],
            "volume": ["create", "list", "remove", "inspect"],
            "compose": [
                "up",
                "down",
                "start",
                "stop",
                "restart",
                "logs",
                "ps",
                "build",
            ],
            "system": ["info", "df", "prune", "events"],
        }

    def extract_json_from_response(self, response: str) -> Dict[str, Any]:
        """
        Extract JSON object from LLM response text.

        Args:
            response: The raw text response from the LLM

        Returns:
            Parsed JSON object

        Raises:
            ResponseParsingError: If JSON extraction fails
        """
        # Try to find JSON object in the response using regex
        json_match = re.search(r"({[\s\S]*})", response)
        if not json_match:
            # If no JSON object is found, try to find a code block
            code_block_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", response)
            if code_block_match:
                json_str = code_block_match.group(1)
            else:
                # If no code block is found, use the entire response
                json_str = response
        else:
            json_str = json_match.group(1)

        # Clean up the JSON string
        json_str = json_str.strip()

        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ResponseParsingError(f"Failed to parse JSON from LLM response: {e}")

    def validate_docker_command(
        self, parsed_data: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate that the parsed data represents a valid Docker command.

        Args:
            parsed_data: The parsed JSON data from the LLM response

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if this is a Docker command
        if not parsed_data.get("is_docker_command", False):
            return False, "Not a Docker command"

        # Check command type
        command_type = parsed_data.get("command_type")
        if not command_type or command_type not in self.valid_operations:
            return False, f"Invalid command type: {command_type}"

        # Check operation
        operation = parsed_data.get("operation")
        if not operation or operation not in self.valid_operations.get(
            command_type, []
        ):
            return (
                False,
                f"Invalid operation '{operation}' for command type '{command_type}'",
            )

        # Check parameters
        parameters = parsed_data.get("parameters", {})
        if not isinstance(parameters, dict):
            return False, "Parameters must be an object"

        return True, None

    def parse_response(self, response: str) -> Dict[str, Any]:
        """
        Parse an LLM response into a structured Docker command.

        Args:
            response: The raw text response from the LLM

        Returns:
            Structured Docker command data

        Raises:
            ResponseParsingError: If parsing or validation fails
        """
        try:
            parsed_data = self.extract_json_from_response(response)
            is_valid, error = self.validate_docker_command(parsed_data)

            if not is_valid:
                # If it's explicitly not a Docker command, return as is
                if (
                    "is_docker_command" in parsed_data
                    and parsed_data["is_docker_command"] is False
                ):
                    return parsed_data

                # Otherwise, raise an error
                raise ResponseParsingError(f"Invalid Docker command: {error}")

            return parsed_data
        except Exception as e:
            if not isinstance(e, ResponseParsingError):
                e = ResponseParsingError(f"Failed to parse LLM response: {str(e)}")
            raise e


class ComposeFileParser:
    """
    Parser for docker-compose.yml content generated by LLMs.
    Validates and cleans up the generated compose files.
    """

    def extract_compose_from_response(self, response: str) -> str:
        """
        Extract docker-compose.yml content from LLM response.

        Args:
            response: The raw text response from the LLM

        Returns:
            Extracted docker-compose.yml content

        Raises:
            ResponseParsingError: If extraction fails
        """
        # Try to find a YAML code block
        yaml_match = re.search(r"```(?:yaml|yml)?\s*([\s\S]*?)\s*```", response)
        if yaml_match:
            return yaml_match.group(1).strip()

        # If no code block is found, look for version: and services: patterns
        version_match = re.search(r"(version:[\s\S]*)", response)
        if version_match:
            return version_match.group(1).strip()

        services_match = re.search(r"(services:[\s\S]*)", response)
        if services_match:
            return services_match.group(1).strip()

        raise ResponseParsingError(
            "Could not extract docker-compose.yml content from LLM response"
        )

    def validate_compose_file(self, compose_content: str) -> Tuple[bool, Optional[str]]:
        """
        Perform basic validation of docker-compose.yml content.

        Args:
            compose_content: The docker-compose.yml content

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check for required sections
        if "services:" not in compose_content:
            return False, "Missing 'services:' section in docker-compose.yml"

        # Check for common YAML syntax issues
        if re.search(r"^\s+[^-#\s].*:", compose_content, re.MULTILINE):
            # This is a basic check for indentation issues in YAML
            # A more thorough check would require a YAML parser
            return True, "Warning: Possible indentation issues in YAML"

        return True, None

    def parse_response(self, response: str) -> str:
        """
        Parse an LLM response into a valid docker-compose.yml file.

        Args:
            response: The raw text response from the LLM

        Returns:
            Validated docker-compose.yml content

        Raises:
            ResponseParsingError: If parsing or validation fails
        """
        try:
            compose_content = self.extract_compose_from_response(response)
            is_valid, error = self.validate_compose_file(compose_content)

            if not is_valid:
                raise ResponseParsingError(f"Invalid docker-compose.yml: {error}")

            return compose_content
        except Exception as e:
            if not isinstance(e, ResponseParsingError):
                e = ResponseParsingError(
                    f"Failed to parse docker-compose.yml: {str(e)}"
                )
            raise e


def parse_llm_response(
    response: str, response_type: str = "command"
) -> Union[Dict[str, Any], str]:
    """
    Parse an LLM response based on the expected response type.

    Args:
        response: The raw text response from the LLM
        response_type: Type of response to parse ("command", "compose", "troubleshoot", "explain")

    Returns:
        Parsed response data

    Raises:
        ResponseParsingError: If parsing fails
        ValueError: If response_type is invalid
    """
    if response_type == "command":
        parser = DockerCommandParser()
        return parser.parse_response(response)
    elif response_type == "compose":
        parser = ComposeFileParser()
        return parser.parse_response(response)
    elif response_type in ["troubleshoot", "explain"]:
        # For these types, we just return the raw response
        return response
    else:
        raise ValueError(f"Invalid response type: {response_type}")
