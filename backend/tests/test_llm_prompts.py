"""
Tests for the LLM Prompts module.
"""

import pytest

from llm.prompts.docker_commands import (
    SYSTEM_PROMPT,
    PARSE_COMMAND_TEMPLATE,
    GENERATE_COMPOSE_TEMPLATE,
    get_parse_command_prompt,
    get_generate_compose_prompt
)


class TestDockerCommandPrompts:
    """Test suite for Docker command prompt generation."""

    def test_system_prompt_exists(self):
        """Test that system prompt is defined and not empty."""
        assert SYSTEM_PROMPT is not None
        assert len(SYSTEM_PROMPT.strip()) > 0
        assert "DockerGPT" in SYSTEM_PROMPT
        assert "Docker container management" in SYSTEM_PROMPT

    def test_parse_command_template_exists(self):
        """Test that parse command template is defined."""
        assert PARSE_COMMAND_TEMPLATE is not None
        assert len(PARSE_COMMAND_TEMPLATE.strip()) > 0
        assert "{system_prompt}" in PARSE_COMMAND_TEMPLATE
        assert "{user_command}" in PARSE_COMMAND_TEMPLATE

    def test_generate_compose_template_exists(self):
        """Test that generate compose template is defined."""
        assert GENERATE_COMPOSE_TEMPLATE is not None
        assert len(GENERATE_COMPOSE_TEMPLATE.strip()) > 0
        assert "{system_prompt}" in GENERATE_COMPOSE_TEMPLATE

    def test_get_parse_command_prompt_basic(self):
        """Test basic parse command prompt generation."""
        command = "list all containers"
        prompt = get_parse_command_prompt(command)
        
        assert command in prompt
        assert SYSTEM_PROMPT in prompt
        assert "JSON Response:" in prompt

    def test_get_parse_command_prompt_with_context(self):
        """Test parse command prompt with context information."""
        command = "stop the web container"
        running_containers = [
            {"name": "web", "id": "abc123def456"},
            {"name": "db", "id": "def456ghi789"}
        ]
        available_images = ["nginx:latest", "postgres:13"]
        networks = ["bridge", "custom_network"]
        volumes = ["data_volume", "config_volume"]
        
        prompt = get_parse_command_prompt(
            command,
            running_containers=running_containers,
            available_images=available_images,
            networks=networks,
            volumes=volumes
        )
        
        assert command in prompt
        assert "web (abc123def456)" in prompt
        assert "db (def456ghi789)" in prompt
        assert "nginx:latest" in prompt
        assert "postgres:13" in prompt
        assert "bridge" in prompt
        assert "custom_network" in prompt
        assert "data_volume" in prompt
        assert "config_volume" in prompt

    def test_get_parse_command_prompt_empty_context(self):
        """Test parse command prompt with empty context."""
        command = "create new container"
        prompt = get_parse_command_prompt(
            command,
            running_containers=[],
            available_images=[],
            networks=[],
            volumes=[]
        )
        
        assert command in prompt
        assert "None" in prompt  # Should show "None" for empty lists

    def test_get_parse_command_prompt_none_context(self):
        """Test parse command prompt with None context."""
        command = "inspect container"
        prompt = get_parse_command_prompt(
            command,
            running_containers=None,
            available_images=None,
            networks=None,
            volumes=None
        )
        
        assert command in prompt
        assert "None" in prompt  # Should show "None" for None values

    def test_get_parse_command_prompt_partial_context(self):
        """Test parse command prompt with partial context."""
        command = "build image from dockerfile"
        running_containers = [{"name": "app", "id": "123456"}]
        
        prompt = get_parse_command_prompt(
            command,
            running_containers=running_containers,
            available_images=None,
            networks=["default"],
            volumes=None
        )
        
        assert command in prompt
        assert "app (123456)" in prompt
        assert "default" in prompt

    def test_get_parse_command_prompt_container_without_name(self):
        """Test parse command prompt with container missing name."""
        command = "list containers"
        running_containers = [
            {"id": "abc123"},  # Missing name
            {"name": "web", "id": "def456"}
        ]
        
        prompt = get_parse_command_prompt(
            command,
            running_containers=running_containers
        )
        
        assert command in prompt
        assert "unnamed (abc123)" in prompt  # Should handle missing name
        assert "web (def456)" in prompt

    def test_get_parse_command_prompt_container_without_id(self):
        """Test parse command prompt with container missing ID."""
        command = "restart containers"
        running_containers = [
            {"name": "app"},  # Missing id
            {"name": "db", "id": "xyz789"}
        ]
        
        prompt = get_parse_command_prompt(
            command,
            running_containers=running_containers
        )
        
        assert command in prompt
        assert "app (unknown)" in prompt  # Should handle missing id
        assert "db (xyz789)" in prompt

    def test_get_generate_compose_prompt_basic(self):
        """Test basic compose generation prompt."""
        stack_type = "LEMP"
        requirements = "Need PHP 8.0, MySQL 8.0, and Nginx"
        
        prompt = get_generate_compose_prompt(stack_type, requirements)
        
        assert stack_type in prompt
        assert requirements in prompt
        assert "docker-compose.yml" in prompt

    def test_get_generate_compose_prompt_with_environment(self):
        """Test compose generation prompt with environment."""
        stack_type = "MEAN"
        requirements = "MongoDB, Express, Angular, Node.js"
        environment = "production"
        
        prompt = get_generate_compose_prompt(
            stack_type, requirements, environment=environment
        )
        
        assert stack_type in prompt
        assert requirements in prompt
        assert environment in prompt

    def test_get_generate_compose_prompt_with_host_os(self):
        """Test compose generation prompt with host OS."""
        stack_type = "WordPress"
        requirements = "WordPress with MySQL"
        host_os = "Windows"
        
        prompt = get_generate_compose_prompt(
            stack_type, requirements, host_os=host_os
        )
        
        assert stack_type in prompt
        assert requirements in prompt
        assert host_os in prompt

    def test_get_generate_compose_prompt_with_ports(self):
        """Test compose generation prompt with available ports."""
        stack_type = "Django"
        requirements = "Django app with PostgreSQL"
        available_ports = [8000, 5432, 6379]
        
        prompt = get_generate_compose_prompt(
            stack_type, requirements, available_ports=available_ports
        )
        
        assert stack_type in prompt
        assert requirements in prompt
        assert "8000" in prompt
        assert "5432" in prompt
        assert "6379" in prompt

    def test_get_generate_compose_prompt_no_persistence(self):
        """Test compose generation prompt without persistence."""
        stack_type = "Redis"
        requirements = "Redis cache server"
        persistence_needed = False
        
        prompt = get_generate_compose_prompt(
            stack_type, requirements, persistence_needed=persistence_needed
        )
        
        assert stack_type in prompt
        assert requirements in prompt
        # Should mention no persistence needed

    def test_get_generate_compose_prompt_all_parameters(self):
        """Test compose generation prompt with all parameters."""
        stack_type = "Full Stack"
        requirements = "React frontend, Node.js backend, PostgreSQL database"
        environment = "development"
        host_os = "macOS"
        available_ports = [3000, 5000, 5432]
        persistence_needed = True
        
        prompt = get_generate_compose_prompt(
            stack_type=stack_type,
            requirements=requirements,
            environment=environment,
            host_os=host_os,
            available_ports=available_ports,
            persistence_needed=persistence_needed
        )
        
        assert stack_type in prompt
        assert requirements in prompt
        assert environment in prompt
        assert host_os in prompt
        assert "3000" in prompt
        assert "5000" in prompt
        assert "5432" in prompt

    def test_get_generate_compose_prompt_default_ports(self):
        """Test compose generation prompt with default ports."""
        stack_type = "Basic Web"
        requirements = "Simple web server"
        
        prompt = get_generate_compose_prompt(stack_type, requirements)
        
        assert stack_type in prompt
        assert requirements in prompt
        # Should include default ports like 80, 443, etc.
        assert "80" in prompt

    def test_prompt_templates_contain_required_placeholders(self):
        """Test that prompt templates contain required placeholders."""
        # Check PARSE_COMMAND_TEMPLATE
        required_placeholders = [
            "{system_prompt}",
            "{user_command}",
            "{running_containers}",
            "{available_images}",
            "{networks}",
            "{volumes}"
        ]
        
        for placeholder in required_placeholders:
            assert placeholder in PARSE_COMMAND_TEMPLATE, f"Missing placeholder: {placeholder}"

        # Check GENERATE_COMPOSE_TEMPLATE
        compose_placeholders = [
            "{system_prompt}",
            "{stack_type}",
            "{requirements}",
            "{environment}",
            "{host_os}",
            "{available_ports}",
            "{persistence_needed}"
        ]
        
        for placeholder in compose_placeholders:
            assert placeholder in GENERATE_COMPOSE_TEMPLATE, f"Missing placeholder: {placeholder}"

    def test_prompt_generation_handles_special_characters(self):
        """Test that prompt generation handles special characters properly."""
        command = "create container with name 'test-app' and port 8080:80"
        running_containers = [{"name": "app-1", "id": "abc-123"}]
        
        prompt = get_parse_command_prompt(command, running_containers=running_containers)
        
        assert command in prompt
        assert "app-1" in prompt
        assert "abc-123" in prompt

    def test_prompt_generation_handles_unicode(self):
        """Test that prompt generation handles unicode characters."""
        command = "créer un conteneur nginx"  # French with accents
        requirements = "Aplicación web con base de datos"  # Spanish
        
        parse_prompt = get_parse_command_prompt(command)
        compose_prompt = get_generate_compose_prompt("Web", requirements)
        
        assert command in parse_prompt
        assert requirements in compose_prompt

    def test_prompt_length_reasonable(self):
        """Test that generated prompts are reasonable length."""
        command = "list all containers"
        prompt = get_parse_command_prompt(command)
        
        # Prompt should be substantial but not excessive
        assert len(prompt) > 100  # Should have meaningful content
        assert len(prompt) < 10000  # Should not be excessively long

    def test_compose_prompt_length_reasonable(self):
        """Test that compose prompts are reasonable length."""
        prompt = get_generate_compose_prompt("LAMP", "PHP application with MySQL")
        
        # Prompt should be substantial but not excessive
        assert len(prompt) > 100  # Should have meaningful content
        assert len(prompt) < 10000  # Should not be excessively long
