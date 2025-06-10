"""
Tests for DockerManager metrics functionality.
"""

from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pytest
from docker.errors import APIError, NotFound

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

    @pytest.mark.asyncio
    async def test_get_streaming_stats_success(self, docker_manager, mock_docker_client, mock_container_stats):
        """Test successful streaming stats retrieval."""
        # Setup mock container
        mock_container = MagicMock()
        mock_container.id = "test_container_id"
        mock_container.name = "test_container"
        mock_container.status = "running"

        # Setup stats generator with multiple stats
        stats_data = [mock_container_stats, mock_container_stats]
        mock_stats_generator = iter(stats_data)
        mock_container.stats.return_value = mock_stats_generator

        mock_docker_client.containers.get.return_value = mock_container

        # Test the async generator
        results = []
        async for stats in docker_manager.get_streaming_stats("test_container_id"):
            results.append(stats)
            if len(results) >= 2:  # Limit to avoid infinite loop
                break

        # Assertions
        assert len(results) == 2
        for result in results:
            assert "container_id" in result
            assert "container_name" in result
            assert result["container_id"] == "test_container_id"
            assert result["container_name"] == "test_container"

    @pytest.mark.asyncio
    async def test_get_streaming_stats_not_found(self, docker_manager, mock_docker_client):
        """Test streaming stats when container not found."""
        from docker.errors import NotFound

        mock_docker_client.containers.get.side_effect = NotFound("Container not found")

        # Test the async generator
        results = []
        async for stats in docker_manager.get_streaming_stats("nonexistent_container"):
            results.append(stats)
            break  # Only get first result

        assert len(results) == 1
        assert "error" in results[0]
        assert "Container nonexistent_container not found" in results[0]["error"]

    def test_get_multiple_container_stats_success(self, docker_manager, mock_docker_client, mock_container_stats):
        """Test successful multiple container stats retrieval."""
        # Setup mock containers
        container_ids = ["container1", "container2", "container3"]

        def mock_get_stats(container_id):
            mock_container = MagicMock()
            mock_container.id = container_id
            mock_container.name = f"name_{container_id}"
            mock_container.status = "running"

            mock_stats_generator = iter([mock_container_stats])
            mock_container.stats.return_value = mock_stats_generator

            return mock_container

        mock_docker_client.containers.get.side_effect = mock_get_stats

        # Test the method
        result = docker_manager.get_multiple_container_stats(container_ids)

        # Assertions
        assert len(result) == 3
        for container_id in container_ids:
            assert container_id in result
            assert "container_id" in result[container_id]
            assert result[container_id]["container_id"] == container_id
            assert result[container_id]["container_name"] == f"name_{container_id}"

    def test_get_multiple_container_stats_with_errors(self, docker_manager, mock_docker_client, mock_container_stats):
        """Test multiple container stats with some containers having errors."""
        from docker.errors import NotFound

        container_ids = ["container1", "container2", "container3"]

        def mock_get_stats(container_id):
            if container_id == "container2":
                raise NotFound("Container not found")

            mock_container = MagicMock()
            mock_container.id = container_id
            mock_container.name = f"name_{container_id}"
            mock_container.status = "running"

            mock_stats_generator = iter([mock_container_stats])
            mock_container.stats.return_value = mock_stats_generator

            return mock_container

        mock_docker_client.containers.get.side_effect = mock_get_stats

        # Test the method
        result = docker_manager.get_multiple_container_stats(container_ids)

        # Assertions
        assert len(result) == 3
        assert "container_id" in result["container1"]
        assert "error" in result["container2"]
        assert "container_id" in result["container3"]

    def test_get_aggregated_metrics_success(self, docker_manager, mock_docker_client, mock_container_stats):
        """Test successful aggregated metrics calculation."""
        container_ids = ["container1", "container2"]

        def mock_get_stats(container_id):
            mock_container = MagicMock()
            mock_container.id = container_id
            mock_container.name = f"name_{container_id}"
            mock_container.status = "running"

            mock_stats_generator = iter([mock_container_stats])
            mock_container.stats.return_value = mock_stats_generator

            return mock_container

        mock_docker_client.containers.get.side_effect = mock_get_stats

        # Test the method
        result = docker_manager.get_aggregated_metrics(container_ids)

        # Assertions
        assert "timestamp" in result
        assert "container_count" in result
        assert "total_containers" in result
        assert "aggregated_metrics" in result
        assert "individual_stats" in result

        assert result["container_count"] == 2
        assert result["total_containers"] == 2

        aggregated = result["aggregated_metrics"]
        assert "avg_cpu_percent" in aggregated
        assert "total_memory_usage" in aggregated
        assert "total_memory_limit" in aggregated
        assert "avg_memory_percent" in aggregated
        assert "total_network_rx_bytes" in aggregated
        assert "total_network_tx_bytes" in aggregated

        # Check that values are aggregated correctly
        assert aggregated["total_memory_usage"] == 134217728 * 2  # 2 containers
        assert aggregated["total_memory_limit"] == 536870912 * 2  # 2 containers
        assert aggregated["total_network_rx_bytes"] == 1024 * 2  # 2 containers
        assert aggregated["total_network_tx_bytes"] == 2048 * 2  # 2 containers

    def test_get_aggregated_metrics_empty_list(self, docker_manager):
        """Test aggregated metrics with empty container list."""
        result = docker_manager.get_aggregated_metrics([])

        # Should return aggregated metrics with zero values
        assert "timestamp" in result
        assert result["container_count"] == 0
        assert result["total_containers"] == 0

    def test_get_aggregated_metrics_with_errors(self, docker_manager, mock_docker_client, mock_container_stats):
        """Test aggregated metrics with some containers having errors."""
        from docker.errors import NotFound

        container_ids = ["container1", "container2", "container3"]

        def mock_get_stats(container_id):
            if container_id == "container2":
                raise NotFound("Container not found")

            mock_container = MagicMock()
            mock_container.id = container_id
            mock_container.name = f"name_{container_id}"
            mock_container.status = "running"

            mock_stats_generator = iter([mock_container_stats])
            mock_container.stats.return_value = mock_stats_generator

            return mock_container

        mock_docker_client.containers.get.side_effect = mock_get_stats

        # Test the method
        result = docker_manager.get_aggregated_metrics(container_ids)

        # Assertions - should only aggregate valid containers
        assert result["container_count"] == 2  # Only 2 valid containers
        assert result["total_containers"] == 3  # Total requested containers

        # Should have individual stats for all containers (including errors)
        assert len(result["individual_stats"]) == 3
        assert "error" in result["individual_stats"]["container2"]

    @patch("docker.from_env")
    def test_get_streaming_stats_error_handling(self, mock_from_env, mock_docker_client):
        """Test error handling in streaming stats."""
        mock_from_env.return_value = mock_docker_client

        docker_manager = DockerManager()

        # Test container not found
        mock_docker_client.containers.get.side_effect = NotFound("Container not found")

        async def test_streaming():
            async for result in docker_manager.get_streaming_stats("nonexistent_container"):
                assert "error" in result
                assert "Container nonexistent_container not found" in result["error"]
                break

        # Run the async test
        import asyncio
        asyncio.run(test_streaming())

        # Test API error during streaming
        mock_container = MagicMock()
        mock_container.stats.side_effect = APIError("Streaming failed")
        mock_docker_client.containers.get.side_effect = None
        mock_docker_client.containers.get.return_value = mock_container

        async def test_api_error():
            async for result in docker_manager.get_streaming_stats("test_container"):
                assert "error" in result
                assert "Streaming failed" in result["error"]
                break

        asyncio.run(test_api_error())

        # Test unexpected error during streaming
        mock_container.stats.side_effect = Exception("Unexpected streaming error")

        async def test_unexpected_error():
            async for result in docker_manager.get_streaming_stats("test_container"):
                assert "error" in result
                assert "Unexpected streaming error" in result["error"]
                break

        asyncio.run(test_unexpected_error())

    @patch("docker.from_env")
    def test_parse_container_stats_complex_scenarios(self, mock_from_env, mock_docker_client):
        """Test complex container stats parsing scenarios."""
        mock_from_env.return_value = mock_docker_client

        docker_manager = DockerManager()

        mock_container = MagicMock()
        mock_container.id = "test_id"
        mock_container.name = "test_name"
        mock_container.status = "running"

        # Test with complex network stats (multiple interfaces)
        complex_stats = {
            "cpu_stats": {
                "cpu_usage": {"total_usage": 1000000000},
                "system_cpu_usage": 2000000000,
                "online_cpus": 4,
            },
            "precpu_stats": {
                "cpu_usage": {"total_usage": 900000000},
                "system_cpu_usage": 1900000000,
            },
            "memory_stats": {
                "usage": 134217728,
                "limit": 536870912,
            },
            "networks": {
                "eth0": {"rx_bytes": 1024, "tx_bytes": 2048},
                "eth1": {"rx_bytes": 512, "tx_bytes": 1024},
                "lo": {"rx_bytes": 256, "tx_bytes": 512},
            },
            "blkio_stats": {
                "io_service_bytes_recursive": [
                    {"op": "Read", "value": 4096},
                    {"op": "Write", "value": 8192},
                    {"op": "Read", "value": 2048},
                    {"op": "Write", "value": 4096},
                ]
            },
        }

        result = docker_manager._parse_container_stats(complex_stats, mock_container)

        # Verify aggregated network stats
        assert result["network_rx_bytes"] == 1792  # 1024 + 512 + 256
        assert result["network_tx_bytes"] == 3584  # 2048 + 1024 + 512

        # Verify aggregated block I/O stats
        assert result["block_read_bytes"] == 6144  # 4096 + 2048
        assert result["block_write_bytes"] == 12288  # 8192 + 4096

        # Verify CPU calculation with multiple cores
        assert result["cpu_percent"] == 400.0  # (100000000 / 100000000) * 4 * 100

    @patch("docker.from_env")
    def test_parse_container_stats_missing_data_scenarios(self, mock_from_env, mock_docker_client):
        """Test container stats parsing with various missing data scenarios."""
        mock_from_env.return_value = mock_docker_client

        docker_manager = DockerManager()

        mock_container = MagicMock()
        mock_container.id = "test_id"
        mock_container.name = "test_name"
        mock_container.status = "running"

        # Test with missing memory limit (should handle division by zero)
        stats_no_memory_limit = {
            "memory_stats": {"usage": 134217728}  # No limit field
        }

        result = docker_manager._parse_container_stats(stats_no_memory_limit, mock_container)
        assert result["memory_percent"] == 0.0
        assert result["memory_limit"] == 0

        # Test with missing network data
        stats_no_networks = {
            "memory_stats": {"usage": 134217728, "limit": 536870912}
        }

        result = docker_manager._parse_container_stats(stats_no_networks, mock_container)
        assert result["network_rx_bytes"] == 0
        assert result["network_tx_bytes"] == 0

        # Test with missing block I/O data
        stats_no_blkio = {
            "memory_stats": {"usage": 134217728, "limit": 536870912}
        }

        result = docker_manager._parse_container_stats(stats_no_blkio, mock_container)
        assert result["block_read_bytes"] == 0
        assert result["block_write_bytes"] == 0
