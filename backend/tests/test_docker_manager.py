"""
Tests for the Docker manager module.
"""

import pytest
from unittest.mock import MagicMock, patch
import docker
from docker.errors import NotFound, APIError

from backend.docker_manager.manager import DockerManager


class TestDockerManager:
    """Test suite for DockerManager class."""

    @pytest.fixture
    def mock_docker_client(self):
        """Create a mock Docker client."""
        mock_client = MagicMock(spec=docker.DockerClient)

        # Mock container
        mock_container = MagicMock()
        mock_container.id = "test_container_id"
        mock_container.name = "test_container"
        mock_container.status = "running"
        mock_container.image.tags = ["test_image:latest"]
        mock_container.labels = {"app": "test"}
        mock_container.ports = {"80/tcp": [{"HostIp": "0.0.0.0", "HostPort": "8080"}]}

        # Mock container collection
        mock_containers = MagicMock()
        mock_containers.list.return_value = [mock_container]
        mock_containers.get.return_value = mock_container

        # Assign to client
        mock_client.containers = mock_containers

        # Mock logs method
        mock_container.logs.return_value = b"Test logs output"

        # Mock container actions
        mock_container.start.return_value = None
        mock_container.stop.return_value = None
        mock_container.restart.return_value = None

        return mock_client

    @patch("docker.from_env")
    def test_init(self, mock_from_env, mock_docker_client):
        """Test DockerManager initialization."""
        mock_from_env.return_value = mock_docker_client

        manager = DockerManager()

        assert manager.client == mock_docker_client
        mock_from_env.assert_called_once()

    @patch("docker.from_env")
    def test_list_containers(self, mock_from_env, mock_docker_client):
        """Test listing containers."""
        mock_from_env.return_value = mock_docker_client

        manager = DockerManager()
        containers = manager.list_containers(all=True)

        assert len(containers) == 1
        assert containers[0]["id"] == "test_container_id"
        assert containers[0]["name"] == "test_container"
        assert containers[0]["status"] == "running"
        assert containers[0]["image"] == ["test_image:latest"]

        mock_docker_client.containers.list.assert_called_once_with(all=True)

    @patch("docker.from_env")
    def test_start_container_success(self, mock_from_env, mock_docker_client):
        """Test starting a container successfully."""
        mock_from_env.return_value = mock_docker_client

        manager = DockerManager()
        result = manager.start_container("test_container_id")

        assert result["status"] == "started"
        assert result["id"] == "test_container_id"

        mock_docker_client.containers.get.assert_called_once_with("test_container_id")
        mock_docker_client.containers.get.return_value.start.assert_called_once()

    @patch("docker.from_env")
    def test_start_container_not_found(self, mock_from_env, mock_docker_client):
        """Test starting a non-existent container."""
        mock_from_env.return_value = mock_docker_client
        mock_docker_client.containers.get.side_effect = NotFound("Container not found")

        manager = DockerManager()
        result = manager.start_container("nonexistent_id")

        assert "error" in result
        assert "not found" in result["error"].lower()

        mock_docker_client.containers.get.assert_called_once_with("nonexistent_id")

    @patch("docker.from_env")
    def test_stop_container_success(self, mock_from_env, mock_docker_client):
        """Test stopping a container successfully."""
        mock_from_env.return_value = mock_docker_client

        manager = DockerManager()
        result = manager.stop_container("test_container_id")

        assert result["status"] == "stopped"
        assert result["id"] == "test_container_id"

        mock_docker_client.containers.get.assert_called_once_with("test_container_id")
        mock_docker_client.containers.get.return_value.stop.assert_called_once()

    @patch("docker.from_env")
    def test_restart_container_success(self, mock_from_env, mock_docker_client):
        """Test restarting a container successfully."""
        mock_from_env.return_value = mock_docker_client

        manager = DockerManager()
        result = manager.restart_container("test_container_id")

        assert result["status"] == "restarted"
        assert result["id"] == "test_container_id"

        mock_docker_client.containers.get.assert_called_once_with("test_container_id")
        mock_docker_client.containers.get.return_value.restart.assert_called_once()

    @patch("docker.from_env")
    def test_get_logs_success(self, mock_from_env, mock_docker_client):
        """Test getting container logs successfully."""
        mock_from_env.return_value = mock_docker_client

        manager = DockerManager()
        result = manager.get_logs("test_container_id")

        assert result["logs"] == "Test logs output"
        assert result["id"] == "test_container_id"

        mock_docker_client.containers.get.assert_called_once_with("test_container_id")
        mock_docker_client.containers.get.return_value.logs.assert_called_once()

    @patch("docker.from_env")
    def test_get_logs_api_error(self, mock_from_env, mock_docker_client):
        """Test handling API error when getting logs."""
        mock_from_env.return_value = mock_docker_client
        mock_docker_client.containers.get.return_value.logs.side_effect = APIError("API Error")

        manager = DockerManager()
        result = manager.get_logs("test_container_id")

        assert "error" in result
        assert "api error" in result["error"].lower()

        mock_docker_client.containers.get.assert_called_once_with("test_container_id")
        mock_docker_client.containers.get.return_value.logs.assert_called_once()
