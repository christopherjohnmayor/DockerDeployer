import React from "react";
import { screen, waitFor, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { render, mockAuthContext } from "../utils/testUtils";
import ContainerMetricsVisualization from "./ContainerMetricsVisualization";

// Mock the useApiCall hook
const mockExecute = jest.fn();

jest.mock("../hooks/useApiCall", () => ({
  useApiCall: jest.fn(() => ({
    data: null,
    loading: false,
    error: null,
    execute: mockExecute,
  })),
}));

// Mock MetricsChart component
jest.mock("./MetricsChart", () => {
  return function MockMetricsChart({
    title,
    loading,
  }: {
    title: string;
    loading?: boolean;
  }) {
    if (loading) {
      return <div data-testid="metrics-chart-loading">Loading chart...</div>;
    }
    return <div data-testid="metrics-chart">{title}</div>;
  };
});

// Mock formatters
jest.mock("../utils/formatters", () => ({
  formatBytes: (bytes: number) => `${bytes} B`,
  formatPercentage: (value: number) => `${value}%`,
}));

describe("ContainerMetricsVisualization", () => {
  const defaultProps = {
    containerId: "test-container-123",
    autoRefresh: false, // Disable auto-refresh for tests
  };

  beforeEach(() => {
    jest.clearAllMocks();
    const { useApiCall } = require("../hooks/useApiCall");
    useApiCall.mockReturnValue({
      data: null,
      loading: false,
      error: null,
      execute: mockExecute,
    });
  });

  it("renders the component with header controls", async () => {
    await act(async () => {
      render(<ContainerMetricsVisualization {...defaultProps} />, {
        authContext: mockAuthContext,
      });
    });

    expect(
      screen.getByText("Container Metrics Visualization")
    ).toBeInTheDocument();
    expect(screen.getByRole("combobox")).toBeInTheDocument(); // Time Range select
    expect(screen.getByLabelText("Predictions")).toBeInTheDocument();
    expect(screen.getByLabelText("Auto Refresh")).toBeInTheDocument();
    expect(screen.getByRole("button")).toBeInTheDocument(); // Refresh button
  });

  it("calls API endpoints on mount", async () => {
    await act(async () => {
      render(<ContainerMetricsVisualization {...defaultProps} />, {
        authContext: mockAuthContext,
      });
    });

    await waitFor(() => {
      expect(mockExecute).toHaveBeenCalledWith(
        expect.stringContaining(
          "/api/containers/test-container-123/metrics/visualization"
        )
      );
      expect(mockExecute).toHaveBeenCalledWith(
        expect.stringContaining(
          "/api/containers/test-container-123/health-score"
        )
      );
      expect(mockExecute).toHaveBeenCalledWith(
        expect.stringContaining(
          "/api/containers/test-container-123/metrics/predictions"
        )
      );
    });
  });

  it("updates time range and refetches data", async () => {
    const user = userEvent.setup();

    await act(async () => {
      render(<ContainerMetricsVisualization {...defaultProps} />, {
        authContext: mockAuthContext,
      });
    });

    // Clear initial calls
    mockExecute.mockClear();

    // Change time range
    const timeRangeSelect = screen.getByRole("combobox");
    await act(async () => {
      await user.click(timeRangeSelect);
    });

    await waitFor(() => {
      const sevenDaysOption = screen.getByText("7 Days");
      return user.click(sevenDaysOption);
    });

    await waitFor(() => {
      expect(mockExecute).toHaveBeenCalledWith(
        expect.stringContaining("time_range=7d&hours=168")
      );
    });
  });

  it("toggles predictions and updates API calls", async () => {
    const user = userEvent.setup();

    await act(async () => {
      render(<ContainerMetricsVisualization {...defaultProps} />, {
        authContext: mockAuthContext,
      });
    });

    // Clear initial calls
    mockExecute.mockClear();

    // Toggle predictions off
    const predictionsSwitch = screen.getByLabelText("Predictions");
    await act(async () => {
      await user.click(predictionsSwitch);
    });

    await waitFor(() => {
      // Should not call predictions endpoint when disabled
      const predictionCalls = mockExecute.mock.calls.filter((call) =>
        call[0].includes("/metrics/predictions")
      );
      expect(predictionCalls).toHaveLength(0);
    });
  });

  it("handles refresh button click", async () => {
    const user = userEvent.setup();

    await act(async () => {
      render(<ContainerMetricsVisualization {...defaultProps} />, {
        authContext: mockAuthContext,
      });
    });

    // Clear initial calls
    mockExecute.mockClear();

    // Click refresh button
    const refreshButton = screen.getByRole("button");
    await act(async () => {
      await user.click(refreshButton);
    });

    await waitFor(() => {
      expect(mockExecute).toHaveBeenCalledTimes(3); // visualization, health, predictions
    });
  });

  it("displays error message when API call fails", async () => {
    // Mock useApiCall to return error
    const { useApiCall } = require("../hooks/useApiCall");
    useApiCall.mockReturnValue({
      data: null,
      loading: false,
      error: "Failed to load metrics",
      execute: mockExecute,
    });

    await act(async () => {
      render(<ContainerMetricsVisualization {...defaultProps} />, {
        authContext: mockAuthContext,
      });
    });

    expect(
      screen.getByText(/failed to load metrics visualization/i)
    ).toBeInTheDocument();
  });

  it("shows loading state", async () => {
    // Mock useApiCall to return loading state
    const { useApiCall } = require("../hooks/useApiCall");
    useApiCall.mockReturnValue({
      data: null,
      loading: true,
      error: null,
      execute: mockExecute,
    });

    await act(async () => {
      render(<ContainerMetricsVisualization {...defaultProps} />, {
        authContext: mockAuthContext,
      });
    });

    expect(screen.getByRole("progressbar")).toBeInTheDocument();
  });

  it("renders health score card when data is available", async () => {
    const mockHealthScore = {
      overall_health_score: 85,
      health_status: "good",
      component_scores: {
        cpu_health: 80,
        memory_health: 90,
        network_health: 85,
        disk_health: 85,
      },
      recommendations: ["Container health is good - continue monitoring"],
    };

    // Mock useApiCall to return health score data
    const { useApiCall } = require("../hooks/useApiCall");
    useApiCall
      .mockReturnValueOnce({
        data: null,
        loading: false,
        error: null,
        execute: mockExecute,
      })
      .mockReturnValueOnce({
        data: mockHealthScore,
        loading: false,
        error: null,
        execute: mockExecute,
      })
      .mockReturnValueOnce({
        data: null,
        loading: false,
        error: null,
        execute: mockExecute,
      });

    await act(async () => {
      render(<ContainerMetricsVisualization {...defaultProps} />, {
        authContext: mockAuthContext,
      });
    });

    expect(screen.getByText("Container Health Score")).toBeInTheDocument();
    expect(screen.getAllByText("85/100")).toHaveLength(3); // Chip and component scores
    expect(screen.getByText("Component Health Scores")).toBeInTheDocument();
    expect(screen.getByText("Recommendations")).toBeInTheDocument();
    expect(screen.getByText(/container health is good/i)).toBeInTheDocument();
  });

  it("renders performance trends when data is available", async () => {
    const mockEnhancedMetrics = {
      trends: {
        cpu_trend: {
          direction: "stable",
          average: 25.5,
          volatility: "low",
        },
        memory_trend: {
          direction: "increasing",
          average: 30.2,
          volatility: "medium",
        },
        overall_stability: "good",
      },
      historical_metrics: [],
    };

    // Mock useApiCall to return enhanced metrics data
    const { useApiCall } = require("../hooks/useApiCall");
    useApiCall
      .mockReturnValueOnce({
        data: mockEnhancedMetrics,
        loading: false,
        error: null,
        execute: mockExecute,
      })
      .mockReturnValueOnce({
        data: null,
        loading: false,
        error: null,
        execute: mockExecute,
      })
      .mockReturnValueOnce({
        data: null,
        loading: false,
        error: null,
        execute: mockExecute,
      });

    await act(async () => {
      render(<ContainerMetricsVisualization {...defaultProps} />, {
        authContext: mockAuthContext,
      });
    });

    expect(screen.getByText("Performance Trends")).toBeInTheDocument();
    expect(screen.getByText("CPU Trend: stable")).toBeInTheDocument();
    expect(screen.getByText("Memory Trend: increasing")).toBeInTheDocument();
    expect(screen.getByText("Overall Stability: good")).toBeInTheDocument();
  });

  it("renders prediction alerts when available", async () => {
    const mockPredictions = {
      alerts: [
        {
          type: "warning",
          metric: "cpu_percent",
          message: "CPU usage predicted to reach 85% in the next few hours",
          severity: "medium",
        },
      ],
      cpu_percent: {
        values: [26, 27, 28],
        timestamps: [
          "2024-01-01T13:00:00Z",
          "2024-01-01T14:00:00Z",
          "2024-01-01T15:00:00Z",
        ],
        confidence: 0.85,
      },
      memory_percent: {
        values: [31, 32, 33],
        timestamps: [
          "2024-01-01T13:00:00Z",
          "2024-01-01T14:00:00Z",
          "2024-01-01T15:00:00Z",
        ],
        confidence: 0.8,
      },
    };

    // Mock useApiCall to return predictions data
    const { useApiCall } = require("../hooks/useApiCall");
    useApiCall
      .mockReturnValueOnce({
        data: null,
        loading: false,
        error: null,
        execute: mockExecute,
      })
      .mockReturnValueOnce({
        data: null,
        loading: false,
        error: null,
        execute: mockExecute,
      })
      .mockReturnValueOnce({
        data: mockPredictions,
        loading: false,
        error: null,
        execute: mockExecute,
      });

    await act(async () => {
      render(<ContainerMetricsVisualization {...defaultProps} />, {
        authContext: mockAuthContext,
      });
    });

    expect(screen.getByText("Prediction Alerts:")).toBeInTheDocument();
    expect(
      screen.getByText(
        "• CPU usage predicted to reach 85% in the next few hours"
      )
    ).toBeInTheDocument();
  });

  it("renders charts when historical metrics are available", async () => {
    const mockEnhancedMetrics = {
      historical_metrics: [
        {
          timestamp: "2024-01-01T12:00:00Z",
          cpu_percent: 25,
          memory_percent: 30,
        },
        {
          timestamp: "2024-01-01T13:00:00Z",
          cpu_percent: 30,
          memory_percent: 35,
        },
      ],
    };

    // Mock useApiCall to return enhanced metrics data
    const { useApiCall } = require("../hooks/useApiCall");
    useApiCall
      .mockReturnValueOnce({
        data: mockEnhancedMetrics,
        loading: false,
        error: null,
        execute: mockExecute,
      })
      .mockReturnValueOnce({
        data: null,
        loading: false,
        error: null,
        execute: mockExecute,
      })
      .mockReturnValueOnce({
        data: null,
        loading: false,
        error: null,
        execute: mockExecute,
      });

    await act(async () => {
      render(<ContainerMetricsVisualization {...defaultProps} />, {
        authContext: mockAuthContext,
      });
    });

    expect(screen.getByText("CPU Usage History")).toBeInTheDocument();
    expect(screen.getByText("Memory Usage History")).toBeInTheDocument();
  });

  it("handles auto-refresh when enabled", async () => {
    jest.useFakeTimers();

    await act(async () => {
      render(
        <ContainerMetricsVisualization
          {...defaultProps}
          autoRefresh={true}
          refreshInterval={5000}
        />,
        {
          authContext: mockAuthContext,
        }
      );
    });

    // Clear initial calls
    mockExecute.mockClear();

    // Fast-forward time
    act(() => {
      jest.advanceTimersByTime(5000);
    });

    await waitFor(() => {
      expect(mockExecute).toHaveBeenCalled();
    });

    jest.useRealTimers();
  });
});
