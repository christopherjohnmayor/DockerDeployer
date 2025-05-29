import React from "react";
import {
  render,
  screen,
  fireEvent,
  waitFor,
  act,
} from "@testing-library/react";
import axios from "axios";
import Containers from "./Containers";

// Mock axios
jest.mock("axios");
const mockedAxios = axios as jest.Mocked<typeof axios>;

// Suppress Material-UI warnings in tests
const originalError = console.error;
beforeAll(() => {
  console.error = (...args: any[]) => {
    if (
      typeof args[0] === "string" &&
      (args[0].includes("Warning: An update to") ||
        args[0].includes("Warning: validateDOMNesting"))
    ) {
      return;
    }
    originalError.call(console, ...args);
  };
});

afterAll(() => {
  console.error = originalError;
});

describe("Containers Component", () => {
  const mockContainers = [
    {
      id: "container123456789",
      name: "test-container",
      status: "running",
      image: ["nginx:latest"],
      ports: { "80/tcp": ["8080"] },
    },
    {
      id: "container987654321",
      name: "stopped-container",
      status: "exited",
      image: ["redis:alpine"],
      ports: {},
    },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("renders containers page title", async () => {
    mockedAxios.get.mockResolvedValue({ data: [] });

    await act(async () => {
      render(<Containers />);
    });

    expect(screen.getByText("Docker Containers")).toBeInTheDocument();
  });

  test("renders refresh button", async () => {
    mockedAxios.get.mockResolvedValue({ data: [] });

    await act(async () => {
      render(<Containers />);
    });

    expect(screen.getByText("Refresh")).toBeInTheDocument();
  });

  test("shows loading state initially", async () => {
    mockedAxios.get.mockImplementation(() => new Promise(() => {})); // Never resolves

    await act(async () => {
      render(<Containers />);
    });

    expect(screen.getByRole("progressbar")).toBeInTheDocument();
  });

  test("displays containers when loaded successfully", async () => {
    mockedAxios.get.mockResolvedValue({ data: mockContainers });

    await act(async () => {
      render(<Containers />);
    });

    await waitFor(() => {
      expect(screen.getByText("test-container")).toBeInTheDocument();
      expect(screen.getByText("stopped-container")).toBeInTheDocument();
    });

    // Check table headers
    expect(screen.getByText("Name")).toBeInTheDocument();
    expect(screen.getByText("Status")).toBeInTheDocument();
    expect(screen.getByText("Image")).toBeInTheDocument();
    expect(screen.getByText("Ports")).toBeInTheDocument();
    expect(screen.getByText("ID")).toBeInTheDocument();
    expect(screen.getByText("Actions")).toBeInTheDocument();
  });

  test("displays container details correctly", async () => {
    mockedAxios.get.mockResolvedValue({ data: mockContainers });

    await act(async () => {
      render(<Containers />);
    });

    await waitFor(() => {
      // Check container names
      expect(screen.getByText("test-container")).toBeInTheDocument();
      expect(screen.getByText("stopped-container")).toBeInTheDocument();

      // Check status chips
      expect(screen.getByText("running")).toBeInTheDocument();
      expect(screen.getByText("exited")).toBeInTheDocument();

      // Check images
      expect(screen.getByText("nginx:latest")).toBeInTheDocument();
      expect(screen.getByText("redis:alpine")).toBeInTheDocument();

      // Check ports
      expect(screen.getByText("80/tcp → 8080")).toBeInTheDocument();

      // Check truncated IDs
      expect(screen.getByText("container123")).toBeInTheDocument();
      expect(screen.getByText("container987")).toBeInTheDocument();
    });
  });

  test("shows error message when fetch fails", async () => {
    mockedAxios.get.mockRejectedValue({
      response: { data: { detail: "Failed to fetch containers" } },
    });

    await act(async () => {
      render(<Containers />);
    });

    await waitFor(() => {
      expect(
        screen.getByText("Failed to fetch containers")
      ).toBeInTheDocument();
    });
  });

  test("shows no containers message when list is empty", async () => {
    mockedAxios.get.mockResolvedValue({ data: [] });

    await act(async () => {
      render(<Containers />);
    });

    await waitFor(() => {
      expect(screen.getByText("No containers found.")).toBeInTheDocument();
    });
  });

  test("handles start container action", async () => {
    mockedAxios.get.mockResolvedValue({ data: mockContainers });
    mockedAxios.post.mockResolvedValue({ data: {} });

    await act(async () => {
      render(<Containers />);
    });

    await waitFor(() => {
      expect(screen.getByText("test-container")).toBeInTheDocument();
    });

    // Find start button for stopped container using querySelector to get the actual button
    const startTooltips = screen.getAllByLabelText("Start");
    const enabledStartTooltip = startTooltips.find(
      (tooltip) => !tooltip.querySelector("button")?.hasAttribute("disabled")
    );
    const startButton = enabledStartTooltip?.querySelector("button");

    await act(async () => {
      fireEvent.click(startButton!);
    });

    expect(mockedAxios.post).toHaveBeenCalledWith(
      "/api/containers/container987654321/action",
      { action: "start" }
    );
  });

  test("handles stop container action", async () => {
    mockedAxios.get.mockResolvedValue({ data: mockContainers });
    mockedAxios.post.mockResolvedValue({ data: {} });

    await act(async () => {
      render(<Containers />);
    });

    await waitFor(() => {
      expect(screen.getByText("test-container")).toBeInTheDocument();
    });

    // Find stop button for running container using querySelector to get the actual button
    const stopTooltips = screen.getAllByLabelText("Stop");
    const enabledStopTooltip = stopTooltips.find(
      (tooltip) => !tooltip.querySelector("button")?.hasAttribute("disabled")
    );
    const stopButton = enabledStopTooltip?.querySelector("button");

    await act(async () => {
      fireEvent.click(stopButton!);
    });

    expect(mockedAxios.post).toHaveBeenCalledWith(
      "/api/containers/container123456789/action",
      { action: "stop" }
    );
  });

  test("handles restart container action", async () => {
    mockedAxios.get.mockResolvedValue({ data: mockContainers });
    mockedAxios.post.mockResolvedValue({ data: {} });

    await act(async () => {
      render(<Containers />);
    });

    await waitFor(() => {
      expect(screen.getByText("test-container")).toBeInTheDocument();
    });

    // Find restart button for running container using querySelector to get the actual button
    const restartTooltips = screen.getAllByLabelText("Restart");
    const enabledRestartTooltip = restartTooltips.find(
      (tooltip) => !tooltip.querySelector("button")?.hasAttribute("disabled")
    );
    const restartButton = enabledRestartTooltip?.querySelector("button");

    await act(async () => {
      fireEvent.click(restartButton!);
    });

    expect(mockedAxios.post).toHaveBeenCalledWith(
      "/api/containers/container123456789/action",
      { action: "restart" }
    );
  });

  test("opens logs dialog when logs button is clicked", async () => {
    mockedAxios.get.mockImplementation((url) => {
      if (url.includes("/api/logs/")) {
        return Promise.resolve({ data: { logs: "Sample log content" } });
      }
      return Promise.resolve({ data: mockContainers });
    });

    await act(async () => {
      render(<Containers />);
    });

    await waitFor(() => {
      expect(screen.getByText("test-container")).toBeInTheDocument();
    });

    // Click logs button using querySelector to get the actual button
    const logsTooltips = screen.getAllByLabelText("Logs");
    const logsButton = logsTooltips[0].querySelector("button");

    await act(async () => {
      fireEvent.click(logsButton!);
    });

    // Check if dialog opens with loading first
    await waitFor(() => {
      expect(screen.getByText("Logs: test-container")).toBeInTheDocument();
    });

    // Then check for the actual log content
    await waitFor(() => {
      expect(screen.getByText("Sample log content")).toBeInTheDocument();
    });
  });

  test("closes logs dialog when close button is clicked", async () => {
    mockedAxios.get.mockImplementation((url) => {
      if (url.includes("/api/logs/")) {
        return Promise.resolve({ data: { logs: "Sample log content" } });
      }
      return Promise.resolve({ data: mockContainers });
    });

    await act(async () => {
      render(<Containers />);
    });

    await waitFor(() => {
      expect(screen.getByText("test-container")).toBeInTheDocument();
    });

    // Open logs dialog using querySelector to get the actual button
    const logsTooltips = screen.getAllByLabelText("Logs");
    const logsButton = logsTooltips[0].querySelector("button");

    await act(async () => {
      fireEvent.click(logsButton!);
    });

    await waitFor(() => {
      expect(screen.getByText("Logs: test-container")).toBeInTheDocument();
    });

    // Close dialog
    const closeButton = screen.getByText("Close");

    await act(async () => {
      fireEvent.click(closeButton);
    });

    await waitFor(() => {
      expect(
        screen.queryByText("Logs: test-container")
      ).not.toBeInTheDocument();
    });
  });

  test("refreshes containers when refresh button is clicked", async () => {
    mockedAxios.get.mockResolvedValue({ data: mockContainers });

    await act(async () => {
      render(<Containers />);
    });

    await waitFor(() => {
      expect(screen.getByText("test-container")).toBeInTheDocument();
    });

    // Clear previous calls
    mockedAxios.get.mockClear();

    // Click refresh button
    const refreshButton = screen.getByText("Refresh");

    await act(async () => {
      fireEvent.click(refreshButton);
    });

    expect(mockedAxios.get).toHaveBeenCalledWith("/api/containers");
  });

  test("handles action errors gracefully", async () => {
    // First load containers successfully
    mockedAxios.get.mockResolvedValue({ data: mockContainers });
    // Then make action fail
    mockedAxios.post.mockRejectedValue({
      response: { data: { detail: "Action failed" } },
    });

    await act(async () => {
      render(<Containers />);
    });

    await waitFor(() => {
      expect(screen.getByText("test-container")).toBeInTheDocument();
    });

    // Try to stop a container using querySelector to get the actual button
    const stopTooltips = screen.getAllByLabelText("Stop");
    const enabledStopTooltip = stopTooltips.find(
      (tooltip) => !tooltip.querySelector("button")?.hasAttribute("disabled")
    );
    const stopButton = enabledStopTooltip?.querySelector("button");

    await act(async () => {
      fireEvent.click(stopButton!);
    });

    // Verify the API was called
    expect(mockedAxios.post).toHaveBeenCalledWith(
      "/api/containers/container123456789/action",
      { action: "stop" }
    );
  });

  // Enhanced test for branch coverage - line 84
  test("handles logs fetch error without detailed response", async () => {
    // Mock successful containers fetch first
    mockedAxios.get.mockResolvedValueOnce({ data: mockContainers });

    await act(async () => {
      render(<Containers />);
    });

    await waitFor(() => {
      expect(screen.getByText("test-container")).toBeInTheDocument();
    });

    // Mock logs fetch failure without detailed error response - covers line 84
    mockedAxios.get.mockRejectedValueOnce({
      message: "Network Error",
    });

    // Click logs button using querySelector to get the actual button
    const logsTooltips = screen.getAllByLabelText("Logs");
    const logsButton = logsTooltips[0].querySelector("button");

    await act(async () => {
      fireEvent.click(logsButton!);
    });

    // Wait for dialog to open
    await waitFor(() => {
      expect(screen.getByText("Logs: test-container")).toBeInTheDocument();
    });

    // Wait for error message in logs content - this covers the error handling branch on line 84
    await waitFor(() => {
      expect(screen.getByText("Network Error")).toBeInTheDocument();
    });
  });

  test("handles logs fetch error with generic fallback message", async () => {
    // Mock successful containers fetch first
    mockedAxios.get.mockResolvedValueOnce({ data: mockContainers });

    await act(async () => {
      render(<Containers />);
    });

    await waitFor(() => {
      expect(screen.getByText("test-container")).toBeInTheDocument();
    });

    // Mock logs fetch failure with no message - covers fallback error handling
    mockedAxios.get.mockRejectedValueOnce({});

    // Click logs button using querySelector to get the actual button
    const logsTooltips = screen.getAllByLabelText("Logs");
    const logsButton = logsTooltips[0].querySelector("button");

    await act(async () => {
      fireEvent.click(logsButton!);
    });

    // Wait for dialog to open
    await waitFor(() => {
      expect(screen.getByText("Logs: test-container")).toBeInTheDocument();
    });

    // Wait for fallback error message
    await waitFor(() => {
      expect(screen.getByText("Failed to fetch logs.")).toBeInTheDocument();
    });
  });
});
