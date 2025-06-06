import React from "react";
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { ThemeProvider } from "@mui/material/styles";
import ProductionMonitoring from "./ProductionMonitoring";
import { useApiCall } from "../hooks/useApiCall";
import { useWebSocket } from "../hooks/useWebSocket";
import theme from "../theme";

// Mock hooks
jest.mock("../hooks/useApiCall");
jest.mock("../hooks/useWebSocket");

const mockedUseApiCall = useApiCall as jest.MockedFunction<typeof useApiCall>;
const mockedUseWebSocket = useWebSocket as jest.MockedFunction<typeof useWebSocket>;

// Test wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <BrowserRouter>
    <ThemeProvider theme={theme}>{children}</ThemeProvider>
  </BrowserRouter>
);

// Mock production metrics data
const mockProductionMetrics = {
  timestamp: "2024-01-15T10:30:00Z",
  api_performance: {
    avg_response_time: 150,
    p95_response_time: 280,
    p99_response_time: 450,
    requests_per_minute: 120,
    error_rate: 2.5,
  },
  system_health: {
    cpu_usage: 45.2,
    memory_usage: 62.8,
    disk_usage: 35.1,
    network_latency: 12,
    uptime_percentage: 99.95,
  },
  container_metrics: {
    total_containers: 15,
    running_containers: 12,
    failed_containers: 2,
    resource_alerts: 1,
  },
  alerts: [
    {
      id: "alert_1",
      type: "warning" as const,
      message: "High memory usage detected",
      timestamp: "2024-01-15T10:25:00Z",
      container_id: "container_123",
    },
    {
      id: "alert_2",
      type: "error" as const,
      message: "Container failed to start",
      timestamp: "2024-01-15T10:20:00Z",
      container_id: "container_456",
    },
  ],
  health_score: 85,
};

const mockSystemHealth = {
  status: "healthy",
  message: "All systems operational",
  health_score: 85,
  timestamp: "2024-01-15T10:30:00Z",
};

// Mock useApiCall return value
const mockUseApiCall = {
  data: null,
  loading: false,
  error: null,
  execute: jest.fn(),
};

// Mock useWebSocket return value
const mockUseWebSocket = {
  isConnected: true,
  connectionState: "connected" as const,
};

describe("ProductionMonitoring", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Reset mocks to default state
    mockUseApiCall.data = null;
    mockUseApiCall.loading = false;
    mockUseApiCall.error = null;
    mockUseApiCall.execute.mockClear();
    
    mockedUseApiCall.mockReturnValue(mockUseApiCall);
    mockedUseWebSocket.mockReturnValue(mockUseWebSocket);
  });

  test("renders production monitoring dashboard", async () => {
    await act(async () => {
      render(
        <TestWrapper>
          <ProductionMonitoring />
        </TestWrapper>
      );
    });

    expect(screen.getByText("Production Monitoring")).toBeInTheDocument();
    expect(screen.getByText("Real-time")).toBeInTheDocument();
    expect(screen.getByLabelText("Refresh")).toBeInTheDocument();
  });

  test("displays production metrics when loaded", async () => {
    mockUseApiCall.data = mockProductionMetrics;
    mockedUseApiCall.mockReturnValue(mockUseApiCall);

    await act(async () => {
      render(
        <TestWrapper>
          <ProductionMonitoring />
        </TestWrapper>
      );
    });

    await waitFor(() => {
      expect(screen.getByText("System Health")).toBeInTheDocument();
      expect(screen.getByText("85")).toBeInTheDocument(); // Health score
      expect(screen.getByText("API Performance")).toBeInTheDocument();
      expect(screen.getByText("150ms")).toBeInTheDocument(); // Avg response time
    });
  });

  test("displays system resources correctly", async () => {
    mockUseApiCall.data = mockProductionMetrics;
    mockedUseApiCall.mockReturnValue(mockUseApiCall);

    await act(async () => {
      render(
        <TestWrapper>
          <ProductionMonitoring />
        </TestWrapper>
      );
    });

    await waitFor(() => {
      expect(screen.getByText("System Resources")).toBeInTheDocument();
      expect(screen.getByText("CPU Usage")).toBeInTheDocument();
      expect(screen.getByText("45.2%")).toBeInTheDocument();
      expect(screen.getByText("Memory Usage")).toBeInTheDocument();
      expect(screen.getByText("62.8%")).toBeInTheDocument();
    });
  });

  test("displays container status correctly", async () => {
    mockUseApiCall.data = mockProductionMetrics;
    mockedUseApiCall.mockReturnValue(mockUseApiCall);

    await act(async () => {
      render(
        <TestWrapper>
          <ProductionMonitoring />
        </TestWrapper>
      );
    });

    await waitFor(() => {
      expect(screen.getByText("Container Status")).toBeInTheDocument();
      expect(screen.getByText("15")).toBeInTheDocument(); // Total containers
      expect(screen.getByText("12")).toBeInTheDocument(); // Running containers
      expect(screen.getByText("2")).toBeInTheDocument(); // Failed containers
    });
  });

  test("displays recent alerts", async () => {
    mockUseApiCall.data = mockProductionMetrics;
    mockedUseApiCall.mockReturnValue(mockUseApiCall);

    await act(async () => {
      render(
        <TestWrapper>
          <ProductionMonitoring />
        </TestWrapper>
      );
    });

    await waitFor(() => {
      expect(screen.getByText("Recent Alerts")).toBeInTheDocument();
      expect(screen.getByText("High memory usage detected")).toBeInTheDocument();
      expect(screen.getByText("Container failed to start")).toBeInTheDocument();
    });
  });

  test("handles loading state", async () => {
    mockUseApiCall.loading = true;
    mockedUseApiCall.mockReturnValue(mockUseApiCall);

    await act(async () => {
      render(
        <TestWrapper>
          <ProductionMonitoring />
        </TestWrapper>
      );
    });

    expect(screen.getByRole("progressbar")).toBeInTheDocument();
  });

  test("handles error state", async () => {
    mockUseApiCall.error = "Failed to load production metrics";
    mockedUseApiCall.mockReturnValue(mockUseApiCall);

    await act(async () => {
      render(
        <TestWrapper>
          <ProductionMonitoring />
        </TestWrapper>
      );
    });

    await waitFor(() => {
      expect(screen.getByText(/Failed to load production metrics/)).toBeInTheDocument();
    });
  });

  test("handles refresh button click", async () => {
    await act(async () => {
      render(
        <TestWrapper>
          <ProductionMonitoring />
        </TestWrapper>
      );
    });

    const refreshButton = screen.getByLabelText("Refresh");
    
    await act(async () => {
      fireEvent.click(refreshButton);
    });

    expect(mockUseApiCall.execute).toHaveBeenCalledWith("/api/production/metrics");
  });

  test("toggles real-time monitoring", async () => {
    await act(async () => {
      render(
        <TestWrapper>
          <ProductionMonitoring />
        </TestWrapper>
      );
    });

    const realTimeSwitch = screen.getByRole("checkbox");
    
    await act(async () => {
      fireEvent.click(realTimeSwitch);
    });

    // Should toggle the switch state
    expect(realTimeSwitch).not.toBeChecked();
  });

  test("displays WebSocket connection status", async () => {
    mockUseWebSocket.isConnected = true;
    mockedUseWebSocket.mockReturnValue(mockUseWebSocket);

    await act(async () => {
      render(
        <TestWrapper>
          <ProductionMonitoring />
        </TestWrapper>
      );
    });

    expect(screen.getByText("LIVE")).toBeInTheDocument();
  });

  test("displays connecting status when WebSocket is not connected", async () => {
    mockUseWebSocket.isConnected = false;
    mockedUseWebSocket.mockReturnValue(mockUseWebSocket);

    await act(async () => {
      render(
        <TestWrapper>
          <ProductionMonitoring />
        </TestWrapper>
      );
    });

    expect(screen.getByText("CONNECTING")).toBeInTheDocument();
  });

  test("displays alerts count badge", async () => {
    mockUseApiCall.data = mockProductionMetrics;
    mockedUseApiCall.mockReturnValue(mockUseApiCall);

    await act(async () => {
      render(
        <TestWrapper>
          <ProductionMonitoring />
        </TestWrapper>
      );
    });

    // Should show alerts count in the badge
    await waitFor(() => {
      expect(screen.getByText("2")).toBeInTheDocument(); // Alert count chip
    });
  });

  test("handles auto-refresh with custom interval", async () => {
    await act(async () => {
      render(
        <TestWrapper>
          <ProductionMonitoring autoRefresh={true} refreshInterval={5000} />
        </TestWrapper>
      );
    });

    // Initial API calls should be made
    expect(mockUseApiCall.execute).toHaveBeenCalledWith("/api/production/metrics");
    expect(mockUseApiCall.execute).toHaveBeenCalledWith("/api/system/health");
  });

  test("disables refresh button when loading", async () => {
    mockUseApiCall.loading = true;
    mockedUseApiCall.mockReturnValue(mockUseApiCall);

    await act(async () => {
      render(
        <TestWrapper>
          <ProductionMonitoring />
        </TestWrapper>
      );
    });

    const refreshButton = screen.getByLabelText("Refresh");
    expect(refreshButton).toBeDisabled();
  });
}, 30000);
