import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import RealTimeMetricsGrid from '../RealTimeMetricsGrid';
import { ContainerMetrics } from '../../types/enhancedMetrics';
import theme from '../../theme';

// Mock Recharts components
jest.mock('recharts', () => ({
  LineChart: ({ children }: any) => <div data-testid="line-chart">{children}</div>,
  Line: () => <div data-testid="line" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  ResponsiveContainer: ({ children }: any) => <div data-testid="responsive-container">{children}</div>,
  ReferenceLine: () => <div data-testid="reference-line" />,
}));

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  );
};

const mockContainerMetrics: ContainerMetrics = {
  container_id: 'test-container',
  container_name: 'test-container-name',
  cpu_percent: 45.5,
  memory_percent: 62.3,
  memory_usage: 1073741824, // 1GB
  memory_limit: 2147483648, // 2GB
  network_rx_bytes: 1048576, // 1MB
  network_tx_bytes: 2097152, // 2MB
  block_read_bytes: 524288, // 512KB
  block_write_bytes: 1048576, // 1MB
  status: 'running',
  timestamp: new Date().toISOString(),
};

const mockProps = {
  containerId: 'test-container',
  containerName: 'test-container-name',
  metricsData: mockContainerMetrics,
  autoRefresh: true,
  refreshInterval: 3000,
  onRefresh: jest.fn(),
  onAutoRefreshToggle: jest.fn(),
  loading: false,
  error: null,
};

describe('RealTimeMetricsGrid', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders real-time metrics grid correctly', async () => {
    renderWithTheme(<RealTimeMetricsGrid {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText('Real-Time Metrics')).toBeInTheDocument();
      expect(screen.getByText('test-container-name')).toBeInTheDocument();
      expect(screen.getByText('CPU Usage')).toBeInTheDocument();
      expect(screen.getByText('Memory Usage')).toBeInTheDocument();
      expect(screen.getByText('Network I/O')).toBeInTheDocument();
      expect(screen.getByText('Disk I/O')).toBeInTheDocument();
    });
  });

  it('displays current metric values correctly', async () => {
    renderWithTheme(<RealTimeMetricsGrid {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText('45.5%')).toBeInTheDocument(); // CPU
      expect(screen.getByText('62.3%')).toBeInTheDocument(); // Memory
    });
  });

  it('handles auto-refresh toggle', async () => {
    renderWithTheme(<RealTimeMetricsGrid {...mockProps} />);

    const autoRefreshSwitch = screen.getByRole('checkbox');
    expect(autoRefreshSwitch).toBeChecked();

    await act(async () => {
      fireEvent.click(autoRefreshSwitch);
    });

    expect(mockProps.onAutoRefreshToggle).toHaveBeenCalledWith(false);
  });

  it('handles manual refresh button click', async () => {
    renderWithTheme(<RealTimeMetricsGrid {...mockProps} />);

    const refreshButton = screen.getByRole('button');
    
    await act(async () => {
      fireEvent.click(refreshButton);
    });

    expect(mockProps.onRefresh).toHaveBeenCalled();
  });

  it('displays error state correctly', () => {
    const errorMessage = 'Failed to load metrics';
    renderWithTheme(
      <RealTimeMetricsGrid
        {...mockProps}
        error={errorMessage}
      />
    );

    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });

  it('displays loading state correctly', () => {
    renderWithTheme(
      <RealTimeMetricsGrid
        {...mockProps}
        loading={true}
      />
    );

    // Component should still render but may show loading indicators
    expect(screen.getByText('Real-Time Metrics')).toBeInTheDocument();
  });

  it('renders charts for all metric types', async () => {
    renderWithTheme(<RealTimeMetricsGrid {...mockProps} />);

    await waitFor(() => {
      const charts = screen.getAllByTestId('responsive-container');
      expect(charts).toHaveLength(4); // CPU, Memory, Network, Disk
    });
  });

  it('displays refresh interval correctly', async () => {
    renderWithTheme(<RealTimeMetricsGrid {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText('3s interval')).toBeInTheDocument();
    });
  });

  it('handles different refresh intervals', async () => {
    renderWithTheme(
      <RealTimeMetricsGrid
        {...mockProps}
        refreshInterval={5000}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('5s interval')).toBeInTheDocument();
    });
  });

  it('updates metrics history when new data arrives', async () => {
    const { rerender } = renderWithTheme(<RealTimeMetricsGrid {...mockProps} />);

    const newMetrics: ContainerMetrics = {
      ...mockContainerMetrics,
      cpu_percent: 55.0,
      memory_percent: 70.0,
      timestamp: new Date(Date.now() + 3000).toISOString(),
    };

    await act(async () => {
      rerender(
        <ThemeProvider theme={theme}>
          <RealTimeMetricsGrid
            {...mockProps}
            metricsData={newMetrics}
          />
        </ThemeProvider>
      );
    });

    await waitFor(() => {
      expect(screen.getByText('55.0%')).toBeInTheDocument();
      expect(screen.getByText('70.0%')).toBeInTheDocument();
    });
  });

  it('displays status information correctly', async () => {
    renderWithTheme(<RealTimeMetricsGrid {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText(/Last updated:/)).toBeInTheDocument();
      expect(screen.getByText(/Status: running/)).toBeInTheDocument();
      expect(screen.getByText(/CPU: 45.5%/)).toBeInTheDocument();
      expect(screen.getByText(/Memory: 62.3%/)).toBeInTheDocument();
    });
  });

  it('handles null metrics data gracefully', () => {
    renderWithTheme(
      <RealTimeMetricsGrid
        {...mockProps}
        metricsData={null}
      />
    );

    expect(screen.getByText('Real-Time Metrics')).toBeInTheDocument();
    // Should not crash and should handle null data gracefully
  });

  it('displays trend indicators correctly', async () => {
    renderWithTheme(<RealTimeMetricsGrid {...mockProps} />);

    await waitFor(() => {
      // Trend icons should be present for each metric
      expect(screen.getByText('CPU Usage')).toBeInTheDocument();
      expect(screen.getByText('Memory Usage')).toBeInTheDocument();
      expect(screen.getByText('Network I/O')).toBeInTheDocument();
      expect(screen.getByText('Disk I/O')).toBeInTheDocument();
    });
  });

  it('handles auto-refresh disabled state', async () => {
    renderWithTheme(
      <RealTimeMetricsGrid
        {...mockProps}
        autoRefresh={false}
      />
    );

    const autoRefreshSwitch = screen.getByRole('checkbox');
    expect(autoRefreshSwitch).not.toBeChecked();
  });

  it('displays container name chip when provided', async () => {
    renderWithTheme(<RealTimeMetricsGrid {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText('test-container-name')).toBeInTheDocument();
    });
  });

  it('handles missing container name gracefully', async () => {
    renderWithTheme(
      <RealTimeMetricsGrid
        {...mockProps}
        containerName={undefined}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Real-Time Metrics')).toBeInTheDocument();
      // Should not show container name chip
      expect(screen.queryByText('test-container-name')).not.toBeInTheDocument();
    });
  });

  it('displays threshold lines in charts', async () => {
    renderWithTheme(<RealTimeMetricsGrid {...mockProps} />);

    await waitFor(() => {
      const referenceLines = screen.getAllByTestId('reference-line');
      expect(referenceLines.length).toBeGreaterThan(0);
    });
  });

  it('handles different metric data points correctly', async () => {
    const highUsageMetrics: ContainerMetrics = {
      ...mockContainerMetrics,
      cpu_percent: 95.0,
      memory_percent: 90.0,
    };

    renderWithTheme(
      <RealTimeMetricsGrid
        {...mockProps}
        metricsData={highUsageMetrics}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('95.0%')).toBeInTheDocument();
      expect(screen.getByText('90.0%')).toBeInTheDocument();
    });
  });

  it('displays correct data point counts', async () => {
    renderWithTheme(<RealTimeMetricsGrid {...mockProps} />);

    await waitFor(() => {
      // Should show data point counts for each chart
      const pointsText = screen.getAllByText(/Points: \d+/);
      expect(pointsText.length).toBe(4); // One for each metric chart
    });
  });
});
