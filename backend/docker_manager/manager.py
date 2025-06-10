try:
    import docker
    from docker.errors import APIError, DockerException, NotFound
except ImportError:
    # Handle case where docker is not available
    docker = None
    NotFound = Exception
    APIError = Exception
    DockerException = Exception

import logging
from datetime import datetime
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class DockerManager:
    def __init__(self):
        if docker is None:
            raise ImportError(
                "Docker SDK is not available. Please install docker package."
            )

        try:
            self.client = docker.from_env()
            # Test the connection
            self.client.ping()
            logger.info("Docker client initialized successfully")
        except DockerException as e:
            logger.error(f"Failed to connect to Docker daemon: {e}")
            # Check common issues
            if "Permission denied" in str(e):
                raise ConnectionError(
                    "Permission denied accessing Docker socket. "
                    "Ensure the user is in the docker group and has access to /var/run/docker.sock"
                ) from e
            elif "No such file or directory" in str(e):
                raise ConnectionError(
                    "Docker socket not found. Ensure Docker is running and socket is mounted."
                ) from e
            else:
                raise ConnectionError(f"Docker daemon connection failed: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error initializing Docker client: {e}")
            raise ConnectionError(f"Failed to initialize Docker client: {e}") from e

    def list_containers(self, all: bool = False):
        containers = self.client.containers.list(all=all)
        result = []
        for c in containers:
            result.append(
                {
                    "id": c.id,
                    "name": c.name,
                    "status": c.status,
                    "image": c.image.tags,
                    "ports": c.ports,
                    "labels": c.labels,
                }
            )
        return result

    def start_container(self, container_id: str):
        try:
            container = self.client.containers.get(container_id)
            container.start()
            return {"status": "started", "id": container_id}
        except NotFound:
            return {"error": f"Container {container_id} not found"}
        except APIError as e:
            return {"error": str(e)}

    def stop_container(self, container_id: str):
        try:
            container = self.client.containers.get(container_id)
            container.stop()
            return {"status": "stopped", "id": container_id}
        except NotFound:
            return {"error": f"Container {container_id} not found"}
        except APIError as e:
            return {"error": str(e)}

    def restart_container(self, container_id: str):
        try:
            container = self.client.containers.get(container_id)
            container.restart()
            return {"status": "restarted", "id": container_id}
        except NotFound:
            return {"error": f"Container {container_id} not found"}
        except APIError as e:
            return {"error": str(e)}

    def get_logs(self, container_id: str, tail: int = 100):
        try:
            container = self.client.containers.get(container_id)
            logs = container.logs(tail=tail).decode("utf-8")
            return {"id": container_id, "logs": logs}
        except NotFound:
            return {"error": f"Container {container_id} not found"}
        except APIError as e:
            return {"error": str(e)}

    def get_container_stats(
        self, container_id: str, stream: bool = False
    ) -> Dict[str, Any]:
        """
        Get real-time statistics for a container.

        Args:
            container_id: Container ID or name
            stream: If True, return streaming stats (for real-time monitoring)

        Returns:
            Dictionary containing container statistics
        """
        try:
            container = self.client.containers.get(container_id)

            # Get container stats (non-streaming by default)
            if stream:
                # For streaming, return the generator
                stats_generator = container.stats(stream=True, decode=True)
                # Return the generator for streaming
                return {"stats_stream": stats_generator}
            else:
                # For single snapshot, try different approaches based on Docker SDK version
                try:
                    # First try with stream=False (newer Docker SDK versions)
                    raw_stats = container.stats(stream=False, decode=True)

                    # If we get a dict directly, use it
                    if isinstance(raw_stats, dict):
                        stats = raw_stats
                    # If we get bytes, parse JSON
                    elif isinstance(raw_stats, bytes):
                        import json
                        stats = json.loads(raw_stats.decode('utf-8'))
                    else:
                        # If it's a generator or other iterable, get first result
                        try:
                            stats_result = next(iter(raw_stats))
                            if isinstance(stats_result, bytes):
                                import json
                                stats = json.loads(stats_result.decode('utf-8'))
                            else:
                                stats = stats_result
                        except (StopIteration, TypeError):
                            return {"error": "No stats available for container"}

                except Exception as stream_false_error:
                    # Fallback to stream=True approach for older Docker SDK versions
                    try:
                        stats_generator = container.stats(stream=True, decode=True)

                        # Check if it's actually a generator/iterator
                        if hasattr(stats_generator, '__next__') or hasattr(stats_generator, 'next'):
                            # It's a generator, get first result
                            raw_stats = next(stats_generator)
                            # Stop the generator to avoid hanging
                            if hasattr(stats_generator, 'close'):
                                stats_generator.close()
                        else:
                            # It's not a generator, use directly
                            raw_stats = stats_generator

                        # Parse JSON if it's bytes
                        if isinstance(raw_stats, bytes):
                            import json
                            stats = json.loads(raw_stats.decode('utf-8'))
                        else:
                            stats = raw_stats

                    except Exception as stream_true_error:
                        logger.error(f"Both stream=False and stream=True failed for {container_id}. "
                                   f"stream=False error: {stream_false_error}, "
                                   f"stream=True error: {stream_true_error}")
                        return {"error": f"Failed to get stats: {str(stream_true_error)}"}

                return self._parse_container_stats(stats, container)

        except NotFound:
            return {"error": f"Container {container_id} not found"}
        except APIError as e:
            logger.error(f"Docker API error getting stats for {container_id}: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error getting stats for {container_id}: {e}")
            return {"error": str(e)}

    async def get_streaming_stats(self, container_id: str):
        """
        Get streaming statistics for a container (async generator).

        Args:
            container_id: Container ID or name

        Yields:
            Dictionary containing parsed container statistics
        """
        try:
            container = self.client.containers.get(container_id)
            stats_generator = container.stats(stream=True, decode=True)

            for raw_stats in stats_generator:
                # Parse JSON if it's bytes
                if isinstance(raw_stats, bytes):
                    import json
                    stats = json.loads(raw_stats.decode('utf-8'))
                else:
                    stats = raw_stats

                yield self._parse_container_stats(stats, container)

        except NotFound:
            yield {"error": f"Container {container_id} not found"}
        except APIError as e:
            logger.error(f"Docker API error streaming stats for {container_id}: {e}")
            yield {"error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error streaming stats for {container_id}: {e}")
            yield {"error": str(e)}

    def get_multiple_container_stats(self, container_ids: List[str]) -> Dict[str, Any]:
        """
        Get statistics for multiple containers efficiently.

        Args:
            container_ids: List of container IDs or names

        Returns:
            Dictionary mapping container IDs to their statistics
        """
        results = {}

        for container_id in container_ids:
            try:
                stats = self.get_container_stats(container_id)
                results[container_id] = stats
            except Exception as e:
                logger.error(f"Error getting stats for container {container_id}: {e}")
                results[container_id] = {"error": f"Failed to get stats: {str(e)}"}

        return results

    def get_aggregated_metrics(self, container_ids: List[str]) -> Dict[str, Any]:
        """
        Get aggregated metrics across multiple containers.

        Args:
            container_ids: List of container IDs or names

        Returns:
            Dictionary containing aggregated metrics
        """
        try:
            all_stats = self.get_multiple_container_stats(container_ids)

            # Initialize aggregation variables
            total_cpu = 0.0
            total_memory_usage = 0
            total_memory_limit = 0
            total_network_rx = 0
            total_network_tx = 0
            total_block_read = 0
            total_block_write = 0
            valid_containers = 0

            # Aggregate metrics
            for container_id, stats in all_stats.items():
                if "error" not in stats:
                    total_cpu += stats.get("cpu_percent", 0)
                    total_memory_usage += stats.get("memory_usage", 0)
                    total_memory_limit += stats.get("memory_limit", 0)
                    total_network_rx += stats.get("network_rx_bytes", 0)
                    total_network_tx += stats.get("network_tx_bytes", 0)
                    total_block_read += stats.get("block_read_bytes", 0)
                    total_block_write += stats.get("block_write_bytes", 0)
                    valid_containers += 1

            # Calculate averages and totals
            avg_cpu = total_cpu / valid_containers if valid_containers > 0 else 0
            avg_memory_percent = (total_memory_usage / total_memory_limit * 100) if total_memory_limit > 0 else 0

            return {
                "timestamp": datetime.utcnow().isoformat(),
                "container_count": valid_containers,
                "total_containers": len(container_ids),
                "aggregated_metrics": {
                    "avg_cpu_percent": round(avg_cpu, 2),
                    "total_memory_usage": total_memory_usage,
                    "total_memory_limit": total_memory_limit,
                    "avg_memory_percent": round(avg_memory_percent, 2),
                    "total_network_rx_bytes": total_network_rx,
                    "total_network_tx_bytes": total_network_tx,
                    "total_block_read_bytes": total_block_read,
                    "total_block_write_bytes": total_block_write,
                },
                "individual_stats": all_stats,
            }

        except Exception as e:
            logger.error(f"Error getting aggregated metrics: {e}")
            return {"error": f"Failed to get aggregated metrics: {str(e)}"}

    def _parse_container_stats(
        self, stats: Dict[str, Any], container
    ) -> Dict[str, Any]:
        """
        Parse raw Docker stats into a standardized format.

        Args:
            stats: Raw stats from Docker API
            container: Docker container object

        Returns:
            Parsed statistics dictionary
        """
        try:
            # Extract basic container info
            parsed_stats = {
                "container_id": container.id,
                "container_name": container.name,
                "timestamp": datetime.utcnow().isoformat(),
                "status": container.status,
            }

            # Parse CPU stats
            cpu_stats = stats.get("cpu_stats", {})
            precpu_stats = stats.get("precpu_stats", {})

            if cpu_stats and precpu_stats:
                cpu_percent = self._calculate_cpu_percent(cpu_stats, precpu_stats)
                parsed_stats["cpu_percent"] = round(cpu_percent, 2)
            else:
                parsed_stats["cpu_percent"] = 0.0

            # Parse memory stats
            memory_stats = stats.get("memory_stats", {})
            if memory_stats:
                memory_usage = memory_stats.get("usage", 0)
                memory_limit = memory_stats.get("limit", 0)

                parsed_stats["memory_usage"] = memory_usage
                parsed_stats["memory_limit"] = memory_limit

                if memory_limit > 0:
                    memory_percent = (memory_usage / memory_limit) * 100
                    parsed_stats["memory_percent"] = round(memory_percent, 2)
                else:
                    parsed_stats["memory_percent"] = 0.0
            else:
                parsed_stats.update(
                    {"memory_usage": 0, "memory_limit": 0, "memory_percent": 0.0}
                )

            # Parse network stats
            networks = stats.get("networks", {})
            total_rx_bytes = 0
            total_tx_bytes = 0

            for network_data in networks.values():
                total_rx_bytes += network_data.get("rx_bytes", 0)
                total_tx_bytes += network_data.get("tx_bytes", 0)

            parsed_stats["network_rx_bytes"] = total_rx_bytes
            parsed_stats["network_tx_bytes"] = total_tx_bytes

            # Parse block I/O stats
            blkio_stats = stats.get("blkio_stats", {})
            io_service_bytes = blkio_stats.get("io_service_bytes_recursive", [])

            total_read_bytes = 0
            total_write_bytes = 0

            for io_stat in io_service_bytes:
                if io_stat.get("op") == "Read":
                    total_read_bytes += io_stat.get("value", 0)
                elif io_stat.get("op") == "Write":
                    total_write_bytes += io_stat.get("value", 0)

            parsed_stats["block_read_bytes"] = total_read_bytes
            parsed_stats["block_write_bytes"] = total_write_bytes

            return parsed_stats

        except Exception as e:
            logger.error(f"Error parsing container stats: {e}")
            return {
                "container_id": container.id if container else "unknown",
                "container_name": container.name if container else "unknown",
                "timestamp": datetime.utcnow().isoformat(),
                "error": f"Failed to parse stats: {str(e)}",
            }

    def _calculate_cpu_percent(
        self, cpu_stats: Dict[str, Any], precpu_stats: Dict[str, Any]
    ) -> float:
        """
        Calculate CPU usage percentage from Docker stats.

        Args:
            cpu_stats: Current CPU stats
            precpu_stats: Previous CPU stats

        Returns:
            CPU usage percentage
        """
        try:
            cpu_delta = cpu_stats.get("cpu_usage", {}).get(
                "total_usage", 0
            ) - precpu_stats.get("cpu_usage", {}).get("total_usage", 0)

            system_delta = cpu_stats.get("system_cpu_usage", 0) - precpu_stats.get(
                "system_cpu_usage", 0
            )

            online_cpus = cpu_stats.get("online_cpus", 1)

            if system_delta > 0 and cpu_delta > 0:
                cpu_percent = (cpu_delta / system_delta) * online_cpus * 100.0
                return cpu_percent
            else:
                return 0.0

        except (KeyError, TypeError, ZeroDivisionError):
            return 0.0

    def get_system_stats(self) -> Dict[str, Any]:
        """
        Get system-wide Docker statistics.

        Returns:
            Dictionary containing system statistics
        """
        try:
            # Get system info
            system_info = self.client.info()

            # Get all containers
            all_containers = self.client.containers.list(all=True)
            running_containers = self.client.containers.list(all=False)

            # Calculate container counts by status
            container_counts = {}
            for container in all_containers:
                status = container.status
                container_counts[status] = container_counts.get(status, 0) + 1

            return {
                "timestamp": datetime.utcnow().isoformat(),
                "containers_total": len(all_containers),
                "containers_running": len(running_containers),
                "containers_by_status": container_counts,
                "system_info": {
                    "docker_version": system_info.get("ServerVersion", "unknown"),
                    "total_memory": system_info.get("MemTotal", 0),
                    "cpus": system_info.get("NCPU", 0),
                    "kernel_version": system_info.get("KernelVersion", "unknown"),
                    "operating_system": system_info.get("OperatingSystem", "unknown"),
                    "architecture": system_info.get("Architecture", "unknown"),
                },
            }

        except DockerException as e:
            logger.error(f"Docker error getting system stats: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error getting system stats: {e}")
            return {"error": str(e)}

    def health_check(self):
        """
        Perform a health check on the Docker connection.
        Returns dict with status and details.
        """
        try:
            # Test basic connectivity
            ping_result = self.client.ping()

            # Get Docker version info
            version_info = self.client.version()

            return {
                "status": "healthy",
                "docker_ping": ping_result,
                "docker_version": version_info.get("Version", "unknown"),
                "api_version": version_info.get("ApiVersion", "unknown"),
            }
        except DockerException as e:
            logger.error(f"Docker health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "error_type": "docker_connection",
            }
        except Exception as e:
            logger.error(f"Unexpected error in Docker health check: {e}")
            return {"status": "unhealthy", "error": str(e), "error_type": "unexpected"}
