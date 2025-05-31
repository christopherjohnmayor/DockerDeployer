"""
Tests for the Docker manager module.
"""

from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import docker
import pytest
from docker.errors import APIError, DockerException, NotFound

from docker_manager.manager import DockerManager


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
    def test_init_success(self, mock_from_env, mock_docker_client):
        """Test successful DockerManager initialization."""
        mock_from_env.return_value = mock_docker_client
        mock_docker_client.ping.return_value = True

        manager = DockerManager()

        assert manager.client == mock_docker_client
        mock_from_env.assert_called_once()
        mock_docker_client.ping.assert_called_once()

    @patch("docker_manager.manager.docker", None)
    def test_init_docker_not_available(self):
        """Test initialization when Docker SDK is not available."""
        with pytest.raises(ImportError, match="Docker SDK is not available"):
            DockerManager()

    @patch("docker.from_env")
    def test_init_permission_denied(self, mock_from_env):
        """Test initialization with permission denied error."""
        mock_from_env.side_effect = DockerException("Permission denied")

        with pytest.raises(
            ConnectionError, match="Permission denied accessing Docker socket"
        ):
            DockerManager()

    @patch("docker.from_env")
    def test_init_socket_not_found(self, mock_from_env):
        """Test initialization when Docker socket is not found."""
        mock_from_env.side_effect = DockerException("No such file or directory")

        with pytest.raises(ConnectionError, match="Docker socket not found"):
            DockerManager()

    @patch("docker.from_env")
    def test_init_generic_docker_error(self, mock_from_env):
        """Test initialization with generic Docker error."""
        mock_from_env.side_effect = DockerException("Generic Docker error")

        with pytest.raises(ConnectionError, match="Docker daemon connection failed"):
            DockerManager()

    @patch("docker.from_env")
    def test_init_unexpected_error(self, mock_from_env):
        """Test initialization with unexpected error."""
        mock_from_env.side_effect = Exception("Unexpected error")

        with pytest.raises(ConnectionError, match="Failed to initialize Docker client"):
            DockerManager()

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
        mock_docker_client.containers.get.return_value.logs.side_effect = APIError(
            "API Error"
        )

        manager = DockerManager()
        result = manager.get_logs("test_container_id")

        assert "error" in result
        assert "api error" in result["error"].lower()

        mock_docker_client.containers.get.assert_called_once_with("test_container_id")
        mock_docker_client.containers.get.return_value.logs.assert_called_once()

    @patch("docker.from_env")
    def test_get_container_stats_success(self, mock_from_env, mock_docker_client):
        """Test getting container stats successfully."""
        mock_from_env.return_value = mock_docker_client

        # Mock container
        mock_container = Mock()
        mock_container.id = "test_container_id"
        mock_container.name = "test_container"
        mock_container.status = "running"
        mock_docker_client.containers.get.return_value = mock_container

        # Mock stats data
        mock_stats = {
            "cpu_stats": {
                "cpu_usage": {"total_usage": 1000000000},
                "system_cpu_usage": 2000000000,
                "online_cpus": 2,
            },
            "precpu_stats": {
                "cpu_usage": {"total_usage": 900000000},
                "system_cpu_usage": 1900000000,
            },
            "memory_stats": {"usage": 536870912, "limit": 1073741824},  # 512MB  # 1GB
            "networks": {"eth0": {"rx_bytes": 1024, "tx_bytes": 2048}},
            "blkio_stats": {
                "io_service_bytes_recursive": [
                    {"op": "Read", "value": 4096},
                    {"op": "Write", "value": 8192},
                ]
            },
        }

        # Mock stats generator
        def mock_stats_generator():
            yield mock_stats

        mock_container.stats.return_value = mock_stats_generator()

        manager = DockerManager()
        result = manager.get_container_stats("test_container_id")

        assert result["container_id"] == "test_container_id"
        assert result["container_name"] == "test_container"
        assert result["status"] == "running"
        assert "cpu_percent" in result
        assert "memory_usage" in result
        assert "memory_percent" in result
        assert result["memory_percent"] == 50.0  # 512MB / 1GB * 100
        assert result["network_rx_bytes"] == 1024
        assert result["network_tx_bytes"] == 2048
        assert result["block_read_bytes"] == 4096
        assert result["block_write_bytes"] == 8192

    @patch("docker.from_env")
    def test_get_container_stats_not_found(self, mock_from_env, mock_docker_client):
        """Test getting stats for non-existent container."""
        mock_from_env.return_value = mock_docker_client
        mock_docker_client.containers.get.side_effect = NotFound("Container not found")

        manager = DockerManager()
        result = manager.get_container_stats("nonexistent")

        assert result == {"error": "Container nonexistent not found"}

    @patch("docker.from_env")
    def test_get_container_stats_api_error(self, mock_from_env, mock_docker_client):
        """Test getting stats with API error."""
        mock_from_env.return_value = mock_docker_client
        mock_docker_client.containers.get.side_effect = APIError("Stats unavailable")

        manager = DockerManager()
        result = manager.get_container_stats("test_container_id")

        assert "error" in result
        assert "Stats unavailable" in result["error"]

    @patch("docker.from_env")
    def test_get_container_stats_streaming(self, mock_from_env, mock_docker_client):
        """Test getting streaming container stats."""
        mock_from_env.return_value = mock_docker_client

        mock_container = Mock()
        mock_docker_client.containers.get.return_value = mock_container

        def mock_stats_generator():
            while True:
                yield {"test": "data"}

        mock_container.stats.return_value = mock_stats_generator()

        manager = DockerManager()
        result = manager.get_container_stats("test_container_id", stream=True)

        assert "stats_stream" in result
        mock_container.stats.assert_called_once_with(stream=True, decode=True)

    @patch("docker.from_env")
    def test_get_system_stats_success(self, mock_from_env, mock_docker_client):
        """Test getting system stats successfully."""
        mock_from_env.return_value = mock_docker_client

        # Mock system info
        mock_system_info = {
            "ServerVersion": "20.10.17",
            "MemTotal": 8589934592,  # 8GB
            "NCPU": 4,
            "KernelVersion": "5.4.0-74-generic",
            "OperatingSystem": "Ubuntu 20.04.2 LTS",
            "Architecture": "x86_64",
        }
        mock_docker_client.info.return_value = mock_system_info

        # Mock containers
        mock_running_container = Mock()
        mock_running_container.status = "running"
        mock_stopped_container = Mock()
        mock_stopped_container.status = "exited"

        mock_docker_client.containers.list.side_effect = [
            [mock_running_container, mock_stopped_container],  # all=True
            [mock_running_container],  # all=False (running only)
        ]

        manager = DockerManager()
        result = manager.get_system_stats()

        assert result["containers_total"] == 2
        assert result["containers_running"] == 1
        assert result["containers_by_status"]["running"] == 1
        assert result["containers_by_status"]["exited"] == 1
        assert result["system_info"]["docker_version"] == "20.10.17"
        assert result["system_info"]["total_memory"] == 8589934592
        assert result["system_info"]["cpus"] == 4
        assert "timestamp" in result

    @patch("docker.from_env")
    def test_get_system_stats_docker_error(self, mock_from_env, mock_docker_client):
        """Test getting system stats with Docker error."""
        mock_from_env.return_value = mock_docker_client
        mock_docker_client.info.side_effect = DockerException(
            "Docker daemon unavailable"
        )

        manager = DockerManager()
        result = manager.get_system_stats()

        assert "error" in result
        assert "Docker daemon unavailable" in result["error"]

    @patch("docker.from_env")
    def test_get_system_stats_unexpected_error(self, mock_from_env, mock_docker_client):
        """Test getting system stats with unexpected error."""
        mock_from_env.return_value = mock_docker_client
        mock_docker_client.info.side_effect = Exception("Unexpected error")

        manager = DockerManager()
        result = manager.get_system_stats()

        assert "error" in result
        assert "Unexpected error" in result["error"]

    @patch("docker.from_env")
    def test_health_check_success(self, mock_from_env, mock_docker_client):
        """Test successful health check."""
        mock_from_env.return_value = mock_docker_client
        mock_docker_client.ping.return_value = True
        mock_docker_client.version.return_value = {
            "Version": "20.10.17",
            "ApiVersion": "1.41",
        }

        manager = DockerManager()
        result = manager.health_check()

        assert result["status"] == "healthy"
        assert result["docker_ping"] is True
        assert result["docker_version"] == "20.10.17"
        assert result["api_version"] == "1.41"

    @patch("docker.from_env")
    def test_health_check_docker_error(self, mock_from_env, mock_docker_client):
        """Test health check with Docker error."""
        mock_from_env.return_value = mock_docker_client
        # First ping succeeds for initialization, second fails for health check
        mock_docker_client.ping.side_effect = [
            True,
            DockerException("Connection failed"),
        ]

        manager = DockerManager()
        result = manager.health_check()

        assert result["status"] == "unhealthy"
        assert result["error_type"] == "docker_connection"
        assert "Connection failed" in result["error"]

    @patch("docker.from_env")
    def test_health_check_unexpected_error(self, mock_from_env, mock_docker_client):
        """Test health check with unexpected error."""
        mock_from_env.return_value = mock_docker_client
        # First ping succeeds for initialization, second fails for health check
        mock_docker_client.ping.side_effect = [True, Exception("Unexpected error")]

        manager = DockerManager()
        result = manager.health_check()

        assert result["status"] == "unhealthy"
        assert result["error_type"] == "unexpected"
        assert "Unexpected error" in result["error"]

    @patch("docker.from_env")
    def test_calculate_cpu_percent_edge_cases(self, mock_from_env, mock_docker_client):
        """Test CPU percentage calculation edge cases."""
        mock_from_env.return_value = mock_docker_client

        manager = DockerManager()

        # Test with zero system delta
        cpu_stats = {
            "cpu_usage": {"total_usage": 1000},
            "system_cpu_usage": 2000,
            "online_cpus": 2,
        }
        precpu_stats = {"cpu_usage": {"total_usage": 900}, "system_cpu_usage": 2000}

        result = manager._calculate_cpu_percent(cpu_stats, precpu_stats)
        assert result == 0.0

        # Test with missing keys
        result = manager._calculate_cpu_percent({}, {})
        assert result == 0.0

    @patch("docker.from_env")
    def test_parse_container_stats_edge_cases(self, mock_from_env, mock_docker_client):
        """Test container stats parsing edge cases."""
        mock_from_env.return_value = mock_docker_client

        mock_container = Mock()
        mock_container.id = "test_id"
        mock_container.name = "test_name"

        manager = DockerManager()

        # Test with empty stats
        result = manager._parse_container_stats({}, mock_container)
        assert result["cpu_percent"] == 0.0
        assert result["memory_percent"] == 0.0
        assert result["network_rx_bytes"] == 0
        assert result["network_tx_bytes"] == 0

        # Test with None container that causes exception during parsing
        result = manager._parse_container_stats(
            {"cpu_stats": {}, "precpu_stats": {}}, None
        )
        assert "error" in result
        assert "Failed to parse stats" in result["error"]
