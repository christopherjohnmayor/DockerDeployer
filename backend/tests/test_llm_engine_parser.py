"""
Tests for the LLM Engine Parser module.
"""

import json
import pytest
import yaml

from llm.engine.parser import (
    DockerCommandParser,
    ComposeFileParser,
    ResponseParsingError,
    parse_llm_response
)


class TestDockerCommandParser:
    """Test suite for DockerCommandParser class."""

    @pytest.fixture
    def parser(self):
        """Create a DockerCommandParser instance."""
        return DockerCommandParser()

    def test_init(self, parser):
        """Test DockerCommandParser initialization."""
        assert parser.valid_operations is not None
        assert "container" in parser.valid_operations
        assert "image" in parser.valid_operations
        assert "network" in parser.valid_operations
        assert "volume" in parser.valid_operations
        assert "compose" in parser.valid_operations
        assert "system" in parser.valid_operations

    def test_extract_json_from_response_valid_json(self, parser):
        """Test extracting valid JSON from response."""
        response = '''
        Here is the parsed command:
        ```json
        {
            "is_docker_command": true,
            "command_type": "container",
            "operation": "list"
        }
        ```
        '''
        
        result = parser.extract_json_from_response(response)
        assert result["is_docker_command"] is True
        assert result["command_type"] == "container"
        assert result["operation"] == "list"

    def test_extract_json_from_response_no_code_block(self, parser):
        """Test extracting JSON without code block."""
        response = '''
        {
            "is_docker_command": true,
            "command_type": "image",
            "operation": "pull"
        }
        '''
        
        result = parser.extract_json_from_response(response)
        assert result["is_docker_command"] is True
        assert result["command_type"] == "image"
        assert result["operation"] == "pull"

    def test_extract_json_from_response_invalid_json(self, parser):
        """Test extracting invalid JSON raises error."""
        response = "This is not valid JSON at all"
        
        with pytest.raises(ResponseParsingError) as excinfo:
            parser.extract_json_from_response(response)
        
        assert "Failed to parse JSON" in str(excinfo.value)

    def test_validate_docker_command_valid(self, parser):
        """Test validation of valid Docker command."""
        command_data = {
            "is_docker_command": True,
            "command_type": "container",
            "operation": "start",
            "parameters": {"name": "webapp"}
        }
        
        is_valid, error = parser.validate_docker_command(command_data)
        assert is_valid is True
        assert error is None

    def test_validate_docker_command_not_docker(self, parser):
        """Test validation of non-Docker command."""
        command_data = {
            "is_docker_command": False,
            "command_type": "unknown",
            "operation": "unknown"
        }
        
        is_valid, error = parser.validate_docker_command(command_data)
        assert is_valid is True  # Non-Docker commands are valid
        assert error is None

    def test_validate_docker_command_missing_fields(self, parser):
        """Test validation with missing required fields."""
        command_data = {
            "is_docker_command": True
            # Missing command_type and operation
        }
        
        is_valid, error = parser.validate_docker_command(command_data)
        assert is_valid is False
        assert "Missing required field" in error

    def test_validate_docker_command_invalid_type(self, parser):
        """Test validation with invalid command type."""
        command_data = {
            "is_docker_command": True,
            "command_type": "invalid_type",
            "operation": "start"
        }
        
        is_valid, error = parser.validate_docker_command(command_data)
        assert is_valid is False
        assert "Invalid command type" in error

    def test_validate_docker_command_invalid_operation(self, parser):
        """Test validation with invalid operation."""
        command_data = {
            "is_docker_command": True,
            "command_type": "container",
            "operation": "invalid_operation"
        }
        
        is_valid, error = parser.validate_docker_command(command_data)
        assert is_valid is False
        assert "Invalid operation" in error

    def test_validate_docker_command_invalid_parameters(self, parser):
        """Test validation with invalid parameters type."""
        command_data = {
            "is_docker_command": True,
            "command_type": "container",
            "operation": "start",
            "parameters": "not_a_dict"
        }
        
        is_valid, error = parser.validate_docker_command(command_data)
        assert is_valid is False
        assert "Parameters must be an object" in error

    def test_parse_response_valid(self, parser):
        """Test parsing valid response."""
        response = json.dumps({
            "is_docker_command": True,
            "command_type": "container",
            "operation": "stop",
            "parameters": {"name": "myapp"},
            "docker_command": "docker stop myapp"
        })
        
        result = parser.parse_response(response)
        assert result["command_type"] == "container"
        assert result["operation"] == "stop"
        assert result["parameters"]["name"] == "myapp"

    def test_parse_response_non_docker_command(self, parser):
        """Test parsing non-Docker command."""
        response = json.dumps({
            "is_docker_command": False,
            "command_type": "unknown",
            "operation": "unknown",
            "explanation": "This is not a Docker command"
        })
        
        result = parser.parse_response(response)
        assert result["is_docker_command"] is False
        assert result["explanation"] == "This is not a Docker command"

    def test_parse_response_invalid(self, parser):
        """Test parsing invalid response raises error."""
        response = json.dumps({
            "is_docker_command": True,
            "command_type": "invalid",
            "operation": "invalid"
        })
        
        with pytest.raises(ResponseParsingError) as excinfo:
            parser.parse_response(response)
        
        assert "Invalid Docker command" in str(excinfo.value)

    def test_parse_response_malformed_json(self, parser):
        """Test parsing malformed JSON raises error."""
        response = "{ invalid json }"
        
        with pytest.raises(ResponseParsingError) as excinfo:
            parser.parse_response(response)
        
        assert "Failed to parse JSON from LLM response" in str(excinfo.value)

    def test_all_valid_operations_coverage(self, parser):
        """Test that all valid operations are properly defined."""
        # Test container operations
        for operation in ["create", "start", "stop", "restart", "remove", "list", "inspect", "logs", "exec", "stats"]:
            command_data = {
                "is_docker_command": True,
                "command_type": "container",
                "operation": operation,
                "parameters": {}
            }
            is_valid, error = parser.validate_docker_command(command_data)
            assert is_valid is True, f"Container operation '{operation}' should be valid"

        # Test image operations
        for operation in ["pull", "build", "list", "remove", "inspect", "tag", "push"]:
            command_data = {
                "is_docker_command": True,
                "command_type": "image",
                "operation": operation,
                "parameters": {}
            }
            is_valid, error = parser.validate_docker_command(command_data)
            assert is_valid is True, f"Image operation '{operation}' should be valid"

        # Test network operations
        for operation in ["create", "list", "remove", "inspect", "connect", "disconnect"]:
            command_data = {
                "is_docker_command": True,
                "command_type": "network",
                "operation": operation,
                "parameters": {}
            }
            is_valid, error = parser.validate_docker_command(command_data)
            assert is_valid is True, f"Network operation '{operation}' should be valid"

        # Test volume operations
        for operation in ["create", "list", "remove", "inspect"]:
            command_data = {
                "is_docker_command": True,
                "command_type": "volume",
                "operation": operation,
                "parameters": {}
            }
            is_valid, error = parser.validate_docker_command(command_data)
            assert is_valid is True, f"Volume operation '{operation}' should be valid"

        # Test compose operations
        for operation in ["up", "down", "start", "stop", "restart", "logs", "ps", "build"]:
            command_data = {
                "is_docker_command": True,
                "command_type": "compose",
                "operation": operation,
                "parameters": {}
            }
            is_valid, error = parser.validate_docker_command(command_data)
            assert is_valid is True, f"Compose operation '{operation}' should be valid"

        # Test system operations
        for operation in ["info", "df", "prune", "events"]:
            command_data = {
                "is_docker_command": True,
                "command_type": "system",
                "operation": operation,
                "parameters": {}
            }
            is_valid, error = parser.validate_docker_command(command_data)
            assert is_valid is True, f"System operation '{operation}' should be valid"


class TestComposeFileParser:
    """Test suite for ComposeFileParser class."""

    @pytest.fixture
    def parser(self):
        """Create a ComposeFileParser instance."""
        return ComposeFileParser()

    def test_init(self, parser):
        """Test ComposeFileParser initialization."""
        assert parser is not None

    def test_extract_compose_from_response_yaml_block(self, parser):
        """Test extracting compose content from YAML code block."""
        response = '''
        Here is your docker-compose.yml:
        ```yaml
        version: '3.8'
        services:
          web:
            image: nginx
            ports:
              - "80:80"
        ```
        '''
        
        result = parser.extract_compose_from_response(response)
        assert "version: '3.8'" in result
        assert "services:" in result
        assert "nginx" in result

    def test_extract_compose_from_response_yml_block(self, parser):
        """Test extracting compose content from yml code block."""
        response = '''
        ```yml
        version: '3.8'
        services:
          app:
            image: node:16
        ```
        '''
        
        result = parser.extract_compose_from_response(response)
        assert "version: '3.8'" in result
        assert "node:16" in result

    def test_extract_compose_from_response_no_block(self, parser):
        """Test extracting compose content without code block."""
        response = '''
        version: '3.8'
        services:
          db:
            image: postgres:13
            environment:
              POSTGRES_DB: mydb
        '''
        
        result = parser.extract_compose_from_response(response)
        assert "version: '3.8'" in result
        assert "postgres:13" in result

    def test_extract_compose_from_response_services_only(self, parser):
        """Test extracting compose content with services only."""
        response = '''
        services:
          redis:
            image: redis:alpine
            ports:
              - "6379:6379"
        '''
        
        result = parser.extract_compose_from_response(response)
        assert "services:" in result
        assert "redis:alpine" in result

    def test_extract_compose_from_response_no_match(self, parser):
        """Test extracting when no compose content found."""
        response = "This response contains no docker-compose content"
        
        with pytest.raises(ResponseParsingError) as excinfo:
            parser.extract_compose_from_response(response)
        
        assert "No docker-compose.yml content found" in str(excinfo.value)

    def test_validate_compose_file_valid(self, parser):
        """Test validation of valid compose file."""
        compose_content = '''
        version: '3.8'
        services:
          web:
            image: nginx
            ports:
              - "80:80"
        '''
        
        is_valid, error = parser.validate_compose_file(compose_content)
        assert is_valid is True
        assert error is None

    def test_validate_compose_file_invalid_yaml(self, parser):
        """Test validation of invalid YAML."""
        compose_content = '''
        version: '3.8'
        services:
          web:
            image: nginx
            ports:
              - "80:80"
            invalid_yaml: [unclosed
        '''
        
        is_valid, error = parser.validate_compose_file(compose_content)
        assert is_valid is False
        assert "Invalid YAML" in error

    def test_validate_compose_file_missing_services(self, parser):
        """Test validation of compose file without services."""
        compose_content = '''
        version: '3.8'
        networks:
          default:
            driver: bridge
        '''
        
        is_valid, error = parser.validate_compose_file(compose_content)
        assert is_valid is False
        assert "No services defined" in error

    def test_parse_response_valid(self, parser):
        """Test parsing valid compose response."""
        response = '''```yaml
version: '3.8'
services:
  app:
    image: python:3.9
    ports:
      - "5000:5000"
```'''

        result = parser.parse_response(response)
        assert "version: '3.8'" in result
        assert "python:3.9" in result

    def test_parse_response_invalid(self, parser):
        """Test parsing invalid compose response."""
        response = '''
        ```yaml
        version: '3.8'
        # Missing services section
        ```
        '''
        
        with pytest.raises(ResponseParsingError) as excinfo:
            parser.parse_response(response)
        
        assert "Invalid docker-compose.yml" in str(excinfo.value)

    def test_parse_response_extraction_failure(self, parser):
        """Test parsing when extraction fails."""
        response = "No compose content here"
        
        with pytest.raises(ResponseParsingError) as excinfo:
            parser.parse_response(response)
        
        assert "No docker-compose.yml content found" in str(excinfo.value)


class TestParseLLMResponse:
    """Test suite for parse_llm_response function."""

    def test_parse_llm_response_docker_command(self):
        """Test parsing LLM response for Docker command."""
        response = json.dumps({
            "is_docker_command": True,
            "command_type": "container",
            "operation": "list"
        })
        
        result = parse_llm_response(response, "command")
        assert result["command_type"] == "container"
        assert result["operation"] == "list"

    def test_parse_llm_response_compose(self):
        """Test parsing LLM response for compose file."""
        response = '''```yaml
version: '3.8'
services:
  web:
    image: nginx
```'''

        result = parse_llm_response(response, "compose")
        assert "version: '3.8'" in result
        assert "nginx" in result

    def test_parse_llm_response_invalid_type(self):
        """Test parsing with invalid response type."""
        response = "test response"
        
        with pytest.raises(ValueError) as excinfo:
            parse_llm_response(response, "invalid_type")
        
        assert "Invalid response type" in str(excinfo.value)
