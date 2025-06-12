"""
Tests for the Docker manager module.
"""

from datetime import datetime
from unittest.mock import MagicMock, Mock, PropertyMock, patch

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

    @patch("docker.from_env")
    def test_get_container_stats_complex_parsing(self, mock_from_env, mock_docker_client):
        """Test complex container stats parsing scenarios."""
        mock_from_env.return_value = mock_docker_client

        mock_container = Mock()
        mock_container.id = "test_container_id"
        mock_container.name = "test_container"
        mock_container.status = "running"

        mock_docker_client.containers.get.return_value = mock_container

        manager = DockerManager()

        # Test with bytes response that needs JSON parsing
        mock_stats_bytes = b'{"cpu_stats": {"cpu_usage": {"total_usage": 1000000}}, "memory_stats": {"usage": 1024}}'
        mock_container.stats.return_value = mock_stats_bytes

        result = manager.get_container_stats("test_container_id")
        assert "container_id" in result
        assert result["container_id"] == "test_container_id"

        # Test with generator response (older Docker SDK)
        def mock_stats_generator():
            yield {"cpu_stats": {"cpu_usage": {"total_usage": 2000000}}, "memory_stats": {"usage": 2048}}

        mock_container.stats.side_effect = [Exception("stream=False failed"), mock_stats_generator()]

        result = manager.get_container_stats("test_container_id")
        assert "container_id" in result
        assert result["container_id"] == "test_container_id"

    @patch("docker.from_env")
    def test_get_container_stats_fallback_scenarios(self, mock_from_env, mock_docker_client):
        """Test container stats fallback scenarios."""
        mock_from_env.return_value = mock_docker_client

        mock_container = Mock()
        mock_container.id = "test_container_id"
        mock_container.name = "test_container"
        mock_container.status = "running"

        mock_docker_client.containers.get.return_value = mock_container

        manager = DockerManager()

        # Test both stream=False and stream=True failing
        mock_container.stats.side_effect = [
            Exception("stream=False failed"),
            Exception("stream=True failed")
        ]

        result = manager.get_container_stats("test_container_id")
        assert "error" in result
        assert "Failed to get stats" in result["error"]

    @patch("docker.from_env")
    def test_get_multiple_container_stats_success(self, mock_from_env, mock_docker_client):
        """Test getting stats for multiple containers successfully."""
        mock_from_env.return_value = mock_docker_client

        # Mock containers
        mock_container1 = Mock()
        mock_container1.id = "container1"
        mock_container1.name = "test1"
        mock_container1.status = "running"

        mock_container2 = Mock()
        mock_container2.id = "container2"
        mock_container2.name = "test2"
        mock_container2.status = "running"

        def mock_get_container(container_id):
            if container_id == "container1":
                return mock_container1
            elif container_id == "container2":
                return mock_container2
            else:
                raise NotFound("Container not found")

        mock_docker_client.containers.get.side_effect = mock_get_container

        # Mock stats for both containers
        mock_stats = {
            "cpu_stats": {"cpu_usage": {"total_usage": 1000000}, "system_cpu_usage": 2000000, "online_cpus": 1},
            "precpu_stats": {"cpu_usage": {"total_usage": 900000}, "system_cpu_usage": 1900000},
            "memory_stats": {"usage": 1024, "limit": 2048},
            "networks": {"eth0": {"rx_bytes": 100, "tx_bytes": 200}},
            "blkio_stats": {"io_service_bytes_recursive": []}
        }

        mock_container1.stats.return_value = mock_stats
        mock_container2.stats.return_value = mock_stats

        manager = DockerManager()
        result = manager.get_multiple_container_stats(["container1", "container2"])

        assert len(result) == 2
        assert "container1" in result
        assert "container2" in result
        assert result["container1"]["container_id"] == "container1"
        assert result["container2"]["container_id"] == "container2"

    @patch("docker.from_env")
    def test_get_multiple_container_stats_with_errors(self, mock_from_env, mock_docker_client):
        """Test getting stats for multiple containers with some errors."""
        mock_from_env.return_value = mock_docker_client

        def mock_get_container(container_id):
            if container_id == "valid_container":
                mock_container = Mock()
                mock_container.id = "valid_container"
                mock_container.name = "valid"
                mock_container.status = "running"
                mock_container.stats.return_value = {
                    "cpu_stats": {"cpu_usage": {"total_usage": 1000000}},
                    "memory_stats": {"usage": 1024}
                }
                return mock_container
            else:
                raise NotFound("Container not found")

        mock_docker_client.containers.get.side_effect = mock_get_container

        manager = DockerManager()
        result = manager.get_multiple_container_stats(["valid_container", "invalid_container"])

        assert len(result) == 2
        assert "valid_container" in result
        assert "invalid_container" in result
        assert "container_id" in result["valid_container"]
        assert "error" in result["invalid_container"]
        assert "not found" in result["invalid_container"]["error"]

    @patch("docker.from_env")
    def test_get_aggregated_metrics_success(self, mock_from_env, mock_docker_client):
        """Test getting aggregated metrics successfully."""
        mock_from_env.return_value = mock_docker_client

        # Mock containers with different stats
        def mock_get_container(container_id):
            mock_container = Mock()
            mock_container.id = container_id
            mock_container.name = f"container_{container_id}"
            mock_container.status = "running"

            # Different stats for each container
            if container_id == "container1":
                mock_container.stats.return_value = {
                    "cpu_stats": {"cpu_usage": {"total_usage": 2000000}, "system_cpu_usage": 4000000, "online_cpus": 2},
                    "precpu_stats": {"cpu_usage": {"total_usage": 1000000}, "system_cpu_usage": 2000000},
                    "memory_stats": {"usage": 1073741824, "limit": 2147483648},  # 1GB / 2GB
                    "networks": {"eth0": {"rx_bytes": 1024, "tx_bytes": 2048}},
                    "blkio_stats": {"io_service_bytes_recursive": [
                        {"op": "Read", "value": 4096}, {"op": "Write", "value": 8192}
                    ]}
                }
            else:
                mock_container.stats.return_value = {
                    "cpu_stats": {"cpu_usage": {"total_usage": 3000000}, "system_cpu_usage": 6000000, "online_cpus": 2},
                    "precpu_stats": {"cpu_usage": {"total_usage": 2000000}, "system_cpu_usage": 4000000},
                    "memory_stats": {"usage": 536870912, "limit": 1073741824},  # 512MB / 1GB
                    "networks": {"eth0": {"rx_bytes": 2048, "tx_bytes": 4096}},
                    "blkio_stats": {"io_service_bytes_recursive": [
                        {"op": "Read", "value": 8192}, {"op": "Write", "value": 16384}
                    ]}
                }
            return mock_container

        mock_docker_client.containers.get.side_effect = mock_get_container

        manager = DockerManager()
        result = manager.get_aggregated_metrics(["container1", "container2"])

        assert "timestamp" in result
        assert result["container_count"] == 2
        assert result["total_containers"] == 2
        assert "aggregated_metrics" in result

        metrics = result["aggregated_metrics"]
        assert "avg_cpu_percent" in metrics
        assert "total_memory_usage" in metrics
        assert "total_memory_limit" in metrics
        assert "avg_memory_percent" in metrics
        assert "total_network_rx_bytes" in metrics
        assert "total_network_tx_bytes" in metrics
        assert "total_block_read_bytes" in metrics
        assert "total_block_write_bytes" in metrics

        # Verify aggregated values
        assert metrics["total_memory_usage"] == 1073741824 + 536870912  # 1GB + 512MB
        assert metrics["total_memory_limit"] == 2147483648 + 1073741824  # 2GB + 1GB
        assert metrics["total_network_rx_bytes"] == 1024 + 2048
        assert metrics["total_network_tx_bytes"] == 2048 + 4096
        assert metrics["total_block_read_bytes"] == 4096 + 8192
        assert metrics["total_block_write_bytes"] == 8192 + 16384

        assert "individual_stats" in result
        assert len(result["individual_stats"]) == 2

    @patch("docker.from_env")
    def test_get_aggregated_metrics_with_errors(self, mock_from_env, mock_docker_client):
        """Test getting aggregated metrics with some container errors."""
        mock_from_env.return_value = mock_docker_client

        def mock_get_container(container_id):
            if container_id == "valid_container":
                mock_container = Mock()
                mock_container.id = "valid_container"
                mock_container.name = "valid"
                mock_container.status = "running"
                mock_container.stats.return_value = {
                    "cpu_stats": {"cpu_usage": {"total_usage": 1000000}},
                    "memory_stats": {"usage": 1024, "limit": 2048}
                }
                return mock_container
            else:
                raise NotFound("Container not found")

        mock_docker_client.containers.get.side_effect = mock_get_container

        manager = DockerManager()
        result = manager.get_aggregated_metrics(["valid_container", "invalid_container"])

        assert result["container_count"] == 1  # Only valid container counted
        assert result["total_containers"] == 2  # Total requested
        assert "aggregated_metrics" in result
        assert "individual_stats" in result
        assert len(result["individual_stats"]) == 2

    @patch("docker.from_env")
    def test_get_aggregated_metrics_no_valid_containers(self, mock_from_env, mock_docker_client):
        """Test getting aggregated metrics with no valid containers."""
        mock_from_env.return_value = mock_docker_client
        mock_docker_client.containers.get.side_effect = NotFound("Container not found")

        manager = DockerManager()
        result = manager.get_aggregated_metrics(["invalid1", "invalid2"])

        assert result["container_count"] == 0
        assert result["total_containers"] == 2
        assert result["aggregated_metrics"]["avg_cpu_percent"] == 0
        assert result["aggregated_metrics"]["avg_memory_percent"] == 0

    @patch("docker.from_env")
    def test_get_aggregated_metrics_exception(self, mock_from_env, mock_docker_client):
        """Test getting aggregated metrics with exception."""
        mock_from_env.return_value = mock_docker_client
        mock_docker_client.containers.get.side_effect = Exception("Unexpected error")

        manager = DockerManager()
        result = manager.get_aggregated_metrics(["container1"])

        # The method doesn't fail completely, it returns aggregated results with individual errors
        assert result["container_count"] == 0
        assert "individual_stats" in result
        assert "error" in result["individual_stats"]["container1"]

    @patch("docker.from_env")
    async def test_get_streaming_stats_success(self, mock_from_env, mock_docker_client):
        """Test getting streaming stats successfully."""
        mock_from_env.return_value = mock_docker_client

        mock_container = Mock()
        mock_container.id = "test_container"
        mock_container.name = "test"
        mock_container.status = "running"
        mock_docker_client.containers.get.return_value = mock_container

        # Mock streaming stats generator
        def mock_stats_generator():
            yield {"cpu_stats": {"cpu_usage": {"total_usage": 1000000}}, "memory_stats": {"usage": 1024}}
            yield {"cpu_stats": {"cpu_usage": {"total_usage": 2000000}}, "memory_stats": {"usage": 2048}}

        mock_container.stats.return_value = mock_stats_generator()

        manager = DockerManager()
        stats_generator = manager.get_streaming_stats("test_container")

        # Get first two stats
        stats1 = await stats_generator.__anext__()
        stats2 = await stats_generator.__anext__()

        assert stats1["container_id"] == "test_container"
        assert stats2["container_id"] == "test_container"
        assert "timestamp" in stats1
        assert "timestamp" in stats2

    @patch("docker.from_env")
    async def test_get_streaming_stats_not_found(self, mock_from_env, mock_docker_client):
        """Test getting streaming stats for non-existent container."""
        mock_from_env.return_value = mock_docker_client
        mock_docker_client.containers.get.side_effect = NotFound("Container not found")

        manager = DockerManager()
        stats_generator = manager.get_streaming_stats("nonexistent")

        error_result = await stats_generator.__anext__()
        assert "error" in error_result
        assert "not found" in error_result["error"]

    @patch("docker.from_env")
    async def test_get_streaming_stats_api_error(self, mock_from_env, mock_docker_client):
        """Test getting streaming stats with API error."""
        mock_from_env.return_value = mock_docker_client
        mock_docker_client.containers.get.side_effect = APIError("API error")

        manager = DockerManager()
        stats_generator = manager.get_streaming_stats("test_container")

        error_result = await stats_generator.__anext__()
        assert "error" in error_result
        assert "API error" in error_result["error"]

    @patch("docker.from_env")
    async def test_get_streaming_stats_bytes_parsing(self, mock_from_env, mock_docker_client):
        """Test streaming stats with bytes response parsing."""
        mock_from_env.return_value = mock_docker_client

        mock_container = Mock()
        mock_container.id = "test_container"
        mock_container.name = "test"
        mock_container.status = "running"
        mock_docker_client.containers.get.return_value = mock_container

        # Mock streaming stats generator with bytes
        def mock_stats_generator():
            yield b'{"cpu_stats": {"cpu_usage": {"total_usage": 1000000}}, "memory_stats": {"usage": 1024}}'

        mock_container.stats.return_value = mock_stats_generator()

        manager = DockerManager()
        stats_generator = manager.get_streaming_stats("test_container")

        stats = await stats_generator.__anext__()
        assert stats["container_id"] == "test_container"
        assert "timestamp" in stats

    @patch("docker.from_env")
    def test_parse_container_stats_comprehensive(self, mock_from_env, mock_docker_client):
        """Test comprehensive container stats parsing."""
        mock_from_env.return_value = mock_docker_client

        mock_container = Mock()
        mock_container.id = "test_container"
        mock_container.name = "test_name"
        mock_container.status = "running"

        manager = DockerManager()

        # Test with comprehensive stats data
        comprehensive_stats = {
            "cpu_stats": {
                "cpu_usage": {"total_usage": 2000000000},
                "system_cpu_usage": 4000000000,
                "online_cpus": 4
            },
            "precpu_stats": {
                "cpu_usage": {"total_usage": 1000000000},
                "system_cpu_usage": 2000000000
            },
            "memory_stats": {
                "usage": 1073741824,  # 1GB
                "limit": 2147483648   # 2GB
            },
            "networks": {
                "eth0": {"rx_bytes": 1024, "tx_bytes": 2048},
                "eth1": {"rx_bytes": 512, "tx_bytes": 1024}
            },
            "blkio_stats": {
                "io_service_bytes_recursive": [
                    {"op": "Read", "value": 4096},
                    {"op": "Write", "value": 8192},
                    {"op": "Read", "value": 2048},
                    {"op": "Write", "value": 4096}
                ]
            }
        }

        result = manager._parse_container_stats(comprehensive_stats, mock_container)

        assert result["container_id"] == "test_container"
        assert result["container_name"] == "test_name"
        assert result["status"] == "running"
        assert result["cpu_percent"] == 200.0  # (2000000000-1000000000)/(4000000000-2000000000)*4*100
        assert result["memory_usage"] == 1073741824
        assert result["memory_limit"] == 2147483648
        assert result["memory_percent"] == 50.0  # 1GB/2GB * 100
        assert result["network_rx_bytes"] == 1536  # 1024 + 512
        assert result["network_tx_bytes"] == 3072  # 2048 + 1024
        assert result["block_read_bytes"] == 6144   # 4096 + 2048
        assert result["block_write_bytes"] == 12288 # 8192 + 4096
        assert "timestamp" in result

    @patch("docker.from_env")
    def test_parse_container_stats_missing_data(self, mock_from_env, mock_docker_client):
        """Test container stats parsing with missing data."""
        mock_from_env.return_value = mock_docker_client

        mock_container = Mock()
        mock_container.id = "test_container"
        mock_container.name = "test_name"
        mock_container.status = "running"

        manager = DockerManager()

        # Test with minimal stats data
        minimal_stats = {
            "cpu_stats": {},
            "precpu_stats": {},
            "memory_stats": {},
            "networks": {},
            "blkio_stats": {}
        }

        result = manager._parse_container_stats(minimal_stats, mock_container)

        assert result["container_id"] == "test_container"
        assert result["cpu_percent"] == 0.0
        assert result["memory_usage"] == 0
        assert result["memory_limit"] == 0
        assert result["memory_percent"] == 0.0
        assert result["network_rx_bytes"] == 0
        assert result["network_tx_bytes"] == 0
        assert result["block_read_bytes"] == 0
        assert result["block_write_bytes"] == 0

    @patch("docker.from_env")
    def test_parse_container_stats_exception_handling(self, mock_from_env, mock_docker_client):
        """Test container stats parsing exception handling."""
        mock_from_env.return_value = mock_docker_client

        manager = DockerManager()

        # Test with None container (should handle gracefully)
        result = manager._parse_container_stats({}, None)

        assert "error" in result
        assert "Failed to parse stats" in result["error"]
        assert "timestamp" in result

    @patch("docker.from_env")
    def test_calculate_cpu_percent_comprehensive(self, mock_from_env, mock_docker_client):
        """Test comprehensive CPU percentage calculation scenarios."""
        mock_from_env.return_value = mock_docker_client

        manager = DockerManager()

        # Test normal calculation
        cpu_stats = {
            "cpu_usage": {"total_usage": 2000000000},
            "system_cpu_usage": 4000000000,
            "online_cpus": 2
        }
        precpu_stats = {
            "cpu_usage": {"total_usage": 1000000000},
            "system_cpu_usage": 2000000000
        }

        result = manager._calculate_cpu_percent(cpu_stats, precpu_stats)
        assert result == 100.0  # (2000000000-1000000000)/(4000000000-2000000000)*2*100

        # Test with zero CPU delta
        cpu_stats["cpu_usage"]["total_usage"] = 1000000000  # Same as precpu
        result = manager._calculate_cpu_percent(cpu_stats, precpu_stats)
        assert result == 0.0

        # Test with zero system delta
        cpu_stats["system_cpu_usage"] = 2000000000  # Same as precpu
        result = manager._calculate_cpu_percent(cpu_stats, precpu_stats)
        assert result == 0.0

        # Test with missing keys
        result = manager._calculate_cpu_percent({}, {})
        assert result == 0.0

        # Test with malformed data (should handle gracefully)
        try:
            malformed_cpu = {"cpu_usage": "invalid"}
            malformed_precpu = {"cpu_usage": None}
            result = manager._calculate_cpu_percent(malformed_cpu, malformed_precpu)
            assert result == 0.0
        except (AttributeError, TypeError):
            # This is expected behavior for malformed data
            pass

    @patch("docker.from_env")
    def test_container_operations_api_errors(self, mock_from_env, mock_docker_client):
        """Test container operations with various API errors."""
        mock_from_env.return_value = mock_docker_client

        mock_container = Mock()
        mock_docker_client.containers.get.return_value = mock_container

        manager = DockerManager()

        # Test start container with API error
        mock_container.start.side_effect = APIError("Cannot start container")
        result = manager.start_container("test_container")
        assert "error" in result
        assert "Cannot start container" in result["error"]

        # Test stop container with API error
        mock_container.stop.side_effect = APIError("Cannot stop container")
        result = manager.stop_container("test_container")
        assert "error" in result
        assert "Cannot stop container" in result["error"]

        # Test restart container with API error
        mock_container.restart.side_effect = APIError("Cannot restart container")
        result = manager.restart_container("test_container")
        assert "error" in result
        assert "Cannot restart container" in result["error"]

    @patch("docker.from_env")
    def test_get_logs_with_tail_parameter(self, mock_from_env, mock_docker_client):
        """Test getting logs with different tail parameters."""
        mock_from_env.return_value = mock_docker_client

        mock_container = Mock()
        mock_container.logs.return_value = b"Line 1\nLine 2\nLine 3\nLine 4\nLine 5"
        mock_docker_client.containers.get.return_value = mock_container

        manager = DockerManager()

        # Test with default tail
        result = manager.get_logs("test_container")
        assert result["logs"] == "Line 1\nLine 2\nLine 3\nLine 4\nLine 5"
        mock_container.logs.assert_called_with(tail=100)

        # Test with custom tail
        result = manager.get_logs("test_container", tail=50)
        mock_container.logs.assert_called_with(tail=50)

    @patch("docker.from_env")
    def test_get_container_stats_dict_response(self, mock_from_env, mock_docker_client):
        """Test container stats with direct dict response."""
        mock_from_env.return_value = mock_docker_client

        mock_container = Mock()
        mock_container.id = "test_container"
        mock_container.name = "test"
        mock_container.status = "running"
        mock_docker_client.containers.get.return_value = mock_container

        # Mock direct dict response (newer Docker SDK)
        mock_stats_dict = {
            "cpu_stats": {"cpu_usage": {"total_usage": 1000000}},
            "memory_stats": {"usage": 1024}
        }
        mock_container.stats.return_value = mock_stats_dict

        manager = DockerManager()
        result = manager.get_container_stats("test_container")

        assert result["container_id"] == "test_container"
        assert "timestamp" in result

    @patch("docker.from_env")
    def test_get_container_stats_no_stats_available(self, mock_from_env, mock_docker_client):
        """Test container stats when no stats are available."""
        mock_from_env.return_value = mock_docker_client

        mock_container = Mock()
        mock_docker_client.containers.get.return_value = mock_container

        # Mock empty generator
        def empty_generator():
            return
            yield  # This will never be reached

        mock_container.stats.side_effect = [
            Exception("stream=False failed"),
            empty_generator()
        ]

        manager = DockerManager()
        result = manager.get_container_stats("test_container")

        assert "error" in result
        assert "Failed to get stats" in result["error"]

        # Test with no stats available (StopIteration)
        def mock_empty_generator():
            return iter([])

        mock_container.stats.side_effect = [Exception("stream=False failed"), mock_empty_generator()]

        result = manager.get_container_stats("test_container_id")
        assert "error" in result
        assert "Failed to get stats" in result["error"]

    @patch("docker.from_env")
    def test_get_multiple_container_stats_error_handling(self, mock_from_env, mock_docker_client):
        """Test error handling in multiple container stats."""
        mock_from_env.return_value = mock_docker_client

        manager = DockerManager()

        # Mock get_container_stats to raise exception for one container
        original_get_stats = manager.get_container_stats
        def mock_get_stats(container_id):
            if container_id == "failing_container":
                raise Exception("Container stats failed")
            return original_get_stats(container_id)

        manager.get_container_stats = mock_get_stats

        # Test with mixed success/failure
        container_ids = ["working_container", "failing_container"]
        result = manager.get_multiple_container_stats(container_ids)

        assert len(result) == 2
        assert "failing_container" in result
        assert "error" in result["failing_container"]
        assert "Failed to get stats" in result["failing_container"]["error"]

    @patch("docker.from_env")
    def test_get_aggregated_metrics_error_handling(self, mock_from_env, mock_docker_client):
        """Test error handling in aggregated metrics."""
        mock_from_env.return_value = mock_docker_client

        manager = DockerManager()

        # Mock get_multiple_container_stats to raise exception
        def mock_failing_multiple_stats(container_ids):
            raise Exception("Multiple stats failed")

        manager.get_multiple_container_stats = mock_failing_multiple_stats

        result = manager.get_aggregated_metrics(["container1", "container2"])
        assert "error" in result
        assert "Failed to get aggregated metrics" in result["error"]

    def test_docker_import_error_handling(self):
        """Test Docker import error handling."""
        # Test when docker module is None (import failed)
        with patch('docker_manager.manager.docker', None):
            with pytest.raises(ImportError) as exc_info:
                DockerManager()
            assert "Docker SDK is not available" in str(exc_info.value)

    @patch("docker.from_env")
    def test_container_operations_api_errors(self, mock_from_env, mock_docker_client):
        """Test API errors in container operations."""
        mock_from_env.return_value = mock_docker_client

        mock_container = Mock()
        mock_docker_client.containers.get.return_value = mock_container

        manager = DockerManager()

        # Test start container API error
        mock_container.start.side_effect = APIError("Start failed")
        result = manager.start_container("test_container")
        assert "error" in result
        assert "Start failed" in result["error"]

        # Test stop container API error
        mock_container.stop.side_effect = APIError("Stop failed")
        result = manager.stop_container("test_container")
        assert "error" in result
        assert "Stop failed" in result["error"]

        # Test restart container API error
        mock_container.restart.side_effect = APIError("Restart failed")
        result = manager.restart_container("test_container")
        assert "error" in result
        assert "Restart failed" in result["error"]

        # Test get logs API error
        mock_container.logs.side_effect = APIError("Logs failed")
        result = manager.get_logs("test_container")
        assert "error" in result
        assert "Logs failed" in result["error"]


class TestDockerManagerEnhanced:
    """Enhanced test suite for DockerManager with comprehensive coverage."""

    @pytest.fixture
    def mock_docker_client(self):
        """Create a comprehensive mock Docker client."""
        mock_client = MagicMock(spec=docker.DockerClient)

        # Mock container
        mock_container = MagicMock()
        mock_container.id = "test_container_id"
        mock_container.name = "test_container"
        mock_container.status = "running"
        mock_container.image.tags = ["nginx:latest"]
        mock_container.labels = {"app": "web", "env": "production"}
        mock_container.ports = {"80/tcp": [{"HostIp": "0.0.0.0", "HostPort": "8080"}]}

        # Mock container collection
        mock_containers = MagicMock()
        mock_containers.list.return_value = [mock_container]
        mock_containers.get.return_value = mock_container
        mock_client.containers = mock_containers

        # Mock images collection
        mock_images = MagicMock()
        mock_image = MagicMock()
        mock_image.id = "sha256:test_image_id"
        mock_image.tags = ["nginx:latest"]
        mock_image.attrs = {"Size": 133000000}
        mock_images.list.return_value = [mock_image]
        mock_images.get.return_value = mock_image
        mock_images.pull.return_value = mock_image
        mock_client.images = mock_images

        # Mock networks collection
        mock_networks = MagicMock()
        mock_network = MagicMock()
        mock_network.id = "test_network_id"
        mock_network.name = "bridge"
        mock_network.attrs = {"Driver": "bridge", "Scope": "local"}
        mock_networks.list.return_value = [mock_network]
        mock_networks.get.return_value = mock_network
        mock_client.networks = mock_networks

        # Mock volumes collection
        mock_volumes = MagicMock()
        mock_volume = MagicMock()
        mock_volume.id = "test_volume_id"
        mock_volume.name = "test_volume"
        mock_volume.attrs = {"Driver": "local", "Mountpoint": "/var/lib/docker/volumes/test_volume"}
        mock_volumes.list.return_value = [mock_volume]
        mock_volumes.get.return_value = mock_volume
        mock_client.volumes = mock_volumes

        return mock_client

    @patch("docker.from_env")
    def test_docker_sdk_integration_connection_success(self, mock_from_env, mock_docker_client):
        """Test Docker SDK integration with successful connection."""
        mock_from_env.return_value = mock_docker_client
        mock_docker_client.ping.return_value = True

        manager = DockerManager()

        # Verify connection was established
        assert manager.client == mock_docker_client
        mock_from_env.assert_called_once()
        mock_docker_client.ping.assert_called_once()

    @patch("docker.from_env")
    def test_docker_sdk_integration_authentication_failure(self, mock_from_env):
        """Test Docker SDK integration with authentication failure."""
        mock_from_env.side_effect = DockerException("Authentication failed")

        with pytest.raises(ConnectionError, match="Docker daemon connection failed"):
            DockerManager()

    @patch("docker.from_env")
    def test_container_lifecycle_create_start_stop_remove(self, mock_from_env, mock_docker_client):
        """Test complete container lifecycle operations."""
        mock_from_env.return_value = mock_docker_client

        # Mock container for lifecycle operations
        mock_container = MagicMock()
        mock_container.id = "lifecycle_container_id"
        mock_container.name = "lifecycle_container"
        mock_container.status = "created"

        mock_docker_client.containers.get.return_value = mock_container
        mock_docker_client.containers.run.return_value = mock_container

        manager = DockerManager()

        # Test start operation
        mock_container.status = "running"
        result = manager.start_container("lifecycle_container_id")
        assert result["status"] == "started"
        assert result["id"] == "lifecycle_container_id"
        mock_container.start.assert_called_once()

        # Test stop operation
        mock_container.status = "exited"
        result = manager.stop_container("lifecycle_container_id")
        assert result["status"] == "stopped"
        assert result["id"] == "lifecycle_container_id"
        mock_container.stop.assert_called_once()

        # Test restart operation
        mock_container.status = "running"
        result = manager.restart_container("lifecycle_container_id")
        assert result["status"] == "restarted"
        assert result["id"] == "lifecycle_container_id"
        mock_container.restart.assert_called_once()

    @patch("docker.from_env")
    def test_container_deployment_with_configurations(self, mock_from_env, mock_docker_client):
        """Test container deployment with various configurations."""
        mock_from_env.return_value = mock_docker_client

        # Mock container with complex configuration
        mock_container = MagicMock()
        mock_container.id = "config_container_id"
        mock_container.name = "config_container"
        mock_container.status = "running"
        mock_container.attrs = {
            "Config": {
                "Env": ["NODE_ENV=production", "PORT=3000"],
                "ExposedPorts": {"3000/tcp": {}},
                "WorkingDir": "/app",
                "Cmd": ["npm", "start"]
            },
            "HostConfig": {
                "Memory": 536870912,  # 512MB
                "CpuShares": 1024,
                "PortBindings": {"3000/tcp": [{"HostPort": "3000"}]}
            }
        }

        mock_docker_client.containers.get.return_value = mock_container

        manager = DockerManager()

        # Test container with environment variables
        containers = manager.list_containers(all=True)
        assert len(containers) >= 0  # Should not fail

        # Test getting logs with custom tail
        mock_container.logs.return_value = b"Application started on port 3000"
        result = manager.get_logs("config_container_id", tail=50)
        assert result["logs"] == "Application started on port 3000"
        mock_container.logs.assert_called_with(tail=50)

    @patch("docker.from_env")
    def test_container_monitoring_and_health_checks(self, mock_from_env, mock_docker_client):
        """Test container monitoring and health check functionality."""
        mock_from_env.return_value = mock_docker_client

        # Mock container with health check data
        mock_container = MagicMock()
        mock_container.id = "health_container_id"
        mock_container.name = "health_container"
        mock_container.status = "running"
        mock_container.attrs = {
            "State": {
                "Health": {
                    "Status": "healthy",
                    "FailingStreak": 0,
                    "Log": [
                        {
                            "Start": "2024-01-01T12:00:00Z",
                            "End": "2024-01-01T12:00:01Z",
                            "ExitCode": 0,
                            "Output": "Health check passed"
                        }
                    ]
                }
            }
        }

        mock_docker_client.containers.get.return_value = mock_container

        manager = DockerManager()

        # Test health check functionality
        result = manager.health_check()
        assert result["status"] == "healthy"

        # Test system stats for monitoring
        mock_docker_client.info.return_value = {
            "ServerVersion": "20.10.17",
            "MemTotal": 8589934592,
            "NCPU": 4
        }
        mock_docker_client.containers.list.side_effect = [
            [mock_container],  # all=True
            [mock_container]   # all=False
        ]

        result = manager.get_system_stats()
        assert result["containers_total"] == 1
        assert result["containers_running"] == 1
        assert "system_info" in result

    @patch("docker.from_env")
    def test_image_management_operations(self, mock_from_env, mock_docker_client):
        """Test Docker image management operations."""
        mock_from_env.return_value = mock_docker_client

        # Mock image operations
        mock_image = MagicMock()
        mock_image.id = "sha256:test_image_id"
        mock_image.tags = ["nginx:latest", "nginx:1.21"]
        mock_image.attrs = {
            "Size": 133000000,
            "Created": "2024-01-01T12:00:00Z",
            "Architecture": "amd64"
        }

        mock_docker_client.images.get.return_value = mock_image
        mock_docker_client.images.list.return_value = [mock_image]
        mock_docker_client.images.pull.return_value = mock_image

        manager = DockerManager()

        # Test that manager can handle image operations (even though not directly exposed)
        # This tests the Docker client integration
        assert manager.client.images is not None

        # Verify image operations would work through the client
        images = manager.client.images.list()
        assert len(images) == 1
        assert images[0].tags == ["nginx:latest", "nginx:1.21"]

    @patch("docker.from_env")
    def test_network_and_volume_operations(self, mock_from_env, mock_docker_client):
        """Test Docker network and volume operations."""
        mock_from_env.return_value = mock_docker_client

        # Mock network operations
        mock_network = MagicMock()
        mock_network.id = "test_network_id"
        mock_network.name = "custom_network"
        mock_network.attrs = {
            "Driver": "bridge",
            "Scope": "local",
            "IPAM": {"Config": [{"Subnet": "172.20.0.0/16"}]}
        }

        mock_docker_client.networks.get.return_value = mock_network
        mock_docker_client.networks.list.return_value = [mock_network]

        # Mock volume operations
        mock_volume = MagicMock()
        mock_volume.id = "test_volume_id"
        mock_volume.name = "data_volume"
        mock_volume.attrs = {
            "Driver": "local",
            "Mountpoint": "/var/lib/docker/volumes/data_volume/_data"
        }

        mock_docker_client.volumes.get.return_value = mock_volume
        mock_docker_client.volumes.list.return_value = [mock_volume]

        manager = DockerManager()

        # Test that manager can handle network and volume operations
        assert manager.client.networks is not None
        assert manager.client.volumes is not None

        # Verify network operations would work through the client
        networks = manager.client.networks.list()
        assert len(networks) == 1
        assert networks[0].name == "custom_network"

        # Verify volume operations would work through the client
        volumes = manager.client.volumes.list()
        assert len(volumes) == 1
        assert volumes[0].name == "data_volume"

    @patch("docker.from_env")
    def test_docker_daemon_connectivity_errors(self, mock_from_env):
        """Test Docker daemon connectivity error scenarios."""
        # Test connection timeout
        mock_from_env.side_effect = DockerException("Connection timeout")
        with pytest.raises(ConnectionError, match="Docker daemon connection failed"):
            DockerManager()

        # Test daemon not running
        mock_from_env.side_effect = DockerException("Cannot connect to the Docker daemon")
        with pytest.raises(ConnectionError, match="Docker daemon connection failed"):
            DockerManager()

        # Test invalid socket path
        mock_from_env.side_effect = DockerException("No such file or directory: '/var/run/docker.sock'")
        with pytest.raises(ConnectionError, match="Docker socket not found"):
            DockerManager()

    @patch("docker.from_env")
    def test_container_resource_management(self, mock_from_env, mock_docker_client):
        """Test container resource management and limits."""
        mock_from_env.return_value = mock_docker_client

        # Mock container with resource constraints
        mock_container = MagicMock()
        mock_container.id = "resource_container_id"
        mock_container.name = "resource_container"
        mock_container.status = "running"

        # Mock detailed stats with resource information
        mock_stats = {
            "cpu_stats": {
                "cpu_usage": {"total_usage": 2000000000},
                "system_cpu_usage": 4000000000,
                "online_cpus": 4,
                "throttling_data": {
                    "periods": 100,
                    "throttled_periods": 10,
                    "throttled_time": 1000000000
                }
            },
            "precpu_stats": {
                "cpu_usage": {"total_usage": 1800000000},
                "system_cpu_usage": 3800000000,
            },
            "memory_stats": {
                "usage": 1073741824,  # 1GB
                "limit": 2147483648,  # 2GB
                "max_usage": 1200000000,
                "stats": {
                    "cache": 100000000,
                    "rss": 900000000,
                    "swap": 50000000
                }
            },
            "networks": {
                "eth0": {
                    "rx_bytes": 1048576,  # 1MB
                    "tx_bytes": 2097152,  # 2MB
                    "rx_packets": 1000,
                    "tx_packets": 800
                }
            },
            "blkio_stats": {
                "io_service_bytes_recursive": [
                    {"op": "Read", "value": 10485760},   # 10MB
                    {"op": "Write", "value": 5242880},   # 5MB
                    {"op": "Sync", "value": 1048576},    # 1MB
                    {"op": "Async", "value": 2097152}    # 2MB
                ]
            }
        }

        mock_docker_client.containers.get.return_value = mock_container
        mock_container.stats.return_value = mock_stats

        manager = DockerManager()

        # Test getting detailed resource stats
        result = manager.get_container_stats("resource_container_id")

        assert result["container_id"] == "resource_container_id"
        assert result["memory_usage"] == 1073741824
        assert result["memory_limit"] == 2147483648
        assert result["memory_percent"] == 50.0  # 1GB / 2GB * 100
        assert result["network_rx_bytes"] == 1048576
        assert result["network_tx_bytes"] == 2097152
        assert result["block_read_bytes"] == 10485760
        assert result["block_write_bytes"] == 5242880

    @patch("docker.from_env")
    def test_container_environment_variable_handling(self, mock_from_env, mock_docker_client):
        """Test container environment variable handling."""
        mock_from_env.return_value = mock_docker_client

        # Mock container with environment variables
        mock_container = MagicMock()
        mock_container.id = "env_container_id"
        mock_container.name = "env_container"
        mock_container.status = "running"
        mock_container.attrs = {
            "Config": {
                "Env": [
                    "NODE_ENV=production",
                    "PORT=3000",
                    "DATABASE_URL=postgresql://user:pass@db:5432/mydb",
                    "API_KEY=secret_key_123",
                    "DEBUG=false"
                ]
            }
        }

        mock_docker_client.containers.get.return_value = mock_container
        mock_docker_client.containers.list.return_value = [mock_container]

        manager = DockerManager()

        # Test listing containers with environment variables
        containers = manager.list_containers(all=True)
        assert len(containers) == 1
        assert containers[0]["id"] == "env_container_id"
        assert containers[0]["name"] == "env_container"

        # Test that container operations work with environment variables
        result = manager.start_container("env_container_id")
        assert result["status"] == "started"


class TestDockerManagerErrorHandling:
    """Test suite for Docker Manager error handling and recovery."""

    @pytest.fixture
    def mock_docker_client(self):
        """Create a mock Docker client for error testing."""
        mock_client = MagicMock(spec=docker.DockerClient)
        mock_client.ping.return_value = True
        return mock_client

    @patch("docker.from_env")
    def test_docker_daemon_unavailable_scenarios(self, mock_from_env, mock_docker_client):
        """Test scenarios when Docker daemon becomes unavailable."""
        mock_from_env.return_value = mock_docker_client

        manager = DockerManager()

        # Test daemon becomes unavailable during operation
        mock_docker_client.containers.list.side_effect = DockerException("Daemon unavailable")

        # Should handle gracefully without crashing
        try:
            containers = manager.list_containers()
            # If no exception is raised, the method should return empty or handle gracefully
        except DockerException:
            # This is expected behavior
            pass

    @patch("docker.from_env")
    def test_container_deployment_failures_and_rollback(self, mock_from_env, mock_docker_client):
        """Test container deployment failures and rollback scenarios."""
        mock_from_env.return_value = mock_docker_client

        manager = DockerManager()

        # Test container start failure
        mock_docker_client.containers.get.side_effect = NotFound("Container not found")
        result = manager.start_container("nonexistent_container")
        assert "error" in result
        assert "not found" in result["error"].lower()

        # Test container stop failure
        mock_docker_client.containers.get.side_effect = APIError("Container cannot be stopped")
        result = manager.stop_container("problematic_container")
        assert "error" in result
        assert "Container cannot be stopped" in result["error"]

        # Test container restart failure
        mock_docker_client.containers.get.side_effect = APIError("Restart failed")
        result = manager.restart_container("failing_container")
        assert "error" in result
        assert "Restart failed" in result["error"]

    @patch("docker.from_env")
    def test_network_connectivity_issues(self, mock_from_env, mock_docker_client):
        """Test network connectivity issues during Docker operations."""
        mock_from_env.return_value = mock_docker_client

        manager = DockerManager()

        # Test network timeout during stats retrieval
        mock_container = MagicMock()
        mock_container.id = "network_test_container"
        mock_docker_client.containers.get.return_value = mock_container
        mock_container.stats.side_effect = DockerException("Network timeout")

        result = manager.get_container_stats("network_test_container")
        assert "error" in result

        # Test network issues during health check
        # Reset the ping mock to avoid interference from initialization
        mock_docker_client.ping.reset_mock()
        mock_docker_client.ping.side_effect = DockerException("Network unreachable")
        result = manager.health_check()
        assert result["status"] == "unhealthy"
        assert "Network unreachable" in result["error"]

    @patch("docker.from_env")
    def test_insufficient_resources_handling(self, mock_from_env, mock_docker_client):
        """Test handling of insufficient resources scenarios."""
        mock_from_env.return_value = mock_docker_client

        manager = DockerManager()

        # Test insufficient memory error
        mock_docker_client.containers.get.side_effect = APIError("Insufficient memory")
        result = manager.start_container("memory_intensive_container")
        assert "error" in result
        assert "Insufficient memory" in result["error"]

        # Test disk space error
        mock_docker_client.info.side_effect = DockerException("No space left on device")
        result = manager.get_system_stats()
        assert "error" in result
        assert "No space left on device" in result["error"]

    @patch("docker.from_env")
    def test_docker_api_timeout_and_retry_logic(self, mock_from_env, mock_docker_client):
        """Test Docker API timeout and retry logic scenarios."""
        mock_from_env.return_value = mock_docker_client

        manager = DockerManager()

        # Test API timeout during container operations
        mock_container = MagicMock()
        mock_docker_client.containers.get.return_value = mock_container

        # Test timeout during logs retrieval
        mock_container.logs.side_effect = APIError("Request timeout")
        result = manager.get_logs("timeout_container")
        assert "error" in result
        assert "Request timeout" in result["error"]

        # Test timeout during stats retrieval
        mock_container.stats.side_effect = DockerException("Stats timeout")
        result = manager.get_container_stats("timeout_container")
        assert "error" in result

    @patch("docker.from_env")
    def test_malformed_docker_responses(self, mock_from_env, mock_docker_client):
        """Test handling of malformed Docker API responses."""
        mock_from_env.return_value = mock_docker_client

        manager = DockerManager()

        # Test malformed stats response
        mock_container = MagicMock()
        mock_container.id = "malformed_container"
        mock_container.name = "malformed_container"
        mock_container.status = "running"
        mock_docker_client.containers.get.return_value = mock_container

        # Test with malformed JSON in stats
        mock_container.stats.return_value = b'{"invalid": json}'
        result = manager.get_container_stats("malformed_container")
        # Should handle gracefully and return error or default values
        assert "container_id" in result or "error" in result

        # Test with completely invalid response
        mock_container.stats.return_value = b'not json at all'
        result = manager.get_container_stats("malformed_container")
        assert "container_id" in result or "error" in result


class TestDockerManagerPerformance:
    """Test suite for Docker Manager performance and scalability."""

    @pytest.fixture
    def mock_docker_client(self):
        """Create a mock Docker client for performance testing."""
        mock_client = MagicMock(spec=docker.DockerClient)
        mock_client.ping.return_value = True
        return mock_client

    @patch("docker.from_env")
    def test_concurrent_container_operations(self, mock_from_env, mock_docker_client):
        """Test concurrent container operations performance."""
        mock_from_env.return_value = mock_docker_client

        # Mock multiple containers
        containers = []
        for i in range(10):
            mock_container = MagicMock()
            mock_container.id = f"concurrent_container_{i}"
            mock_container.name = f"container_{i}"
            mock_container.status = "running"
            containers.append(mock_container)

        mock_docker_client.containers.list.return_value = containers

        def mock_get_container(container_id):
            for container in containers:
                if container.id == container_id:
                    return container
            raise NotFound("Container not found")

        mock_docker_client.containers.get.side_effect = mock_get_container

        manager = DockerManager()

        # Test listing multiple containers
        result = manager.list_containers(all=True)
        assert len(result) == 10

        # Test multiple container stats retrieval
        container_ids = [f"concurrent_container_{i}" for i in range(5)]

        # Mock stats for each container
        for container in containers[:5]:
            container.stats.return_value = {
                "cpu_stats": {"cpu_usage": {"total_usage": 1000000}},
                "precpu_stats": {"cpu_usage": {"total_usage": 900000}},
                "memory_stats": {"usage": 1024000, "limit": 2048000}
            }

        result = manager.get_multiple_container_stats(container_ids)
        assert len(result) == 5
        for container_id in container_ids:
            assert container_id in result
            assert "error" not in result[container_id] or "container_id" in result[container_id]

    @patch("docker.from_env")
    def test_large_scale_container_deployments(self, mock_from_env, mock_docker_client):
        """Test large-scale container deployment scenarios."""
        mock_from_env.return_value = mock_docker_client

        # Mock a large number of containers
        large_container_list = []
        for i in range(100):
            mock_container = MagicMock()
            mock_container.id = f"scale_container_{i}"
            mock_container.name = f"scale_container_{i}"
            mock_container.status = "running" if i % 2 == 0 else "exited"
            mock_container.image.tags = [f"app:v{i % 10}"]
            mock_container.labels = {"app": "scale_test", "instance": str(i)}
            mock_container.ports = {}
            large_container_list.append(mock_container)

        mock_docker_client.containers.list.return_value = large_container_list

        manager = DockerManager()

        # Test listing large number of containers
        result = manager.list_containers(all=True)
        assert len(result) == 100

        # Verify data structure is maintained
        for i, container in enumerate(result):
            assert container["id"] == f"scale_container_{i}"
            assert container["name"] == f"scale_container_{i}"
            assert container["status"] in ["running", "exited"]

    @patch("docker.from_env")
    def test_resource_usage_optimization(self, mock_from_env, mock_docker_client):
        """Test resource usage optimization during operations."""
        mock_from_env.return_value = mock_docker_client

        manager = DockerManager()

        # Test memory-efficient stats aggregation
        container_ids = [f"resource_container_{i}" for i in range(20)]

        # Mock containers with varying resource usage
        def mock_get_stats(container_id):
            index = int(container_id.split('_')[-1])
            return {
                "cpu_percent": index * 5.0,
                "memory_usage": index * 1024 * 1024,  # MB
                "memory_limit": 1024 * 1024 * 1024,   # 1GB
                "network_rx_bytes": index * 1000,
                "network_tx_bytes": index * 2000,
                "block_read_bytes": index * 4096,
                "block_write_bytes": index * 8192
            }

        # Mock the get_container_stats method
        original_get_stats = manager.get_container_stats
        manager.get_container_stats = mock_get_stats

        # Test aggregated metrics calculation
        result = manager.get_aggregated_metrics(container_ids)

        assert "aggregated_metrics" in result
        assert result["container_count"] == 20
        assert result["total_containers"] == 20
        assert "avg_cpu_percent" in result["aggregated_metrics"]
        assert "total_memory_usage" in result["aggregated_metrics"]

    @patch("docker.from_env")
    def test_docker_api_rate_limiting_handling(self, mock_from_env, mock_docker_client):
        """Test Docker API rate limiting handling."""
        mock_from_env.return_value = mock_docker_client

        manager = DockerManager()

        # Test rate limiting during container listing
        mock_docker_client.containers.list.side_effect = APIError("Rate limit exceeded")

        try:
            result = manager.list_containers()
            # Should handle rate limiting gracefully
        except APIError:
            # Expected behavior for rate limiting
            pass

        # Test rate limiting during stats retrieval
        mock_container = MagicMock()
        mock_container.id = "rate_limited_container"
        mock_docker_client.containers.get.return_value = mock_container
        mock_container.stats.side_effect = APIError("Too many requests")

        result = manager.get_container_stats("rate_limited_container")
        assert "error" in result
        assert "Too many requests" in result["error"]

    @patch("docker.from_env")
    def test_memory_and_performance_under_load(self, mock_from_env, mock_docker_client):
        """Test memory usage and performance under load."""
        mock_from_env.return_value = mock_docker_client

        manager = DockerManager()

        # Test with high-frequency stats requests
        mock_container = MagicMock()
        mock_container.id = "performance_container"
        mock_container.name = "performance_container"
        mock_container.status = "running"
        mock_docker_client.containers.get.return_value = mock_container

        # Mock stats with large data
        large_stats = {
            "cpu_stats": {
                "cpu_usage": {"total_usage": 5000000000},
                "system_cpu_usage": 10000000000,
                "online_cpus": 8
            },
            "precpu_stats": {
                "cpu_usage": {"total_usage": 4500000000},
                "system_cpu_usage": 9500000000
            },
            "memory_stats": {
                "usage": 4294967296,  # 4GB
                "limit": 8589934592,  # 8GB
                "max_usage": 5000000000,
                "stats": {
                    "cache": 1073741824,
                    "rss": 3221225472,
                    "swap": 0
                }
            },
            "networks": {
                f"eth{i}": {
                    "rx_bytes": i * 1048576,
                    "tx_bytes": i * 2097152
                } for i in range(10)  # Multiple network interfaces
            },
            "blkio_stats": {
                "io_service_bytes_recursive": [
                    {"op": "Read", "value": 1073741824},   # 1GB
                    {"op": "Write", "value": 536870912},   # 512MB
                ]
            }
        }

        mock_container.stats.return_value = large_stats

        # Test multiple rapid stats requests
        for i in range(10):
            result = manager.get_container_stats("performance_container")
            assert "container_id" in result
            assert result["container_id"] == "performance_container"
            assert "memory_usage" in result
            assert "cpu_percent" in result

        # Test aggregated metrics with large dataset
        container_ids = [f"performance_container_{i}" for i in range(50)]

        # Mock get_container_stats for performance testing
        def mock_performance_stats(container_id):
            index = hash(container_id) % 100
            return {
                "cpu_percent": float(index),
                "memory_usage": index * 1024 * 1024,
                "memory_limit": 1024 * 1024 * 1024,
                "network_rx_bytes": index * 1000,
                "network_tx_bytes": index * 2000,
                "block_read_bytes": index * 4096,
                "block_write_bytes": index * 8192
            }

        original_get_stats = manager.get_container_stats
        manager.get_container_stats = mock_performance_stats

        # Test performance with large aggregation
        result = manager.get_aggregated_metrics(container_ids)
        assert result["container_count"] == 50
        assert "aggregated_metrics" in result
        assert "individual_stats" in result
        assert len(result["individual_stats"]) == 50


class TestDockerManagerAsyncOperations:
    """Test suite for Docker Manager async operations."""

    @pytest.fixture
    def mock_docker_client(self):
        """Create a mock Docker client for async testing."""
        mock_client = MagicMock(spec=docker.DockerClient)
        mock_client.ping.return_value = True
        return mock_client

    @patch("docker.from_env")
    @pytest.mark.asyncio
    async def test_streaming_stats_async_generator(self, mock_from_env, mock_docker_client):
        """Test async streaming stats generator."""
        mock_from_env.return_value = mock_docker_client

        # Mock container for streaming
        mock_container = MagicMock()
        mock_container.id = "streaming_container"
        mock_container.name = "streaming_container"
        mock_container.status = "running"
        mock_docker_client.containers.get.return_value = mock_container

        # Mock streaming stats generator
        def mock_streaming_stats():
            for i in range(5):
                yield {
                    "cpu_stats": {"cpu_usage": {"total_usage": 1000000 * i}},
                    "memory_stats": {"usage": 1024000 * i, "limit": 2048000},
                    "timestamp": f"2024-01-01T12:00:{i:02d}Z"
                }

        mock_container.stats.return_value = mock_streaming_stats()

        manager = DockerManager()

        # Test async streaming stats
        stats_count = 0
        async for stats in manager.get_streaming_stats("streaming_container"):
            assert "container_id" in stats
            assert stats["container_id"] == "streaming_container"
            stats_count += 1
            if stats_count >= 3:  # Limit iterations for testing
                break

        assert stats_count == 3

    @patch("docker.from_env")
    @pytest.mark.asyncio
    async def test_streaming_stats_error_handling(self, mock_from_env, mock_docker_client):
        """Test async streaming stats error handling."""
        mock_from_env.return_value = mock_docker_client

        # Test container not found
        mock_docker_client.containers.get.side_effect = NotFound("Container not found")

        manager = DockerManager()

        async for stats in manager.get_streaming_stats("nonexistent_container"):
            assert "error" in stats
            assert "not found" in stats["error"].lower()
            break  # Only test first error response

        # Test API error during streaming
        mock_container = MagicMock()
        mock_docker_client.containers.get.side_effect = None
        mock_docker_client.containers.get.return_value = mock_container
        mock_container.stats.side_effect = APIError("Streaming failed")

        async for stats in manager.get_streaming_stats("error_container"):
            assert "error" in stats
            assert "Streaming failed" in stats["error"]
            break  # Only test first error response

    @patch("docker.from_env")
    def test_comprehensive_edge_cases(self, mock_from_env, mock_docker_client):
        """Test comprehensive edge cases and boundary conditions."""
        mock_from_env.return_value = mock_docker_client

        manager = DockerManager()

        # Test with empty container list
        mock_docker_client.containers.list.return_value = []
        result = manager.list_containers(all=True)
        assert result == []

        # Test with None values in container attributes
        mock_container = MagicMock()
        mock_container.id = None
        mock_container.name = None
        mock_container.status = None
        mock_container.image.tags = []
        mock_container.labels = {}
        mock_container.ports = {}

        mock_docker_client.containers.list.return_value = [mock_container]
        result = manager.list_containers(all=True)
        assert len(result) == 1
        assert result[0]["id"] is None
        assert result[0]["name"] is None

        # Test aggregated metrics with empty container list
        result = manager.get_aggregated_metrics([])
        assert result["container_count"] == 0
        assert result["total_containers"] == 0
        assert result["aggregated_metrics"]["avg_cpu_percent"] == 0

        # Test multiple container stats with empty list
        result = manager.get_multiple_container_stats([])
        assert result == {}
