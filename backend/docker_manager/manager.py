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
