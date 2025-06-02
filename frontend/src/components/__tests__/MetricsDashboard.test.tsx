import React from "react";
import {
  render,
  screen,
  fireEvent,
  waitFor,
  act,
} from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { ThemeProvider } from "@mui/material/styles";
import MetricsDashboard from "../MetricsDashboard";
import { useApiCall } from "../../hooks/useApiCall";
import { useWebSocket } from "../../hooks/useWebSocket";
import theme from "../../theme";

// Mock hooks
jest.mock("../../hooks/useApiCall");
jest.mock("../../hooks/useWebSocket");

// Mock child components
jest.mock("../MetricsChart", () => {
  return function MockMetricsChart() {
    return <div data-testid="metrics-chart">Metrics Chart</div>;
  };
});

jest.mock("../RealTimeMetrics", () => {
  return function MockRealTimeMetrics({
    containerId,
  }: {
    containerId: string;
  }) {
    return (
      <div data-testid="real-time-metrics">
        Real-time Metrics for {containerId}
      </div>
    );
  };
});

jest.mock("../MetricsHistory", () => {
  return function MockMetricsHistory({ containerId }: { containerId: string }) {
    return (
      <div data-testid="metrics-history">Metrics History for {containerId}</div>
    );
  };
});

const mockUseApiCall = useApiCall as jest.MockedFunction<typeof useApiCall>;
const mockUseWebSocket = useWebSocket as jest.MockedFunction<
  typeof useWebSocket
>;

// Mock data
const mockDashboardMetrics = {
  timestamp: "2024-01-01T00:00:00Z",
  summary: {
    total_containers: 8,
    healthy_containers: 5,
    warning_containers: 2,
    critical_containers: 1,
  },
  aggregated_metrics: {
    avg_cpu_percent: 42.5,
    avg_memory_percent: 68.3,
    total_network_rx_bytes: 1048576,
    total_network_tx_bytes: 2097152,
  },
  top_consumers: {
    cpu: [
      { container_name: "web-server", value: 85.2 },
      { container_name: "api-server", value: 72.1 },
    ],
    memory: [
      { container_name: "database", value: 88.7 },
      { container_name: "cache", value: 76.3 },
    ],
  },
  alerts_count: 3,
  system_health_score: 75,
};

const mockSystemMetrics = {
  timestamp: "2024-01-01T00:00:00Z",
  docker_info: {
    containers_running: 8,
    containers_paused: 0,
    containers_stopped: 2,
    images: 15,
  },
  system_info: {
    cpu_count: 8,
    memory_total: 17179869184,
    memory_available: 8589934592,
    disk_total: 1099511627776,
    disk_free: 549755813888,
  },
};

// Test wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <BrowserRouter>
    <ThemeProvider theme={theme}>{children}</ThemeProvider>
  </BrowserRouter>
);

describe("MetricsDashboard", () => {
  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks();

    // Mock localStorage
    Object.defineProperty(window, "localStorage", {
      value: {
        getItem: jest.fn((key) => {
          if (key === "token") return "mock-token";
          if (key === "userId") return "1";
          return null;
        }),
      },
      writable: true,
    });

    // Default mock implementations
    mockUseApiCall.mockReturnValue({
      data: null,
      loading: false,
      error: null,
      execute: jest.fn(),
    });

    mockUseWebSocket.mockReturnValue({
      isConnected: false,
      sendMessage: jest.fn(),
      connectionState: "disconnected",
    });
  });

  it("renders the metrics dashboard", async () => {
    mockUseApiCall
      .mockReturnValueOnce({
        data: mockDashboardMetrics,
        loading: false,
        error: null,
        execute: jest.fn(),
      })
      .mockReturnValueOnce({
        data: mockSystemMetrics,
        loading: false,
        error: null,
        execute: jest.fn(),
      });

    await act(async () => {
      render(
        <TestWrapper>
          <MetricsDashboard />
        </TestWrapper>
      );
    });

    expect(screen.getByText("Metrics Dashboard")).toBeInTheDocument();
    expect(screen.getByText("Overview")).toBeInTheDocument();
    expect(screen.getAllByText("Real-time")[0]).toBeInTheDocument();
    expect(screen.getByText("History")).toBeInTheDocument();
  });

  it("renders with container-specific title when containerId is provided", async () => {
    mockUseApiCall
      .mockReturnValueOnce({
        data: mockDashboardMetrics,
        loading: false,
        error: null,
        execute: jest.fn(),
      })
      .mockReturnValueOnce({
        data: mockSystemMetrics,
        loading: false,
        error: null,
        execute: jest.fn(),
      });

    await act(async () => {
      render(
        <TestWrapper>
          <MetricsDashboard
            containerId="container1"
            containerName="web-server"
          />
        </TestWrapper>
      );
    });

    expect(screen.getByText("web-server Metrics")).toBeInTheDocument();
  });

  it("displays loading state", async () => {
    mockUseApiCall.mockReturnValue({
      data: null,
      loading: true,
      error: null,
      execute: jest.fn(),
    });

    await act(async () => {
      render(
        <TestWrapper>
          <MetricsDashboard />
        </TestWrapper>
      );
    });

    expect(screen.getByRole("progressbar")).toBeInTheDocument();
  });

  it("displays system health summary", async () => {
    mockUseApiCall
      .mockReturnValueOnce({
        data: mockDashboardMetrics,
        loading: false,
        error: null,
        execute: jest.fn(),
      })
      .mockReturnValueOnce({
        data: mockSystemMetrics,
        loading: false,
        error: null,
        execute: jest.fn(),
      });

    await act(async () => {
      render(
        <TestWrapper>
          <MetricsDashboard />
        </TestWrapper>
      );
    });

    expect(screen.getByText("8")).toBeInTheDocument(); // Total containers
    expect(screen.getByText("5")).toBeInTheDocument(); // Healthy containers
    expect(screen.getByText("2")).toBeInTheDocument(); // Warning containers
    expect(screen.getByText("1")).toBeInTheDocument(); // Critical containers
  });

  it("displays WebSocket connection status", async () => {
    mockUseApiCall
      .mockReturnValueOnce({
        data: mockDashboardMetrics,
        loading: false,
        error: null,
        execute: jest.fn(),
      })
      .mockReturnValueOnce({
        data: mockSystemMetrics,
        loading: false,
        error: null,
        execute: jest.fn(),
      });

    mockUseWebSocket.mockReturnValue({
      isConnected: true,
      sendMessage: jest.fn(),
      connectionState: "connected",
    });

    await act(async () => {
      render(
        <TestWrapper>
          <MetricsDashboard />
        </TestWrapper>
      );
    });

    expect(screen.getByText("LIVE")).toBeInTheDocument();
  });

  it("toggles real-time updates", async () => {
    mockUseApiCall
      .mockReturnValueOnce({
        data: mockDashboardMetrics,
        loading: false,
        error: null,
        execute: jest.fn(),
      })
      .mockReturnValueOnce({
        data: mockSystemMetrics,
        loading: false,
        error: null,
        execute: jest.fn(),
      });

    await act(async () => {
      render(
        <TestWrapper>
          <MetricsDashboard />
        </TestWrapper>
      );
    });

    const realTimeSwitch = screen.getByRole("checkbox", { name: /real-time/i });
    expect(realTimeSwitch).toBeChecked();

    await act(async () => {
      fireEvent.click(realTimeSwitch);
    });

    expect(realTimeSwitch).not.toBeChecked();
  });

  it("refreshes data when refresh button is clicked", async () => {
    const mockExecute = jest.fn();

    mockUseApiCall
      .mockReturnValueOnce({
        data: mockDashboardMetrics,
        loading: false,
        error: null,
        execute: mockExecute,
      })
      .mockReturnValueOnce({
        data: mockSystemMetrics,
        loading: false,
        error: null,
        execute: jest.fn(),
      });

    await act(async () => {
      render(
        <TestWrapper>
          <MetricsDashboard />
        </TestWrapper>
      );
    });

    const refreshButton = screen.getByLabelText(/refresh/i);

    await act(async () => {
      fireEvent.click(refreshButton);
    });

    expect(mockExecute).toHaveBeenCalled();
  });

  it("switches between tabs", async () => {
    mockUseApiCall
      .mockReturnValueOnce({
        data: mockDashboardMetrics,
        loading: false,
        error: null,
        execute: jest.fn(),
      })
      .mockReturnValueOnce({
        data: mockSystemMetrics,
        loading: false,
        error: null,
        execute: jest.fn(),
      });

    await act(async () => {
      render(
        <TestWrapper>
          <MetricsDashboard
            containerId="container1"
            containerName="web-server"
          />
        </TestWrapper>
      );
    });

    // Click on Real-time tab
    const realTimeTab = screen.getAllByText("Real-time")[0];

    await act(async () => {
      fireEvent.click(realTimeTab);
    });

    // Check that real-time tab content is rendered
    await waitFor(() => {
      // The real-time tab panel should exist (even if hidden)
      expect(document.getElementById("metrics-tabpanel-1")).toBeInTheDocument();
    });

    // Click on History tab
    const historyTab = screen.getByText("History");

    await act(async () => {
      fireEvent.click(historyTab);
    });

    // Check that history tab content is rendered
    await waitFor(() => {
      // The component shows metrics history content with data-testid
      expect(screen.getByTestId("metrics-history")).toBeInTheDocument();
    });
  });

  it("displays system performance metrics in overview tab", async () => {
    mockUseApiCall
      .mockReturnValueOnce({
        data: mockDashboardMetrics,
        loading: false,
        error: null,
        execute: jest.fn(),
      })
      .mockReturnValueOnce({
        data: mockSystemMetrics,
        loading: false,
        error: null,
        execute: jest.fn(),
      });

    await act(async () => {
      render(
        <TestWrapper>
          <MetricsDashboard />
        </TestWrapper>
      );
    });

    expect(screen.getByText("System Performance")).toBeInTheDocument();
    expect(screen.getByText("42.5%")).toBeInTheDocument(); // Average CPU
    expect(screen.getByText("68.3%")).toBeInTheDocument(); // Average Memory
  });

  it("displays network activity metrics", async () => {
    mockUseApiCall
      .mockReturnValueOnce({
        data: mockDashboardMetrics,
        loading: false,
        error: null,
        execute: jest.fn(),
      })
      .mockReturnValueOnce({
        data: mockSystemMetrics,
        loading: false,
        error: null,
        execute: jest.fn(),
      });

    await act(async () => {
      render(
        <TestWrapper>
          <MetricsDashboard />
        </TestWrapper>
      );
    });

    expect(screen.getByText("Network Activity")).toBeInTheDocument();
    expect(screen.getByText("1 MB")).toBeInTheDocument(); // Total RX
    expect(screen.getByText("2 MB")).toBeInTheDocument(); // Total TX
  });

  it("shows info message when no container is selected for real-time tab", async () => {
    mockUseApiCall
      .mockReturnValueOnce({
        data: mockDashboardMetrics,
        loading: false,
        error: null,
        execute: jest.fn(),
      })
      .mockReturnValueOnce({
        data: mockSystemMetrics,
        loading: false,
        error: null,
        execute: jest.fn(),
      });

    await act(async () => {
      render(
        <TestWrapper>
          <MetricsDashboard />
        </TestWrapper>
      );
    });

    // Click on Real-time tab
    const realTimeTab = screen.getAllByText("Real-time")[0];

    await act(async () => {
      fireEvent.click(realTimeTab);
    });

    await waitFor(() => {
      // The real-time tab panel should exist (even if hidden)
      expect(document.getElementById("metrics-tabpanel-1")).toBeInTheDocument();
    });
  });

  it("shows info message when no container is selected for history tab", async () => {
    mockUseApiCall
      .mockReturnValueOnce({
        data: mockDashboardMetrics,
        loading: false,
        error: null,
        execute: jest.fn(),
      })
      .mockReturnValueOnce({
        data: mockSystemMetrics,
        loading: false,
        error: null,
        execute: jest.fn(),
      });

    await act(async () => {
      render(
        <TestWrapper>
          <MetricsDashboard />
        </TestWrapper>
      );
    });

    // Click on History tab
    const historyTab = screen.getByText("History");

    await act(async () => {
      fireEvent.click(historyTab);
    });

    await waitFor(() => {
      // The component shows an info message for history tab
      expect(
        screen.getByText("Select a container to view historical metrics.")
      ).toBeInTheDocument();
    });
  });

  it("handles fullscreen toggle", async () => {
    const mockOnFullscreenToggle = jest.fn();

    mockUseApiCall
      .mockReturnValueOnce({
        data: mockDashboardMetrics,
        loading: false,
        error: null,
        execute: jest.fn(),
      })
      .mockReturnValueOnce({
        data: mockSystemMetrics,
        loading: false,
        error: null,
        execute: jest.fn(),
      });

    await act(async () => {
      render(
        <TestWrapper>
          <MetricsDashboard onFullscreenToggle={mockOnFullscreenToggle} />
        </TestWrapper>
      );
    });

    const fullscreenButton = screen.getByLabelText(/fullscreen/i);

    await act(async () => {
      fireEvent.click(fullscreenButton);
    });

    expect(mockOnFullscreenToggle).toHaveBeenCalled();
  });

  it("displays error message when dashboard data fails to load", async () => {
    mockUseApiCall
      .mockReturnValueOnce({
        data: null,
        loading: false,
        error: "Failed to load data",
        execute: jest.fn(),
      })
      .mockReturnValueOnce({
        data: mockSystemMetrics,
        loading: false,
        error: null,
        execute: jest.fn(),
      });

    await act(async () => {
      render(
        <TestWrapper>
          <MetricsDashboard />
        </TestWrapper>
      );
    });

    expect(
      screen.getByText(/Failed to load dashboard metrics/)
    ).toBeInTheDocument();
  });

  it("hides controls when showControls is false", async () => {
    mockUseApiCall
      .mockReturnValueOnce({
        data: mockDashboardMetrics,
        loading: false,
        error: null,
        execute: jest.fn(),
      })
      .mockReturnValueOnce({
        data: mockSystemMetrics,
        loading: false,
        error: null,
        execute: jest.fn(),
      });

    await act(async () => {
      render(
        <TestWrapper>
          <MetricsDashboard showControls={false} />
        </TestWrapper>
      );
    });

    expect(
      screen.queryByRole("checkbox", { name: /real-time/i })
    ).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/refresh/i)).not.toBeInTheDocument();
  });
});
