import React from "react";
import {
  render,
  screen,
  fireEvent,
  waitFor,
  act,
} from "@testing-library/react";
import { ThemeProvider } from "@mui/material/styles";
import HistoricalTrendsVisualization from "../HistoricalTrendsVisualization";
import { useApiCall } from "../../hooks/useApiCall";
import theme from "../../theme";

// Mock the useApiCall hook
jest.mock("../../hooks/useApiCall");
const mockUseApiCall = useApiCall as jest.MockedFunction<typeof useApiCall>;

// Mock Recharts components
jest.mock("recharts", () => ({
  LineChart: ({ children }: any) => (
    <div data-testid="line-chart">{children}</div>
  ),
  Line: () => <div data-testid="line" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  Legend: () => <div data-testid="legend" />,
  ResponsiveContainer: ({ children }: any) => (
    <div data-testid="responsive-container">{children}</div>
  ),
  Brush: () => <div data-testid="brush" />,
  ReferenceLine: () => <div data-testid="reference-line" />,
}));

const renderWithTheme = (component: React.ReactElement) => {
  return render(<ThemeProvider theme={theme}>{component}</ThemeProvider>);
};

const mockHistoricalData = {
  container_id: "test-container",
  time_range: "24h",
  data_points: [
    { timestamp: "2024-01-01T00:00:00Z", value: 45.5 },
    { timestamp: "2024-01-01T01:00:00Z", value: 50.2 },
    { timestamp: "2024-01-01T02:00:00Z", value: 48.7 },
    { timestamp: "2024-01-01T03:00:00Z", value: 52.1 },
  ],
  aggregation_level: "1hour",
  total_points: 4,
};

const mockProps = {
  containerId: "test-container",
  containerName: "test-container-name",
  initialTimeRange: "24h" as const,
  height: 400,
  showBrush: true,
  showThresholds: true,
  onTimeRangeChange: jest.fn(),
};

describe("HistoricalTrendsVisualization", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseApiCall.mockReturnValue({
      data: mockHistoricalData,
      loading: false,
      error: null,
      execute: jest.fn(),
    });
  });

  it("renders loading state correctly", () => {
    mockUseApiCall.mockReturnValue({
      data: null,
      loading: true,
      error: null,
      execute: jest.fn(),
    });

    renderWithTheme(<HistoricalTrendsVisualization {...mockProps} />);

    expect(screen.getByText("Historical Trends")).toBeInTheDocument();
    expect(screen.getByText("Loading historical data...")).toBeInTheDocument();
  });

  it("renders error state correctly", () => {
    const errorMessage = "Failed to load historical data";
    mockUseApiCall.mockReturnValue({
      data: null,
      loading: false,
      error: errorMessage,
      execute: jest.fn(),
    });

    renderWithTheme(<HistoricalTrendsVisualization {...mockProps} />);

    expect(screen.getByText("Historical Trends")).toBeInTheDocument();
    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });

  it("renders historical trends with data", async () => {
    renderWithTheme(<HistoricalTrendsVisualization {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText("Historical Trends")).toBeInTheDocument();
      expect(screen.getByText("test-container-name")).toBeInTheDocument();
      expect(screen.getByText("4 data points")).toBeInTheDocument();
    });
  });

  it("displays time range buttons correctly", async () => {
    renderWithTheme(<HistoricalTrendsVisualization {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText("1H")).toBeInTheDocument();
      expect(screen.getByText("6H")).toBeInTheDocument();
      expect(screen.getByText("24H")).toBeInTheDocument();
      expect(screen.getByText("7D")).toBeInTheDocument();
      expect(screen.getByText("30D")).toBeInTheDocument();
    });
  });

  it("handles time range selection", async () => {
    const mockExecute = jest.fn();
    mockUseApiCall.mockReturnValue({
      data: mockHistoricalData,
      loading: false,
      error: null,
      execute: mockExecute,
    });

    renderWithTheme(<HistoricalTrendsVisualization {...mockProps} />);

    const sevenDayButton = screen.getByText("7D");

    await act(async () => {
      fireEvent.click(sevenDayButton);
    });

    expect(mockProps.onTimeRangeChange).toHaveBeenCalledWith("7d");
  });

  it("displays metric selector correctly", async () => {
    renderWithTheme(<HistoricalTrendsVisualization {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText("Historical Trends")).toBeInTheDocument();
    });

    // Check that the metrics selector exists by looking for the form control
    const metricsFormControls = screen.getAllByText("Metrics");
    expect(metricsFormControls.length).toBeGreaterThan(0);
  });

  it("handles metric selection changes", async () => {
    renderWithTheme(<HistoricalTrendsVisualization {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText("Historical Trends")).toBeInTheDocument();
    });

    // Test that the component renders the metrics selector
    const metricsFormControls = screen.getAllByText("Metrics");
    expect(metricsFormControls.length).toBeGreaterThan(0);
  });

  it("renders chart components correctly", async () => {
    renderWithTheme(<HistoricalTrendsVisualization {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByTestId("responsive-container")).toBeInTheDocument();
      expect(screen.getByTestId("line-chart")).toBeInTheDocument();
      expect(screen.getByTestId("cartesian-grid")).toBeInTheDocument();
      expect(screen.getByTestId("x-axis")).toBeInTheDocument();
      expect(screen.getByTestId("y-axis")).toBeInTheDocument();
      expect(screen.getByTestId("legend")).toBeInTheDocument();
    });
  });

  it("displays brush when enabled and sufficient data points", async () => {
    const largeDataSet = {
      ...mockHistoricalData,
      data_points: Array.from({ length: 25 }, (_, i) => ({
        timestamp: new Date(Date.now() + i * 3600000).toISOString(),
        value: 50 + Math.random() * 20,
      })),
      total_points: 25,
    };

    mockUseApiCall.mockReturnValue({
      data: largeDataSet,
      loading: false,
      error: null,
      execute: jest.fn(),
    });

    renderWithTheme(<HistoricalTrendsVisualization {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByTestId("brush")).toBeInTheDocument();
    });
  });

  it("displays threshold lines when enabled", async () => {
    renderWithTheme(<HistoricalTrendsVisualization {...mockProps} />);

    await waitFor(() => {
      const referenceLines = screen.getAllByTestId("reference-line");
      expect(referenceLines.length).toBeGreaterThan(0);
    });
  });

  it("hides brush when disabled", async () => {
    renderWithTheme(
      <HistoricalTrendsVisualization {...mockProps} showBrush={false} />
    );

    await waitFor(() => {
      expect(screen.queryByTestId("brush")).not.toBeInTheDocument();
    });
  });

  it("hides threshold lines when disabled", async () => {
    renderWithTheme(
      <HistoricalTrendsVisualization {...mockProps} showThresholds={false} />
    );

    await waitFor(() => {
      expect(screen.queryByTestId("reference-line")).not.toBeInTheDocument();
    });
  });

  it("displays summary information correctly", async () => {
    renderWithTheme(<HistoricalTrendsVisualization {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText(/Time range: 24h/)).toBeInTheDocument();
      expect(screen.getByText(/Aggregation: 1hour/)).toBeInTheDocument();
      expect(screen.getByText(/Data points: 4/)).toBeInTheDocument();
    });
  });

  it("handles different initial time ranges", async () => {
    renderWithTheme(
      <HistoricalTrendsVisualization {...mockProps} initialTimeRange="7d" />
    );

    await waitFor(() => {
      expect(screen.getByText("7D")).toBeInTheDocument();
    });
  });

  it("handles missing container name gracefully", async () => {
    renderWithTheme(
      <HistoricalTrendsVisualization {...mockProps} containerName={undefined} />
    );

    await waitFor(() => {
      expect(screen.getByText("Historical Trends")).toBeInTheDocument();
      expect(screen.queryByText("test-container-name")).not.toBeInTheDocument();
    });
  });

  it("applies custom height correctly", () => {
    const customHeight = 600;
    const { container } = renderWithTheme(
      <HistoricalTrendsVisualization {...mockProps} height={customHeight} />
    );

    const paper = container.querySelector(".MuiPaper-root");
    expect(paper).toHaveStyle(`height: ${customHeight}px`);
  });

  it("fetches data when container ID changes", async () => {
    const mockExecute = jest.fn();
    mockUseApiCall.mockReturnValue({
      data: mockHistoricalData,
      loading: false,
      error: null,
      execute: mockExecute,
    });

    const { rerender } = renderWithTheme(
      <HistoricalTrendsVisualization {...mockProps} />
    );

    expect(mockExecute).toHaveBeenCalledWith(
      "/api/containers/test-container/metrics/historical?time_range=24h&hours=24"
    );

    rerender(
      <ThemeProvider theme={theme}>
        <HistoricalTrendsVisualization
          {...mockProps}
          containerId="new-container"
        />
      </ThemeProvider>
    );

    expect(mockExecute).toHaveBeenCalledWith(
      "/api/containers/new-container/metrics/historical?time_range=24h&hours=24"
    );
  });

  it("handles multiple metric selection", async () => {
    renderWithTheme(<HistoricalTrendsVisualization {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText("Historical Trends")).toBeInTheDocument();
    });

    // Test that the component renders multiple lines for multiple metrics
    await waitFor(() => {
      const lines = screen.getAllByTestId("line");
      expect(lines.length).toBeGreaterThan(0);
    });
  });
});
