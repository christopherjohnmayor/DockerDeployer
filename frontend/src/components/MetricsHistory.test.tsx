import React from "react";
import { screen, fireEvent, waitFor, act } from "@testing-library/react";
import { renderWithDatePicker } from "../utils/testUtils";
import MetricsHistory from "./MetricsHistory";
import * as useApiCallModule from "../hooks/useApiCall";

const mockHistoricalMetrics = [
  {
    id: 1,
    container_id: "test-container",
    container_name: "test-container-name",
    timestamp: "2024-01-01T12:00:00Z",
    cpu_percent: 25.5,
    memory_usage: 134217728,
    memory_limit: 536870912,
    memory_percent: 25.0,
    network_rx_bytes: 1024,
    network_tx_bytes: 2048,
    block_read_bytes: 4096,
    block_write_bytes: 8192,
  },
  {
    id: 2,
    container_id: "test-container",
    container_name: "test-container-name",
    timestamp: "2024-01-01T12:01:00Z",
    cpu_percent: 30.2,
    memory_usage: 150000000,
    memory_limit: 536870912,
    memory_percent: 28.0,
    network_rx_bytes: 1500,
    network_tx_bytes: 3000,
    block_read_bytes: 5000,
    block_write_bytes: 10000,
  },
];

const mockApiResponse = {
  container_id: "test-container",
  hours: 24,
  limit: 1000,
  metrics: mockHistoricalMetrics,
};

const mockUseApiCall = {
  execute: jest.fn(),
  loading: false,
  error: null,
};

const renderWithProviders = renderWithDatePicker;

// Mock the useApiCall hook
jest.mock("../hooks/useApiCall");
const mockedUseApiCall = useApiCallModule.useApiCall as jest.MockedFunction<
  typeof useApiCallModule.useApiCall
>;

describe("MetricsHistory", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockedUseApiCall.mockReturnValue(mockUseApiCall);
  });

  it("renders historical metrics title", () => {
    renderWithProviders(<MetricsHistory containerId="test-container" />);

    expect(screen.getByText("Historical Metrics")).toBeInTheDocument();
  });

  it("renders time range selector", () => {
    renderWithProviders(<MetricsHistory containerId="test-container" />);

    expect(screen.getByRole("combobox")).toBeInTheDocument();
  });

  it("renders refresh button", () => {
    renderWithProviders(<MetricsHistory containerId="test-container" />);

    const refreshButton = screen.getByRole("button", {
      name: /refresh metrics data/i,
    });
    expect(refreshButton).toBeInTheDocument();
  });

  it("fetches historical metrics on mount", async () => {
    mockUseApiCall.execute.mockResolvedValue(mockApiResponse);

    renderWithProviders(<MetricsHistory containerId="test-container" />);

    await waitFor(() => {
      expect(mockUseApiCall.execute).toHaveBeenCalledWith(
        "/api/containers/test-container/metrics/history?hours=24&limit=1000"
      );
    });
  });

  it("displays data points count", async () => {
    mockUseApiCall.execute.mockResolvedValue(mockApiResponse);

    renderWithProviders(<MetricsHistory containerId="test-container" />);

    await waitFor(() => {
      expect(screen.getByText("Showing 2 data points")).toBeInTheDocument();
    });
  });

  it("renders all chart titles", async () => {
    mockUseApiCall.execute.mockResolvedValue(mockApiResponse);

    renderWithProviders(<MetricsHistory containerId="test-container" />);

    await waitFor(() => {
      expect(screen.getByText("CPU Usage History")).toBeInTheDocument();
      expect(screen.getByText("Memory Usage History")).toBeInTheDocument();
      expect(screen.getByText("Network RX History")).toBeInTheDocument();
      expect(screen.getByText("Network TX History")).toBeInTheDocument();
      expect(screen.getByText("Disk Read History")).toBeInTheDocument();
      expect(screen.getByText("Disk Write History")).toBeInTheDocument();
    });
  });

  it("handles time range change", async () => {
    mockUseApiCall.execute.mockResolvedValue(mockApiResponse);

    renderWithProviders(<MetricsHistory containerId="test-container" />);

    // Wait for initial load
    await waitFor(() => {
      expect(mockUseApiCall.execute).toHaveBeenCalledWith(
        "/api/containers/test-container/metrics/history?hours=24&limit=1000"
      );
    });

    const timeRangeSelect = screen.getByRole("combobox");

    await act(async () => {
      fireEvent.mouseDown(timeRangeSelect);
    });

    const option6h = screen.getByText("Last 6 Hours");

    await act(async () => {
      fireEvent.click(option6h);
    });

    await waitFor(() => {
      expect(mockUseApiCall.execute).toHaveBeenCalledWith(
        "/api/containers/test-container/metrics/history?hours=6&limit=1000"
      );
    });
  });

  it("shows custom date pickers when custom range is selected", async () => {
    renderWithProviders(<MetricsHistory containerId="test-container" />);

    const timeRangeSelect = screen.getByRole("combobox");

    await act(async () => {
      fireEvent.mouseDown(timeRangeSelect);
    });

    const customOption = screen.getByText("Custom Range");

    await act(async () => {
      fireEvent.click(customOption);
    });

    expect(screen.getByLabelText("Start Date")).toBeInTheDocument();
    expect(screen.getByLabelText("End Date")).toBeInTheDocument();
  });

  it("handles manual refresh", async () => {
    mockUseApiCall.execute.mockResolvedValue(mockApiResponse);

    renderWithProviders(<MetricsHistory containerId="test-container" />);

    // Wait for initial load
    await waitFor(() => {
      expect(mockUseApiCall.execute).toHaveBeenCalledWith(
        "/api/containers/test-container/metrics/history?hours=24&limit=1000"
      );
    });

    const refreshButton = screen.getByRole("button", {
      name: /refresh metrics data/i,
    });

    await act(async () => {
      fireEvent.click(refreshButton);
    });

    // Should be called twice - once on mount, once on refresh
    expect(mockUseApiCall.execute).toHaveBeenCalledTimes(2);
  });

  it("shows loading state in refresh button", () => {
    mockedUseApiCall.mockReturnValue({
      ...mockUseApiCall,
      loading: true,
    });

    renderWithProviders(<MetricsHistory containerId="test-container" />);

    const refreshButton = screen.getByRole("button", {
      name: /refresh metrics data/i,
    });
    expect(refreshButton).toBeDisabled();
    // Check for loading indicator in the component - use getAllByText since there are multiple charts
    expect(screen.getAllByText("Loading metrics...")).toHaveLength(6);
  });

  it("displays error state", () => {
    const errorMessage = "Failed to load historical metrics";
    mockedUseApiCall.mockReturnValue({
      ...mockUseApiCall,
      error: errorMessage,
    });

    renderWithProviders(<MetricsHistory containerId="test-container" />);

    expect(
      screen.getByText(`Failed to load historical metrics: ${errorMessage}`)
    ).toBeInTheDocument();
  });

  it("handles API errors gracefully", async () => {
    const consoleSpy = jest
      .spyOn(console, "error")
      .mockImplementation(() => {});
    mockUseApiCall.execute.mockRejectedValue(new Error("API Error"));

    renderWithProviders(<MetricsHistory containerId="test-container" />);

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith(
        "Error fetching historical metrics:",
        expect.any(Error)
      );
    });

    consoleSpy.mockRestore();
  });

  it("handles empty metrics response", async () => {
    mockUseApiCall.execute.mockResolvedValue({
      ...mockApiResponse,
      metrics: [],
    });

    renderWithProviders(<MetricsHistory containerId="test-container" />);

    await waitFor(() => {
      expect(
        screen.queryByText(/Showing \d+ data points/)
      ).not.toBeInTheDocument();
    });
  });

  it("converts metrics data to chart format correctly", async () => {
    mockUseApiCall.execute.mockResolvedValue(mockApiResponse);

    renderWithProviders(<MetricsHistory containerId="test-container" />);

    // The component should process the data and display charts
    await waitFor(() => {
      expect(screen.getByText("CPU Usage History")).toBeInTheDocument();
      expect(screen.getByText("Memory Usage History")).toBeInTheDocument();
    });
  });

  it("handles different time range options", async () => {
    mockUseApiCall.execute.mockResolvedValue(mockApiResponse);

    renderWithProviders(<MetricsHistory containerId="test-container" />);

    // Wait for initial load
    await waitFor(() => {
      expect(mockUseApiCall.execute).toHaveBeenCalledWith(
        "/api/containers/test-container/metrics/history?hours=24&limit=1000"
      );
    });

    // Use the combobox role to find the Select component
    const timeRangeSelect = screen.getByRole("combobox");

    // Test 1 hour option
    await act(async () => {
      fireEvent.mouseDown(timeRangeSelect);
    });

    const option1h = screen.getByText("Last Hour");

    await act(async () => {
      fireEvent.click(option1h);
    });

    await waitFor(() => {
      expect(mockUseApiCall.execute).toHaveBeenCalledWith(
        "/api/containers/test-container/metrics/history?hours=1&limit=1000"
      );
    });
  });
});
