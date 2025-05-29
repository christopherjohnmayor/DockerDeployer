import axios from "axios";
import {
  fetchContainers,
  fetchContainer,
  performContainerAction,
  fetchContainerLogs,
  fetchContainerMetrics,
  Container,
  ContainerActionResponse,
  ContainerLogsResponse,
} from "./containers";

// Mock axios
jest.mock("axios");
const mockedAxios = axios as jest.Mocked<typeof axios>;

describe("containers API", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("fetchContainers", () => {
    const mockContainers: Container[] = [
      {
        id: "container123456789",
        name: "test-container",
        status: "running",
        image: ["nginx:latest"],
        ports: { "80/tcp": [{ HostIp: "0.0.0.0", HostPort: "8080" }] },
        labels: { app: "web" },
      },
      {
        id: "container987654321",
        name: "stopped-container",
        status: "exited",
        image: ["redis:alpine"],
        ports: {},
        labels: {},
      },
    ];

    it("successfully fetches containers", async () => {
      mockedAxios.get.mockResolvedValue({ data: mockContainers });

      const result = await fetchContainers();

      expect(mockedAxios.get).toHaveBeenCalledWith("/api/containers");
      expect(result).toEqual(mockContainers);
    });

    it("returns empty array when no containers exist", async () => {
      mockedAxios.get.mockResolvedValue({ data: [] });

      const result = await fetchContainers();

      expect(mockedAxios.get).toHaveBeenCalledWith("/api/containers");
      expect(result).toEqual([]);
    });

    it("handles network error", async () => {
      const networkError = {
        isAxiosError: true,
        message: "Network Error",
        response: undefined,
      };
      mockedAxios.get.mockRejectedValue(networkError);

      await expect(fetchContainers()).rejects.toEqual(networkError);
      expect(mockedAxios.get).toHaveBeenCalledWith("/api/containers");
    });

    it("handles server error (500)", async () => {
      const serverError = {
        isAxiosError: true,
        message: "Request failed with status code 500",
        response: {
          status: 500,
          data: { detail: "Internal server error" },
        },
      };
      mockedAxios.get.mockRejectedValue(serverError);

      await expect(fetchContainers()).rejects.toEqual(serverError);
      expect(mockedAxios.get).toHaveBeenCalledWith("/api/containers");
    });

    it("handles authentication error (401)", async () => {
      const authError = {
        isAxiosError: true,
        message: "Request failed with status code 401",
        response: {
          status: 401,
          data: { detail: "Authentication required" },
        },
      };
      mockedAxios.get.mockRejectedValue(authError);

      await expect(fetchContainers()).rejects.toEqual(authError);
      expect(mockedAxios.get).toHaveBeenCalledWith("/api/containers");
    });

    it("handles authorization error (403)", async () => {
      const forbiddenError = {
        isAxiosError: true,
        message: "Request failed with status code 403",
        response: {
          status: 403,
          data: { detail: "Insufficient permissions" },
        },
      };
      mockedAxios.get.mockRejectedValue(forbiddenError);

      await expect(fetchContainers()).rejects.toEqual(forbiddenError);
      expect(mockedAxios.get).toHaveBeenCalledWith("/api/containers");
    });

    it("handles malformed response data", async () => {
      mockedAxios.get.mockResolvedValue({ data: null });

      const result = await fetchContainers();

      expect(mockedAxios.get).toHaveBeenCalledWith("/api/containers");
      expect(result).toBeNull();
    });

    it("handles containers with minimal data", async () => {
      const minimalContainers: Container[] = [
        {
          id: "minimal123",
          name: "minimal-container",
          status: "created",
        },
      ];
      mockedAxios.get.mockResolvedValue({ data: minimalContainers });

      const result = await fetchContainers();

      expect(mockedAxios.get).toHaveBeenCalledWith("/api/containers");
      expect(result).toEqual(minimalContainers);
    });

    it("handles containers with complex port mappings", async () => {
      const complexContainers: Container[] = [
        {
          id: "complex123",
          name: "complex-container",
          status: "running",
          image: ["nginx:1.21", "nginx:latest"],
          ports: {
            "80/tcp": [
              { HostIp: "0.0.0.0", HostPort: "8080" },
              { HostIp: "127.0.0.1", HostPort: "8081" },
            ],
            "443/tcp": [{ HostIp: "0.0.0.0", HostPort: "8443" }],
          },
          labels: {
            "com.docker.compose.project": "myproject",
            "com.docker.compose.service": "web",
            "traefik.enable": "true",
          },
        },
      ];
      mockedAxios.get.mockResolvedValue({ data: complexContainers });

      const result = await fetchContainers();

      expect(mockedAxios.get).toHaveBeenCalledWith("/api/containers");
      expect(result).toEqual(complexContainers);
    });

    it("handles timeout error", async () => {
      const timeoutError = {
        isAxiosError: true,
        message: "timeout of 5000ms exceeded",
        code: "ECONNABORTED",
        response: undefined,
      };
      mockedAxios.get.mockRejectedValue(timeoutError);

      await expect(fetchContainers()).rejects.toEqual(timeoutError);
      expect(mockedAxios.get).toHaveBeenCalledWith("/api/containers");
    });

    it("handles DNS resolution error", async () => {
      const dnsError = {
        isAxiosError: true,
        message: "getaddrinfo ENOTFOUND api.example.com",
        code: "ENOTFOUND",
        response: undefined,
      };
      mockedAxios.get.mockRejectedValue(dnsError);

      await expect(fetchContainers()).rejects.toEqual(dnsError);
      expect(mockedAxios.get).toHaveBeenCalledWith("/api/containers");
    });
  });

  describe("fetchContainer", () => {
    const mockContainer: Container = {
      id: "container123456789",
      name: "test-container",
      status: "running",
      image: ["nginx:latest"],
      ports: { "80/tcp": [{ HostIp: "0.0.0.0", HostPort: "8080" }] },
      labels: { app: "web" },
    };

    it("successfully fetches a single container", async () => {
      mockedAxios.get.mockResolvedValue({ data: mockContainer });

      const result = await fetchContainer("container123456789");

      expect(mockedAxios.get).toHaveBeenCalledWith(
        "/api/containers/container123456789"
      );
      expect(result).toEqual(mockContainer);
    });

    it("handles container not found (404)", async () => {
      const notFoundError = {
        isAxiosError: true,
        message: "Request failed with status code 404",
        response: {
          status: 404,
          data: { detail: "Container not found" },
        },
      };
      mockedAxios.get.mockRejectedValue(notFoundError);

      await expect(fetchContainer("nonexistent")).rejects.toEqual(
        notFoundError
      );
      expect(mockedAxios.get).toHaveBeenCalledWith(
        "/api/containers/nonexistent"
      );
    });

    it("handles network error", async () => {
      const networkError = {
        isAxiosError: true,
        message: "Network Error",
        response: undefined,
      };
      mockedAxios.get.mockRejectedValue(networkError);

      await expect(fetchContainer("container123")).rejects.toEqual(
        networkError
      );
    });
  });

  describe("performContainerAction", () => {
    const mockActionResponse: ContainerActionResponse = {
      container_id: "container123456789",
      action: "start",
      result: {
        status: "success",
        message: "Container started successfully",
      },
    };

    it("successfully starts a container", async () => {
      mockedAxios.post.mockResolvedValue({ data: mockActionResponse });

      const result = await performContainerAction(
        "container123456789",
        "start"
      );

      expect(mockedAxios.post).toHaveBeenCalledWith(
        "/api/containers/container123456789/action",
        { action: "start" }
      );
      expect(result).toEqual(mockActionResponse);
    });

    it("successfully stops a container", async () => {
      const stopResponse = {
        ...mockActionResponse,
        action: "stop",
        result: {
          status: "success",
          message: "Container stopped successfully",
        },
      };
      mockedAxios.post.mockResolvedValue({ data: stopResponse });

      const result = await performContainerAction("container123456789", "stop");

      expect(mockedAxios.post).toHaveBeenCalledWith(
        "/api/containers/container123456789/action",
        { action: "stop" }
      );
      expect(result).toEqual(stopResponse);
    });

    it("successfully restarts a container", async () => {
      const restartResponse = {
        ...mockActionResponse,
        action: "restart",
        result: {
          status: "success",
          message: "Container restarted successfully",
        },
      };
      mockedAxios.post.mockResolvedValue({ data: restartResponse });

      const result = await performContainerAction(
        "container123456789",
        "restart"
      );

      expect(mockedAxios.post).toHaveBeenCalledWith(
        "/api/containers/container123456789/action",
        { action: "restart" }
      );
      expect(result).toEqual(restartResponse);
    });

    it("handles action failure", async () => {
      const failureResponse = {
        ...mockActionResponse,
        result: { status: "error", message: "Container is already running" },
      };
      mockedAxios.post.mockResolvedValue({ data: failureResponse });

      const result = await performContainerAction(
        "container123456789",
        "start"
      );

      expect(result.result.status).toBe("error");
      expect(result.result.message).toBe("Container is already running");
    });

    it("handles container not found during action", async () => {
      const notFoundError = {
        isAxiosError: true,
        message: "Request failed with status code 404",
        response: {
          status: 404,
          data: { detail: "Container not found" },
        },
      };
      mockedAxios.post.mockRejectedValue(notFoundError);

      await expect(
        performContainerAction("nonexistent", "start")
      ).rejects.toEqual(notFoundError);
    });

    it("handles server error during action", async () => {
      const serverError = {
        isAxiosError: true,
        message: "Request failed with status code 500",
        response: {
          status: 500,
          data: { detail: "Internal server error" },
        },
      };
      mockedAxios.post.mockRejectedValue(serverError);

      await expect(
        performContainerAction("container123", "stop")
      ).rejects.toEqual(serverError);
    });
  });

  describe("fetchContainerLogs", () => {
    const mockLogsResponse: ContainerLogsResponse = {
      container_id: "container123456789",
      logs: "2023-05-01 12:00:00 Server started\n2023-05-01 12:01:00 Request received\n2023-05-01 12:02:00 Processing complete",
    };

    it("successfully fetches container logs", async () => {
      mockedAxios.get.mockResolvedValue({ data: mockLogsResponse });

      const result = await fetchContainerLogs("container123456789");

      expect(mockedAxios.get).toHaveBeenCalledWith(
        "/api/logs/container123456789"
      );
      expect(result).toEqual(mockLogsResponse);
    });

    it("handles empty logs", async () => {
      const emptyLogsResponse = {
        container_id: "container123456789",
        logs: "",
      };
      mockedAxios.get.mockResolvedValue({ data: emptyLogsResponse });

      const result = await fetchContainerLogs("container123456789");

      expect(result.logs).toBe("");
    });

    it("handles container not found for logs", async () => {
      const notFoundError = {
        isAxiosError: true,
        message: "Request failed with status code 404",
        response: {
          status: 404,
          data: { detail: "Container not found" },
        },
      };
      mockedAxios.get.mockRejectedValue(notFoundError);

      await expect(fetchContainerLogs("nonexistent")).rejects.toEqual(
        notFoundError
      );
    });

    it("handles logs access denied", async () => {
      const forbiddenError = {
        isAxiosError: true,
        message: "Request failed with status code 403",
        response: {
          status: 403,
          data: { detail: "Access denied to container logs" },
        },
      };
      mockedAxios.get.mockRejectedValue(forbiddenError);

      await expect(fetchContainerLogs("restricted-container")).rejects.toEqual(
        forbiddenError
      );
    });

    it("handles large log files", async () => {
      const largeLogsResponse = {
        container_id: "container123456789",
        logs: "A".repeat(10000) + "\nLarge log file content",
      };
      mockedAxios.get.mockResolvedValue({ data: largeLogsResponse });

      const result = await fetchContainerLogs("container123456789");

      expect(result.logs.length).toBeGreaterThan(10000);
    });
  });

  describe("fetchContainerMetrics", () => {
    const mockMetricsResponse = {
      container_id: "container123456789",
      cpu_usage: 25.5,
      memory_usage: 512000000,
      memory_limit: 1073741824,
      network_rx: 1024000,
      network_tx: 2048000,
      block_read: 4096000,
      block_write: 8192000,
      timestamp: "2023-05-01T12:00:00Z",
    };

    it("successfully fetches container metrics", async () => {
      mockedAxios.get.mockResolvedValue({ data: mockMetricsResponse });

      const result = await fetchContainerMetrics("container123456789");

      expect(mockedAxios.get).toHaveBeenCalledWith(
        "/api/containers/container123456789/metrics"
      );
      expect(result).toEqual(mockMetricsResponse);
    });

    it("handles metrics not available", async () => {
      const noMetricsResponse = {
        container_id: "container123456789",
        error: "Metrics not available for stopped container",
      };
      mockedAxios.get.mockResolvedValue({ data: noMetricsResponse });

      const result = await fetchContainerMetrics("container123456789");

      expect(result.error).toBe("Metrics not available for stopped container");
    });

    it("handles container not found for metrics", async () => {
      const notFoundError = {
        isAxiosError: true,
        message: "Request failed with status code 404",
        response: {
          status: 404,
          data: { detail: "Container not found" },
        },
      };
      mockedAxios.get.mockRejectedValue(notFoundError);

      await expect(fetchContainerMetrics("nonexistent")).rejects.toEqual(
        notFoundError
      );
    });

    it("handles metrics service unavailable", async () => {
      const serviceError = {
        isAxiosError: true,
        message: "Request failed with status code 503",
        response: {
          status: 503,
          data: { detail: "Metrics service temporarily unavailable" },
        },
      };
      mockedAxios.get.mockRejectedValue(serviceError);

      await expect(fetchContainerMetrics("container123")).rejects.toEqual(
        serviceError
      );
    });

    it("handles zero metrics values", async () => {
      const zeroMetricsResponse = {
        container_id: "container123456789",
        cpu_usage: 0,
        memory_usage: 0,
        memory_limit: 0,
        network_rx: 0,
        network_tx: 0,
        block_read: 0,
        block_write: 0,
        timestamp: "2023-05-01T12:00:00Z",
      };
      mockedAxios.get.mockResolvedValue({ data: zeroMetricsResponse });

      const result = await fetchContainerMetrics("container123456789");

      expect(result.cpu_usage).toBe(0);
      expect(result.memory_usage).toBe(0);
    });

    it("handles network timeout for metrics", async () => {
      const timeoutError = {
        isAxiosError: true,
        message: "timeout of 5000ms exceeded",
        code: "ECONNABORTED",
        response: undefined,
      };
      mockedAxios.get.mockRejectedValue(timeoutError);

      await expect(fetchContainerMetrics("container123")).rejects.toEqual(
        timeoutError
      );
    });
  });
});
