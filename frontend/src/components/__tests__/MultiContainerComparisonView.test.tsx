import React from "react";
import {
  render,
  screen,
  fireEvent,
  waitFor,
  act,
} from "@testing-library/react";
import { ThemeProvider } from "@mui/material/styles";
import MultiContainerComparisonView from "../MultiContainerComparisonView";
import { useApiCall } from "../../hooks/useApiCall";
import theme from "../../theme";

// Mock the useApiCall hook
jest.mock("../../hooks/useApiCall");
const mockUseApiCall = useApiCall as jest.MockedFunction<typeof useApiCall>;

// Mock Recharts components
jest.mock("recharts", () => ({
  BarChart: ({ children }: any) => (
    <div data-testid="bar-chart">{children}</div>
  ),
  Bar: () => <div data-testid="bar" />,
  RadarChart: ({ children }: any) => (
    <div data-testid="radar-chart">{children}</div>
  ),
  Radar: () => <div data-testid="radar" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  Legend: () => <div data-testid="legend" />,
  ResponsiveContainer: ({ children }: any) => (
    <div data-testid="responsive-container">{children}</div>
  ),
  PolarGrid: () => <div data-testid="polar-grid" />,
  PolarAngleAxis: () => <div data-testid="polar-angle-axis" />,
  PolarRadiusAxis: () => <div data-testid="polar-radius-axis" />,
}));

const renderWithTheme = (component: React.ReactElement) => {
  return render(<ThemeProvider theme={theme}>{component}</ThemeProvider>);
};

const mockContainers = [
  { id: "container1", name: "web-server" },
  { id: "container2", name: "database" },
  { id: "container3", name: "cache" },
];

const mockComparisonData = {
  containers: ["container1", "container2"],
  comparison_timestamp: new Date().toISOString(),
  metrics_comparison: {
    container1: {
      container_name: "web-server",
      current_metrics: {
        container_id: "container1",
        container_name: "web-server",
        cpu_percent: 45.5,
        memory_percent: 62.3,
        memory_usage: 1073741824,
        memory_limit: 2147483648,
        network_rx_bytes: 1048576,
        network_tx_bytes: 2097152,
        block_read_bytes: 524288,
        block_write_bytes: 1048576,
        status: "running",
        timestamp: new Date().toISOString(),
      },
      health_score: 85,
      performance_rank: 1,
    },
    container2: {
      container_name: "database",
      current_metrics: {
        container_id: "container2",
        container_name: "database",
        cpu_percent: 65.2,
        memory_percent: 78.1,
        memory_usage: 1610612736,
        memory_limit: 2147483648,
        network_rx_bytes: 2097152,
        network_tx_bytes: 1048576,
        block_read_bytes: 1048576,
        block_write_bytes: 2097152,
        status: "running",
        timestamp: new Date().toISOString(),
      },
      health_score: 72,
      performance_rank: 2,
    },
  },
  aggregated_stats: {
    avg_cpu_percent: 55.35,
    avg_memory_percent: 70.2,
    total_network_io: 6291456,
    total_disk_io: 4718592,
  },
};

const mockProps = {
  selectedContainers: ["container1", "container2"],
  onContainerSelectionChange: jest.fn(),
  height: 500,
  showRanking: true,
  showRadarChart: true,
};

describe("MultiContainerComparisonView", () => {
  beforeEach(() => {
    jest.clearAllMocks();

    // Default mock implementation
    mockUseApiCall.mockReturnValue({
      data: null,
      loading: false,
      error: null,
      execute: jest.fn(),
    });
  });

  it("renders container comparison view correctly", async () => {
    mockUseApiCall
      .mockReturnValueOnce({
        data: mockContainers,
        loading: false,
        error: null,
        execute: jest.fn(),
      })
      .mockReturnValueOnce({
        data: mockComparisonData,
        loading: false,
        error: null,
        execute: jest.fn(),
      });

    renderWithTheme(<MultiContainerComparisonView {...mockProps} />);

    await waitFor(
      () => {
        expect(screen.getByText("Container Comparison")).toBeInTheDocument();
        expect(screen.getByText("2 containers")).toBeInTheDocument();
      },
      { timeout: 20000 }
    );
  });

  it("shows info message when less than 2 containers selected", () => {
    mockUseApiCall
      .mockReturnValueOnce({
        data: mockContainers,
        loading: false,
        error: null,
        execute: jest.fn(),
      })
      .mockReturnValueOnce({
        data: mockComparisonData,
        loading: false,
        error: null,
        execute: jest.fn(),
      });

    renderWithTheme(
      <MultiContainerComparisonView
        {...mockProps}
        selectedContainers={["container1"]}
      />
    );

    expect(
      screen.getByText(
        "Select at least 2 containers to compare their performance metrics."
      )
    ).toBeInTheDocument();
  });

  it("renders error state correctly", () => {
    // Reset all mocks first
    jest.clearAllMocks();

    // Mock implementation that returns different values for each call
    let callCount = 0;
    mockUseApiCall.mockImplementation(() => {
      callCount++;
      if (callCount === 1) {
        // First call - containers
        return {
          data: mockContainers,
          loading: false,
          error: null,
          execute: jest.fn(),
        };
      } else {
        // Second call - comparison data with error
        return {
          data: null,
          loading: false,
          error: "Failed to load comparison data",
          execute: jest.fn(),
        };
      }
    });

    renderWithTheme(<MultiContainerComparisonView {...mockProps} />);

    expect(
      screen.getByText("Failed to load comparison data")
    ).toBeInTheDocument();
  });

  it("renders loading state correctly", () => {
    // Reset all mocks first
    jest.clearAllMocks();

    // Mock implementation that returns different values for each call
    let callCount = 0;
    mockUseApiCall.mockImplementation(() => {
      callCount++;
      if (callCount === 1) {
        // First call - containers
        return {
          data: mockContainers,
          loading: false,
          error: null,
          execute: jest.fn(),
        };
      } else {
        // Second call - comparison data with loading
        return {
          data: null,
          loading: true,
          error: null,
          execute: jest.fn(),
        };
      }
    });

    renderWithTheme(<MultiContainerComparisonView {...mockProps} />);

    expect(screen.getByText("Loading comparison data...")).toBeInTheDocument();
  });

  it("displays container selector correctly", async () => {
    mockUseApiCall
      .mockReturnValueOnce({
        data: mockContainers,
        loading: false,
        error: null,
        execute: jest.fn(),
      })
      .mockReturnValueOnce({
        data: mockComparisonData,
        loading: false,
        error: null,
        execute: jest.fn(),
      });

    renderWithTheme(<MultiContainerComparisonView {...mockProps} />);

    await waitFor(
      () => {
        // Check for container selector using role
        const containerSelector = screen.getAllByRole("combobox")[0]; // First combobox is containers
        expect(containerSelector).toBeInTheDocument();

        // Check for selected container chips in the display
        expect(screen.getByText("web-server")).toBeInTheDocument();
        expect(screen.getByText("database")).toBeInTheDocument();
      },
      { timeout: 20000 }
    );
  });

  it("displays metric selector correctly", async () => {
    mockUseApiCall
      .mockReturnValueOnce({
        data: mockContainers,
        loading: false,
        error: null,
        execute: jest.fn(),
      })
      .mockReturnValueOnce({
        data: mockComparisonData,
        loading: false,
        error: null,
        execute: jest.fn(),
      });

    renderWithTheme(<MultiContainerComparisonView {...mockProps} />);

    await waitFor(
      () => {
        // Check for metric selector using role (second combobox)
        const metricSelector = screen.getAllByRole("combobox")[1]; // Second combobox is metrics
        expect(metricSelector).toBeInTheDocument();

        // Check that CPU Usage is selected by default
        expect(screen.getByText("CPU Usage")).toBeInTheDocument();
      },
      { timeout: 20000 }
    );
  });

  it("handles container selection changes", async () => {
    mockUseApiCall
      .mockReturnValueOnce({
        data: mockContainers,
        loading: false,
        error: null,
        execute: jest.fn(),
      })
      .mockReturnValueOnce({
        data: mockComparisonData,
        loading: false,
        error: null,
        execute: jest.fn(),
      });

    renderWithTheme(<MultiContainerComparisonView {...mockProps} />);

    await waitFor(
      () => {
        const containerSelector = screen.getAllByRole("combobox")[0];
        expect(containerSelector).toBeInTheDocument();
      },
      { timeout: 20000 }
    );

    const containerSelector = screen.getAllByRole("combobox")[0];

    await act(async () => {
      fireEvent.mouseDown(containerSelector);
    });

    await waitFor(
      () => {
        expect(screen.getByText("cache")).toBeInTheDocument();
      },
      { timeout: 20000 }
    );

    await act(async () => {
      fireEvent.click(screen.getByText("cache"));
    });

    expect(mockProps.onContainerSelectionChange).toHaveBeenCalled();
  });

  it("handles metric selection changes", async () => {
    mockUseApiCall
      .mockReturnValueOnce({
        data: mockContainers,
        loading: false,
        error: null,
        execute: jest.fn(),
      })
      .mockReturnValueOnce({
        data: mockComparisonData,
        loading: false,
        error: null,
        execute: jest.fn(),
      });

    renderWithTheme(<MultiContainerComparisonView {...mockProps} />);

    await waitFor(
      () => {
        const metricSelector = screen.getAllByRole("combobox")[1];
        expect(metricSelector).toBeInTheDocument();
      },
      { timeout: 20000 }
    );

    const metricSelector = screen.getAllByRole("combobox")[1];

    await act(async () => {
      fireEvent.mouseDown(metricSelector);
    });

    await waitFor(
      () => {
        expect(screen.getByText("Memory Usage")).toBeInTheDocument();
      },
      { timeout: 20000 }
    );

    await act(async () => {
      fireEvent.click(screen.getByText("Memory Usage"));
    });

    // Should update the chart to show memory usage
    await waitFor(
      () => {
        expect(screen.getByText("Memory Usage Comparison")).toBeInTheDocument();
      },
      { timeout: 20000 }
    );
  });

  it("renders bar chart correctly", async () => {
    // Reset all mocks first
    jest.clearAllMocks();

    // Mock implementation that returns different values for each call
    let callCount = 0;
    mockUseApiCall.mockImplementation(() => {
      callCount++;
      if (callCount === 1) {
        // First call - containers
        return {
          data: mockContainers,
          loading: false,
          error: null,
          execute: jest.fn(),
        };
      } else {
        // Second call - comparison data
        return {
          data: mockComparisonData,
          loading: false,
          error: null,
          execute: jest.fn(),
        };
      }
    });

    renderWithTheme(<MultiContainerComparisonView {...mockProps} />);

    await waitFor(
      () => {
        // Use getAllByTestId to handle multiple responsive containers (bar chart and radar chart)
        const responsiveContainers = screen.getAllByTestId(
          "responsive-container"
        );
        expect(responsiveContainers[0]).toBeInTheDocument();
        expect(screen.getByTestId("bar-chart")).toBeInTheDocument();
        expect(screen.getByTestId("cartesian-grid")).toBeInTheDocument();
        expect(screen.getByTestId("x-axis")).toBeInTheDocument();
        expect(screen.getByTestId("y-axis")).toBeInTheDocument();
      },
      { timeout: 20000 }
    );
  }, 30000);

  it("renders radar chart when enabled", async () => {
    mockUseApiCall
      .mockReturnValueOnce({
        data: mockContainers,
        loading: false,
        error: null,
        execute: jest.fn(),
      })
      .mockReturnValueOnce({
        data: mockComparisonData,
        loading: false,
        error: null,
        execute: jest.fn(),
      });

    renderWithTheme(<MultiContainerComparisonView {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByTestId("radar-chart")).toBeInTheDocument();
      expect(screen.getByTestId("polar-grid")).toBeInTheDocument();
      expect(screen.getByTestId("polar-angle-axis")).toBeInTheDocument();
      expect(screen.getByTestId("polar-radius-axis")).toBeInTheDocument();
    });
  });

  it("hides radar chart when disabled", async () => {
    mockUseApiCall
      .mockReturnValueOnce({
        data: mockContainers,
        loading: false,
        error: null,
        execute: jest.fn(),
      })
      .mockReturnValueOnce({
        data: mockComparisonData,
        loading: false,
        error: null,
        execute: jest.fn(),
      });

    renderWithTheme(
      <MultiContainerComparisonView {...mockProps} showRadarChart={false} />
    );

    await waitFor(() => {
      expect(screen.queryByTestId("radar-chart")).not.toBeInTheDocument();
    });
  });

  it("displays performance ranking table when enabled", async () => {
    // Reset all mocks first
    jest.clearAllMocks();

    // Mock implementation that returns different values for each call
    let callCount = 0;
    mockUseApiCall.mockImplementation(() => {
      callCount++;
      if (callCount === 1) {
        // First call - containers
        return {
          data: mockContainers,
          loading: false,
          error: null,
          execute: jest.fn(),
        };
      } else {
        // Second call - comparison data
        return {
          data: mockComparisonData,
          loading: false,
          error: null,
          execute: jest.fn(),
        };
      }
    });

    renderWithTheme(<MultiContainerComparisonView {...mockProps} />);

    await waitFor(
      () => {
        expect(screen.getByText("Performance Ranking")).toBeInTheDocument();
        expect(screen.getByText("Rank")).toBeInTheDocument();
        expect(screen.getByText("Container")).toBeInTheDocument();
        expect(screen.getByText("CPU %")).toBeInTheDocument();
        expect(screen.getByText("Memory %")).toBeInTheDocument();
        expect(screen.getByText("Health Score")).toBeInTheDocument();
      },
      { timeout: 20000 }
    );
  }, 30000);

  it("displays container data in ranking table", async () => {
    // Reset all mocks first
    jest.clearAllMocks();

    // Mock implementation that returns different values for each call
    let callCount = 0;
    mockUseApiCall.mockImplementation(() => {
      callCount++;
      if (callCount === 1) {
        // First call - containers
        return {
          data: mockContainers,
          loading: false,
          error: null,
          execute: jest.fn(),
        };
      } else {
        // Second call - comparison data
        return {
          data: mockComparisonData,
          loading: false,
          error: null,
          execute: jest.fn(),
        };
      }
    });

    renderWithTheme(<MultiContainerComparisonView {...mockProps} />);

    await waitFor(
      () => {
        expect(screen.getByText("web-server")).toBeInTheDocument();
        expect(screen.getByText("database")).toBeInTheDocument();
        expect(screen.getByText("45.5%")).toBeInTheDocument();
        expect(screen.getByText("62.3%")).toBeInTheDocument();
        expect(screen.getByText("85.0")).toBeInTheDocument();
        expect(screen.getByText("72.0")).toBeInTheDocument();
      },
      { timeout: 20000 }
    );
  }, 30000);

  it("hides ranking table when disabled", async () => {
    mockUseApiCall
      .mockReturnValueOnce({
        data: mockContainers,
        loading: false,
        error: null,
        execute: jest.fn(),
      })
      .mockReturnValueOnce({
        data: mockComparisonData,
        loading: false,
        error: null,
        execute: jest.fn(),
      });

    renderWithTheme(
      <MultiContainerComparisonView {...mockProps} showRanking={false} />
    );

    await waitFor(() => {
      expect(screen.queryByText("Performance Ranking")).not.toBeInTheDocument();
    });
  });

  it("displays aggregate statistics correctly", async () => {
    // Reset all mocks first
    jest.clearAllMocks();

    // Mock implementation that returns different values for each call
    let callCount = 0;
    mockUseApiCall.mockImplementation(() => {
      callCount++;
      if (callCount === 1) {
        // First call - containers
        return {
          data: mockContainers,
          loading: false,
          error: null,
          execute: jest.fn(),
        };
      } else {
        // Second call - comparison data
        return {
          data: mockComparisonData,
          loading: false,
          error: null,
          execute: jest.fn(),
        };
      }
    });

    renderWithTheme(<MultiContainerComparisonView {...mockProps} />);

    await waitFor(
      () => {
        expect(screen.getByText("Aggregate Statistics")).toBeInTheDocument();
        expect(screen.getByText(/Avg CPU: 55.4%/)).toBeInTheDocument();
        expect(screen.getByText(/Avg Memory: 70.2%/)).toBeInTheDocument();
        expect(screen.getByText(/Total Network I\/O:/)).toBeInTheDocument();
        expect(screen.getByText(/Total Disk I\/O:/)).toBeInTheDocument();
      },
      { timeout: 20000 }
    );
  }, 30000);

  it("applies custom height correctly", () => {
    mockUseApiCall
      .mockReturnValueOnce({
        data: mockContainers,
        loading: false,
        error: null,
        execute: jest.fn(),
      })
      .mockReturnValueOnce({
        data: mockComparisonData,
        loading: false,
        error: null,
        execute: jest.fn(),
      });

    const customHeight = 600;
    const { container } = renderWithTheme(
      <MultiContainerComparisonView {...mockProps} height={customHeight} />
    );

    const paper = container.querySelector(".MuiPaper-root");
    expect(paper).toHaveStyle(`height: ${customHeight}px`);
  });

  it("displays performance overview chart title", async () => {
    mockUseApiCall
      .mockReturnValueOnce({
        data: mockContainers,
        loading: false,
        error: null,
        execute: jest.fn(),
      })
      .mockReturnValueOnce({
        data: mockComparisonData,
        loading: false,
        error: null,
        execute: jest.fn(),
      });

    renderWithTheme(<MultiContainerComparisonView {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText("Performance Overview")).toBeInTheDocument();
    });
  });

  it("handles empty comparison data gracefully", async () => {
    const emptyComparisonData = {
      ...mockComparisonData,
      metrics_comparison: {},
    };

    mockUseApiCall
      .mockReturnValueOnce({
        data: mockContainers,
        loading: false,
        error: null,
        execute: jest.fn(),
      })
      .mockReturnValueOnce({
        data: emptyComparisonData,
        loading: false,
        error: null,
        execute: jest.fn(),
      });

    renderWithTheme(<MultiContainerComparisonView {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText("Container Comparison")).toBeInTheDocument();
      // Should handle empty data gracefully without crashing
    });
  });

  it("displays correct chart title based on selected metric", async () => {
    mockUseApiCall
      .mockReturnValueOnce({
        data: mockContainers,
        loading: false,
        error: null,
        execute: jest.fn(),
      })
      .mockReturnValueOnce({
        data: mockComparisonData,
        loading: false,
        error: null,
        execute: jest.fn(),
      });

    renderWithTheme(<MultiContainerComparisonView {...mockProps} />);

    await waitFor(
      () => {
        expect(screen.getByText("CPU Usage Comparison")).toBeInTheDocument();
      },
      { timeout: 20000 }
    );

    const metricSelector = screen.getAllByRole("combobox")[1];

    await act(async () => {
      fireEvent.mouseDown(metricSelector);
    });

    await act(async () => {
      fireEvent.click(screen.getByText("Memory Usage"));
    });

    await waitFor(
      () => {
        expect(screen.getByText("Memory Usage Comparison")).toBeInTheDocument();
      },
      { timeout: 20000 }
    );
  });
});
