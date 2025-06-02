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
import MetricsVisualization from "../MetricsVisualization";
import { useApiCall } from "../../hooks/useApiCall";
import { useWebSocket } from "../../hooks/useWebSocket";
import theme from "../../theme";

// Mock hooks
jest.mock("../../hooks/useApiCall");
jest.mock("../../hooks/useWebSocket");

const mockUseApiCall = useApiCall as jest.MockedFunction<typeof useApiCall>;
const mockUseWebSocket = useWebSocket as jest.MockedFunction<
  typeof useWebSocket
>;

// Mock data
const mockMetricsSummary = {
  timestamp: "2024-01-01T00:00:00Z",
  summary: {
    total_containers: 5,
    healthy_containers: 3,
    warning_containers: 1,
    critical_containers: 1,
  },
  aggregated_metrics: {
    avg_cpu_percent: 45.5,
    avg_memory_percent: 62.3,
  },
  alerts: {
    high_cpu_containers: [
      {
        container_id: "container1",
        container_name: "web-server",
        cpu_percent: 85.2,
      },
    ],
    high_memory_containers: [
      {
        container_id: "container2",
        container_name: "database",
        memory_percent: 88.7,
      },
    ],
  },
  health_scores: {
    container1: 65,
    container2: 45,
    container3: 90,
  },
  individual_metrics: {
    container1: {
      container_id: "container1",
      container_name: "web-server",
      cpu_percent: 85.2,
      memory_percent: 70.5,
      memory_usage: 1073741824,
      memory_limit: 2147483648,
      network_rx_bytes: 1024,
      network_tx_bytes: 2048,
      block_read_bytes: 4096,
      block_write_bytes: 8192,
      status: "running",
      timestamp: "2024-01-01T00:00:00Z",
    },
    container2: {
      container_id: "container2",
      container_name: "database",
      cpu_percent: 45.8,
      memory_percent: 88.7,
      memory_usage: 2147483648,
      memory_limit: 4294967296,
      network_rx_bytes: 2048,
      network_tx_bytes: 4096,
      block_read_bytes: 8192,
      block_write_bytes: 16384,
      status: "running",
      timestamp: "2024-01-01T00:00:00Z",
    },
    container3: {
      container_id: "container3",
      container_name: "cache",
      cpu_percent: 15.3,
      memory_percent: 35.2,
      memory_usage: 536870912,
      memory_limit: 1073741824,
      network_rx_bytes: 512,
      network_tx_bytes: 1024,
      block_read_bytes: 2048,
      block_write_bytes: 4096,
      status: "running",
      timestamp: "2024-01-01T00:00:00Z",
    },
  },
};

const mockContainers = [
  { id: "container1", name: "web-server" },
  { id: "container2", name: "database" },
  { id: "container3", name: "cache" },
];

const mockAggregatedMetrics = {
  timestamp: "2024-01-01T00:00:00Z",
  container_count: 2,
  total_containers: 2,
  aggregated_metrics: {
    avg_cpu_percent: 65.5,
    total_memory_usage: 3221225472,
    total_memory_limit: 6442450944,
    avg_memory_percent: 79.6,
    total_network_rx_bytes: 3072,
    total_network_tx_bytes: 6144,
    total_block_read_bytes: 12288,
    total_block_write_bytes: 24576,
  },
  individual_stats: {
    container1: mockMetricsSummary.individual_metrics.container1,
    container2: mockMetricsSummary.individual_metrics.container2,
  },
};

// Test wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <BrowserRouter>
    <ThemeProvider theme={theme}>{children}</ThemeProvider>
  </BrowserRouter>
);

describe("MetricsVisualization", () => {
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

  it("renders the metrics visualization page", async () => {
    mockUseApiCall
      .mockReturnValueOnce({
        data: mockContainers,
        loading: false,
        error: null,
        execute: jest.fn(),
      })
      .mockReturnValueOnce({
        data: mockMetricsSummary,
        loading: false,
        error: null,
        execute: jest.fn(),
      });

    await act(async () => {
      render(
        <TestWrapper>
          <MetricsVisualization />
        </TestWrapper>
      );
    });

    expect(
      screen.getByText("Advanced Metrics Visualization")
    ).toBeInTheDocument();
    expect(screen.getByText("System Overview")).toBeInTheDocument();
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
          <MetricsVisualization />
        </TestWrapper>
      );
    });

    expect(screen.getByRole("progressbar")).toBeInTheDocument();
  });

  it("displays error state when data fails to load", async () => {
    mockUseApiCall.mockReturnValue({
      data: null,
      loading: false,
      error: "Failed to load data",
      execute: jest.fn(),
    });

    await act(async () => {
      render(
        <TestWrapper>
          <MetricsVisualization />
        </TestWrapper>
      );
    });

    expect(screen.getByText(/Failed to load metrics data/)).toBeInTheDocument();
  });

  it("displays system overview metrics", async () => {
    mockUseApiCall
      .mockReturnValueOnce({
        data: mockContainers,
        loading: false,
        error: null,
        execute: jest.fn(),
      })
      .mockReturnValueOnce({
        data: mockMetricsSummary,
        loading: false,
        error: null,
        execute: jest.fn(),
      });

    await act(async () => {
      render(
        <TestWrapper>
          <MetricsVisualization />
        </TestWrapper>
      );
    });

    expect(screen.getByText("5")).toBeInTheDocument(); // Total containers
    expect(screen.getByText("3")).toBeInTheDocument(); // Healthy containers
    expect(screen.getAllByText("1")[0]).toBeInTheDocument(); // Warning containers
    expect(screen.getAllByText("1")[1]).toBeInTheDocument(); // Critical containers
  });

  it("displays health scores for containers", async () => {
    mockUseApiCall
      .mockReturnValueOnce({
        data: mockContainers,
        loading: false,
        error: null,
        execute: jest.fn(),
      })
      .mockReturnValueOnce({
        data: mockMetricsSummary,
        loading: false,
        error: null,
        execute: jest.fn(),
      });

    await act(async () => {
      render(
        <TestWrapper>
          <MetricsVisualization />
        </TestWrapper>
      );
    });

    expect(screen.getByText("Container Health Scores")).toBeInTheDocument();
    expect(screen.getByText("65")).toBeInTheDocument(); // Health score for container1
    expect(screen.getByText("45")).toBeInTheDocument(); // Health score for container2
    expect(screen.getByText("90")).toBeInTheDocument(); // Health score for container3
  });

  it("allows container selection for detailed analysis", async () => {
    mockUseApiCall
      .mockReturnValueOnce({
        data: mockContainers,
        loading: false,
        error: null,
        execute: jest.fn(),
      })
      .mockReturnValueOnce({
        data: mockMetricsSummary,
        loading: false,
        error: null,
        execute: jest.fn(),
      });

    await act(async () => {
      render(
        <TestWrapper>
          <MetricsVisualization />
        </TestWrapper>
      );
    });

    // Find and click on a container chip
    const containerChip = screen.getByText("web-server");
    expect(containerChip).toBeInTheDocument();

    await act(async () => {
      fireEvent.click(containerChip);
    });

    // Container should be selected (chip should change appearance)
    expect(containerChip.closest(".MuiChip-root")).toHaveClass(
      "MuiChip-filled"
    );
  });

  it("displays alerts when containers have high resource usage", async () => {
    mockUseApiCall
      .mockReturnValueOnce({
        data: mockContainers,
        loading: false,
        error: null,
        execute: jest.fn(),
      })
      .mockReturnValueOnce({
        data: mockMetricsSummary,
        loading: false,
        error: null,
        execute: jest.fn(),
      });

    await act(async () => {
      render(
        <TestWrapper>
          <MetricsVisualization />
        </TestWrapper>
      );
    });

    expect(screen.getByText("Active Alerts")).toBeInTheDocument();
    expect(screen.getByText("High CPU Usage Containers")).toBeInTheDocument();
    expect(
      screen.getByText("High Memory Usage Containers")
    ).toBeInTheDocument();
    expect(screen.getByText(/web-server: 85.2%/)).toBeInTheDocument();
    expect(screen.getByText(/database: 88.7%/)).toBeInTheDocument();
  });

  it("toggles real-time updates", async () => {
    mockUseApiCall
      .mockReturnValueOnce({
        data: mockContainers,
        loading: false,
        error: null,
        execute: jest.fn(),
      })
      .mockReturnValueOnce({
        data: mockMetricsSummary,
        loading: false,
        error: null,
        execute: jest.fn(),
      });

    await act(async () => {
      render(
        <TestWrapper>
          <MetricsVisualization />
        </TestWrapper>
      );
    });

    const realTimeSwitch = screen.getByRole("checkbox", {
      name: /real-time updates/i,
    });
    expect(realTimeSwitch).toBeChecked();

    await act(async () => {
      fireEvent.click(realTimeSwitch);
    });

    expect(realTimeSwitch).not.toBeChecked();
  });

  it("changes time range selection", async () => {
    mockUseApiCall
      .mockReturnValueOnce({
        data: mockContainers,
        loading: false,
        error: null,
        execute: jest.fn(),
      })
      .mockReturnValueOnce({
        data: mockMetricsSummary,
        loading: false,
        error: null,
        execute: jest.fn(),
      });

    await act(async () => {
      render(
        <TestWrapper>
          <MetricsVisualization />
        </TestWrapper>
      );
    });

    const timeRangeSelect = screen.getByLabelText("Time Range");

    await act(async () => {
      fireEvent.mouseDown(timeRangeSelect);
    });

    const lastWeekOption = screen.getByText("Last Week");

    await act(async () => {
      fireEvent.click(lastWeekOption);
    });

    expect(timeRangeSelect).toHaveTextContent("Last Week");
  });

  it("changes metric type selection", async () => {
    mockUseApiCall
      .mockReturnValueOnce({
        data: mockContainers,
        loading: false,
        error: null,
        execute: jest.fn(),
      })
      .mockReturnValueOnce({
        data: mockMetricsSummary,
        loading: false,
        error: null,
        execute: jest.fn(),
      });

    await act(async () => {
      render(
        <TestWrapper>
          <MetricsVisualization />
        </TestWrapper>
      );
    });

    const metricTypeSelect = screen.getByLabelText("Metric Type");

    await act(async () => {
      fireEvent.mouseDown(metricTypeSelect);
    });

    const memoryOption = screen.getByText("Memory Usage");

    await act(async () => {
      fireEvent.click(memoryOption);
    });

    expect(metricTypeSelect).toHaveTextContent("Memory Usage");
  });

  it("refreshes data when refresh button is clicked", async () => {
    const mockExecute = jest.fn();

    mockUseApiCall
      .mockReturnValueOnce({
        data: mockContainers,
        loading: false,
        error: null,
        execute: jest.fn(),
      })
      .mockReturnValueOnce({
        data: mockMetricsSummary,
        loading: false,
        error: null,
        execute: mockExecute,
      });

    await act(async () => {
      render(
        <TestWrapper>
          <MetricsVisualization />
        </TestWrapper>
      );
    });

    const refreshButton = screen.getByLabelText(/refresh/i);

    await act(async () => {
      fireEvent.click(refreshButton);
    });

    expect(mockExecute).toHaveBeenCalled();
  });

  it("displays WebSocket connection status", async () => {
    mockUseApiCall
      .mockReturnValueOnce({
        data: mockContainers,
        loading: false,
        error: null,
        execute: jest.fn(),
      })
      .mockReturnValueOnce({
        data: mockMetricsSummary,
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
          <MetricsVisualization />
        </TestWrapper>
      );
    });

    expect(screen.getByText("WebSocket Status:")).toBeInTheDocument();
    expect(screen.getByText("connected")).toBeInTheDocument();
  });

  it("displays aggregated metrics when containers are selected", async () => {
    const mockExecuteAggregated = jest.fn();

    mockUseApiCall
      .mockReturnValueOnce({
        data: mockContainers,
        loading: false,
        error: null,
        execute: jest.fn(),
      })
      .mockReturnValueOnce({
        data: mockMetricsSummary,
        loading: false,
        error: null,
        execute: jest.fn(),
      })
      .mockReturnValueOnce({
        data: mockAggregatedMetrics,
        loading: false,
        error: null,
        execute: mockExecuteAggregated,
      });

    await act(async () => {
      render(
        <TestWrapper>
          <MetricsVisualization />
        </TestWrapper>
      );
    });

    // Select a container
    const containerChip = screen.getByText("web-server");

    await act(async () => {
      fireEvent.click(containerChip);
    });

    await waitFor(() => {
      expect(
        screen.getByText("Aggregated Metrics for Selected Containers")
      ).toBeInTheDocument();
    });
  });
});
