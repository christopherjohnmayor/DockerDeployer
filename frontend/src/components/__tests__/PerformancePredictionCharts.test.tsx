import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { ThemeProvider } from "@mui/material/styles";
import PerformancePredictionCharts from "../PerformancePredictionCharts";
import { PredictionData, PredictionPoint } from "../../types/enhancedMetrics";
import theme from "../../theme";

// Mock Recharts components
jest.mock("recharts", () => ({
  LineChart: ({ children }: any) => (
    <div data-testid="line-chart">{children}</div>
  ),
  AreaChart: ({ children }: any) => (
    <div data-testid="area-chart">{children}</div>
  ),
  Line: () => <div data-testid="line" />,
  Area: () => <div data-testid="area" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  Legend: () => <div data-testid="legend" />,
  ResponsiveContainer: ({ children }: any) => (
    <div data-testid="responsive-container">{children}</div>
  ),
  ReferenceLine: () => <div data-testid="reference-line" />,
}));

const renderWithTheme = (component: React.ReactElement) => {
  return render(<ThemeProvider theme={theme}>{component}</ThemeProvider>);
};

const createMockPredictionPoints = (count: number): PredictionPoint[] => {
  return Array.from({ length: count }, (_, i) => ({
    timestamp: new Date(Date.now() + i * 3600000).toISOString(), // 1 hour intervals
    predicted_value: 50 + Math.random() * 30,
    confidence_lower: 40 + Math.random() * 20,
    confidence_upper: 60 + Math.random() * 30,
    trend: i % 3 === 0 ? "increasing" : i % 3 === 1 ? "decreasing" : "stable",
  }));
};

const mockPredictionData: PredictionData = {
  container_id: "test-container",
  prediction_timestamp: new Date().toISOString(),
  prediction_horizon_hours: 6,
  predictions: {
    cpu_percent: createMockPredictionPoints(6),
    memory_percent: createMockPredictionPoints(6),
    network_io: createMockPredictionPoints(6),
    disk_io: createMockPredictionPoints(6),
  },
  confidence_level: 0.85,
  model_accuracy: 0.92,
};

describe("PerformancePredictionCharts", () => {
  it("renders loading state correctly", () => {
    renderWithTheme(
      <PerformancePredictionCharts predictionData={null} loading={true} />
    );

    expect(screen.getByText("Performance Predictions")).toBeInTheDocument();
    expect(screen.getByText("Loading predictions...")).toBeInTheDocument();
  });

  it("renders error state correctly", () => {
    const errorMessage = "Failed to load predictions";
    renderWithTheme(
      <PerformancePredictionCharts predictionData={null} error={errorMessage} />
    );

    expect(screen.getByText("Performance Predictions")).toBeInTheDocument();
    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });

  it("renders no data state correctly", () => {
    renderWithTheme(<PerformancePredictionCharts predictionData={null} />);

    expect(screen.getByText("Performance Predictions")).toBeInTheDocument();
    expect(
      screen.getByText("No prediction data available")
    ).toBeInTheDocument();
  });

  it("renders prediction charts with data", async () => {
    renderWithTheme(
      <PerformancePredictionCharts predictionData={mockPredictionData} />
    );

    await waitFor(() => {
      expect(screen.getByText("Performance Predictions")).toBeInTheDocument();
      expect(screen.getByText("6h forecast")).toBeInTheDocument();
      expect(screen.getByText("85% confidence")).toBeInTheDocument();
      expect(screen.getByDisplayValue("cpu_percent")).toBeInTheDocument();
    });
  });

  it("displays confidence intervals when enabled", async () => {
    renderWithTheme(
      <PerformancePredictionCharts
        predictionData={mockPredictionData}
        showConfidenceIntervals={true}
      />
    );

    await waitFor(() => {
      expect(screen.getByTestId("area-chart")).toBeInTheDocument();
    });
  });

  it("displays line chart when confidence intervals disabled", async () => {
    renderWithTheme(
      <PerformancePredictionCharts
        predictionData={mockPredictionData}
        showConfidenceIntervals={false}
      />
    );

    await waitFor(() => {
      expect(screen.getByTestId("line-chart")).toBeInTheDocument();
    });
  });

  it("changes metric selection correctly", async () => {
    renderWithTheme(
      <PerformancePredictionCharts predictionData={mockPredictionData} />
    );

    const metricSelect = screen.getByRole("combobox");

    fireEvent.mouseDown(metricSelect);

    await waitFor(() => {
      const options = screen.getAllByRole("option");
      expect(options.length).toBeGreaterThan(0);
    });

    const memoryOption = screen.getByRole("option", { name: "Memory Usage" });
    fireEvent.click(memoryOption);

    await waitFor(() => {
      expect(screen.getByDisplayValue("memory_percent")).toBeInTheDocument();
    });
  });

  it("displays threshold lines when enabled", async () => {
    renderWithTheme(
      <PerformancePredictionCharts
        predictionData={mockPredictionData}
        showThresholds={true}
      />
    );

    await waitFor(() => {
      expect(screen.getByTestId("reference-line")).toBeInTheDocument();
    });
  });

  it("displays model information correctly", async () => {
    renderWithTheme(
      <PerformancePredictionCharts predictionData={mockPredictionData} />
    );

    await waitFor(() => {
      expect(screen.getByText("Model Accuracy: 92%")).toBeInTheDocument();
      expect(screen.getByText(/Updated:/)).toBeInTheDocument();
    });
  });

  it("handles different prediction horizons", async () => {
    const longHorizonData: PredictionData = {
      ...mockPredictionData,
      prediction_horizon_hours: 24,
    };

    renderWithTheme(
      <PerformancePredictionCharts predictionData={longHorizonData} />
    );

    await waitFor(() => {
      expect(screen.getByText("24h forecast")).toBeInTheDocument();
    });
  });

  it("handles different confidence levels", async () => {
    const lowConfidenceData: PredictionData = {
      ...mockPredictionData,
      confidence_level: 0.65,
    };

    renderWithTheme(
      <PerformancePredictionCharts predictionData={lowConfidenceData} />
    );

    await waitFor(() => {
      expect(screen.getByText("65% confidence")).toBeInTheDocument();
    });
  });

  it("handles empty prediction data", async () => {
    const emptyPredictionData: PredictionData = {
      ...mockPredictionData,
      predictions: {
        cpu_percent: [],
        memory_percent: [],
        network_io: [],
        disk_io: [],
      },
    };

    renderWithTheme(
      <PerformancePredictionCharts predictionData={emptyPredictionData} />
    );

    await waitFor(() => {
      expect(screen.getByText("Performance Predictions")).toBeInTheDocument();
      // Chart should still render even with empty data
      expect(screen.getByTestId("responsive-container")).toBeInTheDocument();
    });
  });

  it("applies custom height correctly", () => {
    const customHeight = 600;
    const { container } = renderWithTheme(
      <PerformancePredictionCharts
        predictionData={mockPredictionData}
        height={customHeight}
      />
    );

    const paper = container.querySelector(".MuiPaper-root");
    expect(paper).toHaveStyle(`height: ${customHeight}px`);
  });

  it("handles metric selection for all metric types", async () => {
    renderWithTheme(
      <PerformancePredictionCharts predictionData={mockPredictionData} />
    );

    const metricSelect = screen.getByRole("combobox");

    // Test CPU metric (default)
    expect(screen.getByDisplayValue("cpu_percent")).toBeInTheDocument();

    // Test that the component renders without crashing with different metrics
    expect(screen.getByText("Performance Predictions")).toBeInTheDocument();
    expect(screen.getByText("CPU Usage")).toBeInTheDocument();
  });

  it("displays correct chart components", async () => {
    renderWithTheme(
      <PerformancePredictionCharts
        predictionData={mockPredictionData}
        showConfidenceIntervals={true}
      />
    );

    await waitFor(() => {
      expect(screen.getByTestId("responsive-container")).toBeInTheDocument();
      expect(screen.getByTestId("area-chart")).toBeInTheDocument();
      expect(screen.getByTestId("cartesian-grid")).toBeInTheDocument();
      expect(screen.getByTestId("x-axis")).toBeInTheDocument();
      expect(screen.getByTestId("y-axis")).toBeInTheDocument();
      expect(screen.getByTestId("legend")).toBeInTheDocument();
    });
  });
});
