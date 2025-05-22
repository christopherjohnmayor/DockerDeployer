try:
    import docker
    from docker.errors import NotFound, APIError
except ImportError:
    # Handle case where docker is not available
    docker = None
    NotFound = Exception
    APIError = Exception

class DockerManager:
    def __init__(self):
        if docker is None:
            raise ImportError("Docker SDK is not available. Please install docker package.")
        self.client = docker.from_env()

    def list_containers(self, all: bool = False):
        containers = self.client.containers.list(all=all)
        result = []
        for c in containers:
            result.append({
                "id": c.id,
                "name": c.name,
                "status": c.status,
                "image": c.image.tags,
                "ports": c.ports,
                "labels": c.labels,
            })
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
