"""
Tests for DockerManager metrics functionality.
"""

from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pytest

from docker_manager.manager import DockerManager


class TestDockerManagerMetrics:
    """Test class for DockerManager metrics functionality."""

    @pytest.fixture
    def mock_docker_client(self):
        """Create a mock Docker client."""
        with patch("docker.from_env") as mock_docker:
            mock_client = MagicMock()
            mock_docker.return_value = mock_client
            mock_client.ping.return_value = True
            yield mock_client

    @pytest.fixture
    def docker_manager(self, mock_docker_client):
        """Create a DockerManager instance with mocked Docker client."""
        return DockerManager()

    @pytest.fixture
    def mock_container_stats(self):
        """Mock container stats data from Docker API."""
        return {
            "cpu_stats": {
                "cpu_usage": {"total_usage": 1000000000},
                "system_cpu_usage": 2000000000,
                "online_cpus": 2,
            },
            "precpu_stats": {
                "cpu_usage": {"total_usage": 900000000},
                "system_cpu_usage": 1900000000,
            },
            "memory_stats": {"usage": 134217728, "limit": 536870912},  # 128MB  # 512MB
            "networks": {"eth0": {"rx_bytes": 1024, "tx_bytes": 2048}},
            "blkio_stats": {
                "io_service_bytes_recursive": [
                    {"op": "Read", "value": 4096},
                    {"op": "Write", "value": 8192},
                ]
            },
        }

    def test_get_container_stats_success(
        self, docker_manager, mock_docker_client, mock_container_stats
    ):
        """Test successful container stats retrieval."""
        # Setup mock container
        mock_container = MagicMock()
        mock_container.id = "test_container_id"
        mock_container.name = "test_container"
        mock_container.status = "running"

        # Setup stats generator
        mock_stats_generator = iter([mock_container_stats])
        mock_container.stats.return_value = mock_stats_generator

        mock_docker_client.containers.get.return_value = mock_container

        # Test the method
        result = docker_manager.get_container_stats("test_container_id")

        # Assertions
        assert "container_id" in result
        assert "container_name" in result
        assert "timestamp" in result
        assert "cpu_percent" in result
        assert "memory_usage" in result
        assert "memory_limit" in result
        assert "memory_percent" in result
        assert "network_rx_bytes" in result
        assert "network_tx_bytes" in result
        assert "block_read_bytes" in result
        assert "block_write_bytes" in result

        assert result["container_id"] == "test_container_id"
        assert result["container_name"] == "test_container"
        assert result["memory_usage"] == 134217728
        assert result["memory_limit"] == 536870912
        assert result["memory_percent"] == 25.0  # 128MB / 512MB * 100
        assert result["network_rx_bytes"] == 1024
        assert result["network_tx_bytes"] == 2048
        assert result["block_read_bytes"] == 4096
        assert result["block_write_bytes"] == 8192

    def test_get_container_stats_not_found(self, docker_manager, mock_docker_client):
        """Test container stats when container not found."""
        from docker.errors import NotFound

        mock_docker_client.containers.get.side_effect = NotFound("Container not found")

        result = docker_manager.get_container_stats("nonexistent_container")

        assert "error" in result
        assert "Container nonexistent_container not found" in result["error"]

    def test_get_container_stats_api_error(self, docker_manager, mock_docker_client):
        """Test container stats with Docker API error."""
        from docker.errors import APIError

        mock_docker_client.containers.get.side_effect = APIError("API Error")

        result = docker_manager.get_container_stats("test_container")

        assert "error" in result
        assert "API Error" in result["error"]

    def test_calculate_cpu_percent(self, docker_manager):
        """Test CPU percentage calculation."""
        cpu_stats = {
            "cpu_usage": {"total_usage": 1000000000},
            "system_cpu_usage": 2000000000,
            "online_cpus": 2,
        }
        precpu_stats = {
            "cpu_usage": {"total_usage": 900000000},
            "system_cpu_usage": 1900000000,
        }

        cpu_percent = docker_manager._calculate_cpu_percent(cpu_stats, precpu_stats)

        # Expected: (100000000 / 100000000) * 2 * 100 = 200%
        assert cpu_percent == 200.0

    def test_calculate_cpu_percent_zero_delta(self, docker_manager):
        """Test CPU percentage calculation with zero delta."""
        cpu_stats = {
            "cpu_usage": {"total_usage": 1000000000},
            "system_cpu_usage": 2000000000,
            "online_cpus": 2,
        }
        precpu_stats = {
            "cpu_usage": {"total_usage": 1000000000},
            "system_cpu_usage": 2000000000,
        }

        cpu_percent = docker_manager._calculate_cpu_percent(cpu_stats, precpu_stats)

        assert cpu_percent == 0.0

    def test_calculate_cpu_percent_missing_data(self, docker_manager):
        """Test CPU percentage calculation with missing data."""
        cpu_stats = {}
        precpu_stats = {}

        cpu_percent = docker_manager._calculate_cpu_percent(cpu_stats, precpu_stats)

        assert cpu_percent == 0.0

    def test_get_system_stats_success(self, docker_manager, mock_docker_client):
        """Test successful system stats retrieval."""
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
        mock_containers_all = [MagicMock() for _ in range(5)]
        mock_containers_running = [MagicMock() for _ in range(3)]

        for i, container in enumerate(mock_containers_all):
            container.status = "running" if i < 3 else "stopped"

        mock_docker_client.containers.list.side_effect = [
            mock_containers_all,  # all=True
            mock_containers_running,  # all=False
        ]

        result = docker_manager.get_system_stats()

        # Assertions
        assert "timestamp" in result
        assert result["containers_total"] == 5
        assert result["containers_running"] == 3
        assert "containers_by_status" in result
        assert result["containers_by_status"]["running"] == 3
        assert result["containers_by_status"]["stopped"] == 2

        system_info = result["system_info"]
        assert system_info["docker_version"] == "20.10.17"
        assert system_info["total_memory"] == 8589934592
        assert system_info["cpus"] == 4
        assert system_info["kernel_version"] == "5.4.0-74-generic"
        assert system_info["operating_system"] == "Ubuntu 20.04.2 LTS"
        assert system_info["architecture"] == "x86_64"

    def test_get_system_stats_docker_error(self, docker_manager, mock_docker_client):
        """Test system stats with Docker error."""
        from docker.errors import DockerException

        mock_docker_client.info.side_effect = DockerException("Docker error")

        result = docker_manager.get_system_stats()

        assert "error" in result
        assert "Docker error" in result["error"]

    def test_parse_container_stats_minimal_data(self, docker_manager):
        """Test parsing container stats with minimal data."""
        mock_container = MagicMock()
        mock_container.id = "test_id"
        mock_container.name = "test_name"
        mock_container.status = "running"

        minimal_stats = {}

        result = docker_manager._parse_container_stats(minimal_stats, mock_container)

        assert result["container_id"] == "test_id"
        assert result["container_name"] == "test_name"
        assert result["cpu_percent"] == 0.0
        assert result["memory_usage"] == 0
        assert result["memory_limit"] == 0
        assert result["memory_percent"] == 0.0
        assert result["network_rx_bytes"] == 0
        assert result["network_tx_bytes"] == 0
        assert result["block_read_bytes"] == 0
        assert result["block_write_bytes"] == 0

    def test_get_container_stats_streaming(self, docker_manager, mock_docker_client):
        """Test container stats with streaming enabled."""
        mock_container = MagicMock()
        mock_stats_generator = iter([{"test": "data"}])
        mock_container.stats.return_value = mock_stats_generator

        mock_docker_client.containers.get.return_value = mock_container

        result = docker_manager.get_container_stats("test_container", stream=True)

        assert "stats_stream" in result
        assert result["stats_stream"] == mock_stats_generator
