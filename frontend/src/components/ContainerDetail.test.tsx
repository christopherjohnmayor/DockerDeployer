import React from "react";
import {
  render,
  screen,
  fireEvent,
  waitFor,
  act,
} from "@testing-library/react";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import axios from "axios";
import ContainerDetail from "./ContainerDetail";
import { ToastProvider } from "./Toast";

// Mock axios
jest.mock("axios");
const mockedAxios = axios as jest.Mocked<typeof axios>;

// Create a theme for testing
const theme = createTheme();

// Test wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ThemeProvider theme={theme}>
    <ToastProvider>{children}</ToastProvider>
  </ThemeProvider>
);

// Suppress Material-UI warnings in tests
const originalError = console.error;
beforeAll(() => {
  console.error = (...args: any[]) => {
    if (
      typeof args[0] === "string" &&
      args[0].includes("Warning: An update to")
    ) {
      return;
    }
    originalError.call(console, ...args);
  };
});

afterAll(() => {
  console.error = originalError;
});

describe("ContainerDetail Component", () => {
  const mockContainer = {
    id: "test-container-id",
    name: "test-container",
    status: "running",
    image: ["nginx:latest"],
    ports: { "80/tcp": [{ HostIp: "0.0.0.0", HostPort: "8080" }] },
    labels: { app: "test", environment: "development" },
  };

  const mockLogs = {
    logs: "Container log output\nLine 1\nLine 2",
    id: "test-container-id",
  };

  const mockMetrics = {
    cpu_usage: "5%",
    memory_usage: "256MB",
    network_io: "RX: 1.2MB, TX: 0.5MB",
    block_io: "Read: 10MB, Write: 5MB",
  };

  beforeEach(() => {
    jest.clearAllMocks();

    // Mock successful container fetch
    mockedAxios.get.mockImplementation((url) => {
      if (url.includes("/api/containers/") && !url.includes("/stats")) {
        return Promise.resolve({ data: mockContainer });
      }
      if (url.includes("/api/logs/")) {
        return Promise.resolve({ data: mockLogs });
      }
      if (url.includes("/stats")) {
        return Promise.resolve({ data: mockMetrics });
      }
      return Promise.reject(new Error("Not found"));
    });

    // Mock successful container action
    mockedAxios.post.mockResolvedValue({
      data: { status: "success", container_id: "test-container-id" },
    });
  });

  test("renders container details correctly", async () => {
    await act(async () => {
      render(
        <TestWrapper>
          <ContainerDetail containerId="test-container-id" />
        </TestWrapper>
      );
    });

    // Wait for container data to load
    await waitFor(() => {
      expect(screen.getByText("test-container")).toBeInTheDocument();
    });

    // Check basic container info is displayed
    expect(screen.getByText("Status")).toBeInTheDocument();
    expect(screen.getByText("running")).toBeInTheDocument();
    expect(screen.getByText("ID")).toBeInTheDocument();
    expect(screen.getByText("test-container-id")).toBeInTheDocument();

    // Check tabs are present
    expect(screen.getByText("Overview")).toBeInTheDocument();
    expect(screen.getByText("Logs")).toBeInTheDocument();
    expect(screen.getByText("Real-time Metrics")).toBeInTheDocument();
    expect(screen.getByText("Environment")).toBeInTheDocument();
  });

  test("switches tabs correctly", async () => {
    await act(async () => {
      render(
        <TestWrapper>
          <ContainerDetail containerId="test-container-id" />
        </TestWrapper>
      );
    });

    // Wait for container data to load
    await waitFor(() => {
      expect(screen.getByText("test-container")).toBeInTheDocument();
    });

    // Click on Logs tab
    await act(async () => {
      fireEvent.click(screen.getByText("Logs"));
    });

    // Wait for logs to load
    await waitFor(() => {
      expect(screen.getByText("Container Logs")).toBeInTheDocument();
    });

    // Check logs content
    await waitFor(() => {
      const logsElement = screen.getByText(/Container log output/);
      expect(logsElement).toBeInTheDocument();
    });

    // Click on Metrics tab
    await act(async () => {
      fireEvent.click(screen.getByText("Real-time Metrics"));
    });

    // Wait for metrics to load
    await waitFor(() => {
      expect(screen.getByText("Container Metrics")).toBeInTheDocument();
    });

    // Wait for metrics API call to complete and data to be displayed
    await waitFor(() => {
      expect(screen.getByText("CPU Usage")).toBeInTheDocument();
    });

    // Check for the actual CPU usage value from our mock
    await waitFor(() => {
      expect(screen.getByText("5%")).toBeInTheDocument();
    });

    expect(screen.getByText("Memory Usage")).toBeInTheDocument();
    expect(screen.getByText("256MB")).toBeInTheDocument();
  });

  test("handles container actions correctly", async () => {
    await act(async () => {
      render(
        <TestWrapper>
          <ContainerDetail containerId="test-container-id" />
        </TestWrapper>
      );
    });

    // Wait for container data to load
    await waitFor(() => {
      expect(screen.getByText("test-container")).toBeInTheDocument();
    });

    // Wait for the container status to be properly set
    await waitFor(() => {
      expect(screen.getByText("running")).toBeInTheDocument();
    });

    // Find the stop button - need to get the actual button, not the span wrapper
    const stopButtonSpan = screen.getByLabelText("Stop");
    const stopButton = stopButtonSpan.querySelector("button");

    // Ensure the button exists and is not disabled
    expect(stopButton).toBeTruthy();
    expect(stopButton).not.toBeDisabled();

    await act(async () => {
      fireEvent.click(stopButton!);
    });

    // Check if the API was called correctly
    await waitFor(() => {
      expect(mockedAxios.post).toHaveBeenCalledWith(
        "/api/containers/test-container-id/action",
        { action: "stop" }
      );
    });

    // Check if the container data was refreshed (initial load + refresh after action)
    await waitFor(() => {
      expect(mockedAxios.get).toHaveBeenCalledTimes(2);
    });
  });

  test("displays error message when container fetch fails", async () => {
    // Mock failed container fetch
    mockedAxios.get.mockRejectedValueOnce({
      response: { data: { detail: "Container not found" } },
    });

    await act(async () => {
      render(
        <TestWrapper>
          <ContainerDetail containerId="nonexistent-id" />
        </TestWrapper>
      );
    });

    // Wait for error message
    await waitFor(() => {
      expect(screen.getByText("Container not found")).toBeInTheDocument();
    });
  });

  test("refreshes logs when refresh button is clicked", async () => {
    await act(async () => {
      render(
        <TestWrapper>
          <ContainerDetail containerId="test-container-id" />
        </TestWrapper>
      );
    });

    // Wait for container data to load
    await waitFor(() => {
      expect(screen.getByText("test-container")).toBeInTheDocument();
    });

    // Click on Logs tab
    await act(async () => {
      fireEvent.click(screen.getByText("Logs"));
    });

    // Wait for logs to load
    await waitFor(() => {
      expect(screen.getByText("Container Logs")).toBeInTheDocument();
    });

    // Find and click the refresh logs button
    const refreshButton = screen.getByText("Refresh Logs");
    await act(async () => {
      fireEvent.click(refreshButton);
    });

    // Check if the logs API was called again
    await waitFor(() => {
      expect(mockedAxios.get).toHaveBeenCalledWith(
        "/api/logs/test-container-id"
      );
      // Initial container + initial logs + refresh logs
      expect(mockedAxios.get).toHaveBeenCalledTimes(3);
    });
  });

  // Enhanced tests for branch coverage
  describe("Branch Coverage Enhancement", () => {
    test("handles logs fetch error without detailed response - line 136", async () => {
      // Mock successful container fetch
      mockedAxios.get.mockImplementation((url) => {
        if (url.includes("/api/logs/")) {
          return Promise.reject({
            message: "Network Error",
          });
        }
        return Promise.resolve({ data: mockContainer });
      });

      await act(async () => {
        render(
          <TestWrapper>
            <ContainerDetail containerId="test-container-id" />
          </TestWrapper>
        );
      });

      await waitFor(() => {
        expect(screen.getByText("test-container")).toBeInTheDocument();
      });

      // Switch to logs tab to trigger fetchLogs
      const logsTab = screen.getByText("Logs");
      await act(async () => {
        fireEvent.click(logsTab);
      });

      // Should show error message - covers line 136
      await waitFor(() => {
        expect(
          screen.getByText(/Error fetching logs: Network Error/)
        ).toBeInTheDocument();
      });
    });

    test("handles metrics fetch error without detailed response - line 152", async () => {
      // Mock successful container fetch
      mockedAxios.get.mockImplementation((url) => {
        if (url.includes("/stats")) {
          return Promise.reject({
            message: "Stats unavailable",
          });
        }
        return Promise.resolve({ data: mockContainer });
      });

      await act(async () => {
        render(
          <TestWrapper>
            <ContainerDetail containerId="test-container-id" />
          </TestWrapper>
        );
      });

      await waitFor(() => {
        expect(screen.getByText("test-container")).toBeInTheDocument();
      });

      // Switch to metrics tab to trigger fetchMetrics
      const metricsTab = screen.getByText("Real-time Metrics");
      await act(async () => {
        fireEvent.click(metricsTab);
      });

      // Should show error message - covers line 152
      await waitFor(() => {
        expect(screen.getByText("Stats unavailable")).toBeInTheDocument();
      });
    });

    test("handles action error without detailed response - line 185", async () => {
      // Mock successful container fetch with stopped status so start button is enabled
      const stoppedContainer = { ...mockContainer, status: "stopped" };
      mockedAxios.get.mockResolvedValue({ data: stoppedContainer });

      // Mock action failure without detailed error
      mockedAxios.post.mockRejectedValue({
        message: "Action failed",
      });

      await act(async () => {
        render(
          <TestWrapper>
            <ContainerDetail containerId="test-container-id" />
          </TestWrapper>
        );
      });

      await waitFor(() => {
        expect(screen.getByText("test-container")).toBeInTheDocument();
      });

      // Click start button to trigger handleAction (start button should be enabled for stopped container)
      const startButtonSpan = screen.getByLabelText("Start");
      const startButton = startButtonSpan.querySelector("button");

      // Ensure button is not disabled
      expect(startButton).not.toBeDisabled();

      await act(async () => {
        fireEvent.click(startButton!);
      });

      // Should show error message - covers line 185
      await waitFor(() => {
        expect(screen.getByText("Action failed")).toBeInTheDocument();
      });
    });

    test("handles container not found scenario - line 211", async () => {
      // Mock container fetch returning null/undefined
      mockedAxios.get.mockResolvedValue({ data: null });

      await act(async () => {
        render(
          <TestWrapper>
            <ContainerDetail containerId="nonexistent-id" />
          </TestWrapper>
        );
      });

      // Should show container not found message - covers line 211
      await waitFor(() => {
        expect(screen.getByText("Container not found.")).toBeInTheDocument();
      });
    });

    test("handles action error with generic fallback - line 235", async () => {
      // Mock successful container fetch
      mockedAxios.get.mockResolvedValue({ data: mockContainer });

      // Mock action failure with no message
      mockedAxios.post.mockRejectedValue({});

      await act(async () => {
        render(
          <TestWrapper>
            <ContainerDetail containerId="test-container-id" />
          </TestWrapper>
        );
      });

      await waitFor(() => {
        expect(screen.getByText("test-container")).toBeInTheDocument();
      });

      // Click stop button to trigger handleAction
      const stopButtonSpan = screen.getByLabelText("Stop");
      const stopButton = stopButtonSpan.querySelector("button");
      await act(async () => {
        fireEvent.click(stopButton!);
      });

      // Should show fallback error message - covers line 235
      await waitFor(() => {
        expect(
          screen.getByText("Failed to stop container.")
        ).toBeInTheDocument();
      });
    });

    test("handles restart action error - line 259", async () => {
      // Mock successful container fetch with running status
      const runningContainer = { ...mockContainer, status: "running" };
      mockedAxios.get.mockResolvedValue({ data: runningContainer });

      // Mock restart action failure
      mockedAxios.post.mockRejectedValue({
        response: { data: { detail: "Restart failed" } },
      });

      await act(async () => {
        render(
          <TestWrapper>
            <ContainerDetail containerId="test-container-id" />
          </TestWrapper>
        );
      });

      await waitFor(() => {
        expect(screen.getByText("test-container")).toBeInTheDocument();
      });

      // Click restart button to trigger handleAction
      const restartButtonSpan = screen.getByLabelText("Restart");
      const restartButton = restartButtonSpan.querySelector("button");
      await act(async () => {
        fireEvent.click(restartButton!);
      });

      // Should show error message - covers line 259
      await waitFor(() => {
        expect(screen.getByText("Restart failed")).toBeInTheDocument();
      });
    });
  });
});
