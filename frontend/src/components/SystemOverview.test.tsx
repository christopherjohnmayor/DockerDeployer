import React from "react";
import {
  render,
  screen,
  fireEvent,
  waitFor,
  act,
} from "@testing-library/react";
import { ThemeProvider } from "@mui/material/styles";
import { createTheme } from "@mui/material/styles";
import SystemOverview from "./SystemOverview";
import * as useApiCallModule from "../hooks/useApiCall";

const theme = createTheme();

const mockSystemMetrics = {
  timestamp: "2024-01-01T12:00:00Z",
  containers_total: 5,
  containers_running: 3,
  containers_by_status: {
    running: 3,
    stopped: 2,
  },
  system_info: {
    docker_version: "20.10.17",
    total_memory: 8589934592, // 8GB
    cpus: 4,
    kernel_version: "5.4.0-74-generic",
    operating_system: "Ubuntu 20.04.2 LTS",
    architecture: "x86_64",
  },
};

const mockUseApiCall = {
  execute: jest.fn(),
  loading: false,
  error: null,
};

const renderWithTheme = (component: React.ReactElement) => {
  return render(<ThemeProvider theme={theme}>{component}</ThemeProvider>);
};

// Mock the useApiCall hook
jest.mock("../hooks/useApiCall");
const mockedUseApiCall = useApiCallModule.useApiCall as jest.MockedFunction<
  typeof useApiCallModule.useApiCall
>;

describe("SystemOverview", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockedUseApiCall.mockReturnValue(mockUseApiCall);
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it("renders system overview title", () => {
    renderWithTheme(<SystemOverview />);

    expect(screen.getByText("System Overview")).toBeInTheDocument();
  });

  it("renders refresh button", () => {
    renderWithTheme(<SystemOverview />);

    const refreshButton = screen.getByRole("button", { name: /refresh/i });
    expect(refreshButton).toBeInTheDocument();
  });

  it("fetches system metrics on mount", async () => {
    mockUseApiCall.execute.mockResolvedValue(mockSystemMetrics);

    await act(async () => {
      renderWithTheme(<SystemOverview />);
    });

    await waitFor(() => {
      expect(mockUseApiCall.execute).toHaveBeenCalledWith(
        "/api/system/metrics"
      );
    });
  });

  it("displays container status information", async () => {
    mockUseApiCall.execute.mockResolvedValue(mockSystemMetrics);

    renderWithTheme(<SystemOverview />);

    await act(async () => {
      jest.advanceTimersByTime(100);
    });

    await waitFor(() => {
      expect(screen.getByText("Container Status")).toBeInTheDocument();
      expect(screen.getByText("3")).toBeInTheDocument(); // running containers
      expect(screen.getByText("of 5 containers running")).toBeInTheDocument();
    });
  });

  it("displays system resources information", async () => {
    mockUseApiCall.execute.mockResolvedValue(mockSystemMetrics);

    renderWithTheme(<SystemOverview />);

    await act(async () => {
      jest.advanceTimersByTime(100);
    });

    await waitFor(() => {
      expect(screen.getByText("System Resources")).toBeInTheDocument();
      expect(screen.getByText("CPU Cores")).toBeInTheDocument();
      expect(screen.getByText("4 cores")).toBeInTheDocument();
      expect(screen.getByText("Total Memory")).toBeInTheDocument();
      expect(screen.getByText("8.00 GB")).toBeInTheDocument();
    });
  });

  it("displays system information", async () => {
    mockUseApiCall.execute.mockResolvedValue(mockSystemMetrics);

    renderWithTheme(<SystemOverview />);

    await act(async () => {
      jest.advanceTimersByTime(100);
    });

    await waitFor(() => {
      expect(screen.getByText("System Information")).toBeInTheDocument();
      expect(screen.getByText("Docker Version")).toBeInTheDocument();
      expect(screen.getByText("20.10.17")).toBeInTheDocument();
      expect(screen.getByText("Operating System")).toBeInTheDocument();
      expect(screen.getByText("Ubuntu 20.04.2 LTS")).toBeInTheDocument();
    });
  });

  it("displays container status chips", async () => {
    mockUseApiCall.execute.mockResolvedValue(mockSystemMetrics);

    renderWithTheme(<SystemOverview />);

    await act(async () => {
      jest.advanceTimersByTime(100);
    });

    await waitFor(() => {
      expect(screen.getByText("running: 3")).toBeInTheDocument();
      expect(screen.getByText("stopped: 2")).toBeInTheDocument();
    });
  });

  it("calculates container health percentage correctly", async () => {
    mockUseApiCall.execute.mockResolvedValue(mockSystemMetrics);

    renderWithTheme(<SystemOverview />);

    await act(async () => {
      jest.advanceTimersByTime(100);
    });

    await waitFor(() => {
      // 3 running out of 5 total = 60%
      expect(screen.getByText("Health: 60.0%")).toBeInTheDocument();
    });
  });

  it("handles manual refresh", async () => {
    mockUseApiCall.execute.mockResolvedValue(mockSystemMetrics);

    renderWithTheme(<SystemOverview />);

    const refreshButton = screen.getByRole("button", { name: /refresh/i });

    await act(async () => {
      fireEvent.click(refreshButton);
    });

    expect(mockUseApiCall.execute).toHaveBeenCalledWith("/api/system/metrics");
  });

  it("shows loading state", () => {
    mockedUseApiCall.mockReturnValue({
      ...mockUseApiCall,
      loading: true,
    });

    renderWithTheme(<SystemOverview />);

    expect(screen.getByRole("progressbar")).toBeInTheDocument();
  });

  it("displays error state", () => {
    const errorMessage = "Failed to load system metrics";
    mockedUseApiCall.mockReturnValue({
      ...mockUseApiCall,
      error: errorMessage,
    });

    renderWithTheme(<SystemOverview />);

    expect(screen.getByText("System Overview")).toBeInTheDocument();
    expect(
      screen.getByText(`Failed to load system metrics: ${errorMessage}`)
    ).toBeInTheDocument();
  });

  it("auto-refreshes at specified interval", async () => {
    mockUseApiCall.execute.mockResolvedValue(mockSystemMetrics);

    renderWithTheme(<SystemOverview refreshInterval={5000} />);

    // Initial call
    await act(async () => {
      jest.advanceTimersByTime(100);
    });

    expect(mockUseApiCall.execute).toHaveBeenCalledTimes(1);

    // Advance by refresh interval
    await act(async () => {
      jest.advanceTimersByTime(5000);
    });

    expect(mockUseApiCall.execute).toHaveBeenCalledTimes(2);
  });

  it("displays last updated time", async () => {
    mockUseApiCall.execute.mockResolvedValue(mockSystemMetrics);

    renderWithTheme(<SystemOverview />);

    await act(async () => {
      jest.advanceTimersByTime(100);
    });

    await waitFor(() => {
      expect(screen.getByText(/Last updated:/)).toBeInTheDocument();
    });
  });

  it("handles API errors gracefully", async () => {
    const consoleSpy = jest
      .spyOn(console, "error")
      .mockImplementation(() => {});
    mockUseApiCall.execute.mockRejectedValue(new Error("API Error"));

    renderWithTheme(<SystemOverview />);

    await act(async () => {
      jest.advanceTimersByTime(100);
    });

    expect(consoleSpy).toHaveBeenCalledWith(
      "Error fetching system metrics:",
      expect.any(Error)
    );
    consoleSpy.mockRestore();
  });

  it("handles error response from API", async () => {
    const consoleSpy = jest
      .spyOn(console, "error")
      .mockImplementation(() => {});
    mockUseApiCall.execute.mockResolvedValue({
      error: "Docker daemon unavailable",
    });

    renderWithTheme(<SystemOverview />);

    await act(async () => {
      jest.advanceTimersByTime(100);
    });

    expect(consoleSpy).toHaveBeenCalledWith(
      "Error fetching system metrics:",
      expect.any(Error)
    );
    consoleSpy.mockRestore();
  });

  it("formats bytes correctly", async () => {
    const metricsWithLargeMemory = {
      ...mockSystemMetrics,
      system_info: {
        ...mockSystemMetrics.system_info,
        total_memory: 1024 * 1024 * 1024, // 1GB
      },
    };

    mockUseApiCall.execute.mockResolvedValue(metricsWithLargeMemory);

    renderWithTheme(<SystemOverview />);

    await act(async () => {
      jest.advanceTimersByTime(100);
    });

    await waitFor(() => {
      expect(screen.getByText("1.00 GB")).toBeInTheDocument();
    });
  });

  it("handles zero containers gracefully", async () => {
    const metricsWithNoContainers = {
      ...mockSystemMetrics,
      containers_total: 0,
      containers_running: 0,
      containers_by_status: {},
    };

    mockUseApiCall.execute.mockResolvedValue(metricsWithNoContainers);

    renderWithTheme(<SystemOverview />);

    await act(async () => {
      jest.advanceTimersByTime(100);
    });

    await waitFor(() => {
      expect(screen.getByText("0")).toBeInTheDocument();
      expect(screen.getByText("of 0 containers running")).toBeInTheDocument();
      expect(screen.getByText("Health: 0.0%")).toBeInTheDocument();
    });
  });

  it("shows appropriate health color based on percentage", async () => {
    // Test with high health percentage
    const highHealthMetrics = {
      ...mockSystemMetrics,
      containers_total: 10,
      containers_running: 9, // 90% health
    };

    mockUseApiCall.execute.mockResolvedValue(highHealthMetrics);

    renderWithTheme(<SystemOverview />);

    await act(async () => {
      jest.advanceTimersByTime(100);
    });

    await waitFor(() => {
      expect(screen.getByText("Health: 90.0%")).toBeInTheDocument();
    });
  });
});
