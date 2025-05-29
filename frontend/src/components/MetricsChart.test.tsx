import React from 'react';
import { render, screen } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import { createTheme } from '@mui/material/styles';
import MetricsChart, { MetricDataPoint } from './MetricsChart';

const theme = createTheme();

const mockData: MetricDataPoint[] = [
  { timestamp: '2024-01-01T12:00:00Z', value: 25.5 },
  { timestamp: '2024-01-01T12:01:00Z', value: 30.2 },
  { timestamp: '2024-01-01T12:02:00Z', value: 28.7 },
  { timestamp: '2024-01-01T12:03:00Z', value: 35.1 },
  { timestamp: '2024-01-01T12:04:00Z', value: 32.8 },
];

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  );
};

describe('MetricsChart', () => {
  it('renders chart with title and data', () => {
    renderWithTheme(
      <MetricsChart
        title="CPU Usage"
        data={mockData}
        unit="%"
      />
    );

    expect(screen.getByText('CPU Usage')).toBeInTheDocument();
  });

  it('renders loading state', () => {
    renderWithTheme(
      <MetricsChart
        title="CPU Usage"
        data={[]}
        loading={true}
      />
    );

    expect(screen.getByText('CPU Usage')).toBeInTheDocument();
    expect(screen.getByText('Loading metrics...')).toBeInTheDocument();
  });

  it('renders error state', () => {
    const errorMessage = 'Failed to load metrics';
    renderWithTheme(
      <MetricsChart
        title="CPU Usage"
        data={[]}
        error={errorMessage}
      />
    );

    expect(screen.getByText('CPU Usage')).toBeInTheDocument();
    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });

  it('renders empty state when no data', () => {
    renderWithTheme(
      <MetricsChart
        title="CPU Usage"
        data={[]}
      />
    );

    expect(screen.getByText('CPU Usage')).toBeInTheDocument();
    expect(screen.getByText('No data available')).toBeInTheDocument();
  });

  it('renders line chart by default', () => {
    const { container } = renderWithTheme(
      <MetricsChart
        title="CPU Usage"
        data={mockData}
        unit="%"
      />
    );

    // Check for Recharts LineChart component
    expect(container.querySelector('.recharts-line')).toBeInTheDocument();
  });

  it('renders area chart when type is area', () => {
    const { container } = renderWithTheme(
      <MetricsChart
        title="Memory Usage"
        data={mockData}
        type="area"
        unit="%"
      />
    );

    // Check for Recharts AreaChart component
    expect(container.querySelector('.recharts-area')).toBeInTheDocument();
  });

  it('renders bar chart when type is bar', () => {
    const { container } = renderWithTheme(
      <MetricsChart
        title="Network Usage"
        data={mockData}
        type="bar"
        unit=" MB"
      />
    );

    // Check for Recharts BarChart component
    expect(container.querySelector('.recharts-bar')).toBeInTheDocument();
  });

  it('applies custom color', () => {
    const customColor = '#ff0000';
    const { container } = renderWithTheme(
      <MetricsChart
        title="CPU Usage"
        data={mockData}
        color={customColor}
        unit="%"
      />
    );

    // Check that the line has the custom color
    const line = container.querySelector('.recharts-line .recharts-line-curve');
    expect(line).toHaveAttribute('stroke', customColor);
  });

  it('uses custom formatValue function', () => {
    const formatValue = (value: number) => `${value.toFixed(0)} percent`;
    renderWithTheme(
      <MetricsChart
        title="CPU Usage"
        data={mockData}
        formatValue={formatValue}
      />
    );

    // The custom format function should be used in tooltips and axis labels
    expect(screen.getByText('CPU Usage')).toBeInTheDocument();
  });

  it('applies custom height', () => {
    const customHeight = 500;
    const { container } = renderWithTheme(
      <MetricsChart
        title="CPU Usage"
        data={mockData}
        height={customHeight}
        unit="%"
      />
    );

    // Check that the container has the custom height
    const paper = container.querySelector('.MuiPaper-root');
    expect(paper).toHaveStyle(`height: ${customHeight}px`);
  });

  it('shows grid when showGrid is true', () => {
    const { container } = renderWithTheme(
      <MetricsChart
        title="CPU Usage"
        data={mockData}
        showGrid={true}
        unit="%"
      />
    );

    // Check for CartesianGrid component
    expect(container.querySelector('.recharts-cartesian-grid')).toBeInTheDocument();
  });

  it('hides grid when showGrid is false', () => {
    const { container } = renderWithTheme(
      <MetricsChart
        title="CPU Usage"
        data={mockData}
        showGrid={false}
        unit="%"
      />
    );

    // Check that CartesianGrid component is not present
    expect(container.querySelector('.recharts-cartesian-grid')).not.toBeInTheDocument();
  });

  it('shows legend when showLegend is true', () => {
    const { container } = renderWithTheme(
      <MetricsChart
        title="CPU Usage"
        data={mockData}
        showLegend={true}
        unit="%"
      />
    );

    // Check for Legend component
    expect(container.querySelector('.recharts-legend-wrapper')).toBeInTheDocument();
  });

  it('hides legend when showLegend is false', () => {
    const { container } = renderWithTheme(
      <MetricsChart
        title="CPU Usage"
        data={mockData}
        showLegend={false}
        unit="%"
      />
    );

    // Check that Legend component is not present
    expect(container.querySelector('.recharts-legend-wrapper')).not.toBeInTheDocument();
  });

  it('handles empty data gracefully', () => {
    renderWithTheme(
      <MetricsChart
        title="CPU Usage"
        data={[]}
        unit="%"
      />
    );

    expect(screen.getByText('CPU Usage')).toBeInTheDocument();
    expect(screen.getByText('No data available')).toBeInTheDocument();
  });

  it('handles null data gracefully', () => {
    renderWithTheme(
      <MetricsChart
        title="CPU Usage"
        data={null as any}
        unit="%"
      />
    );

    expect(screen.getByText('CPU Usage')).toBeInTheDocument();
    expect(screen.getByText('No data available')).toBeInTheDocument();
  });

  it('renders with minimal props', () => {
    renderWithTheme(
      <MetricsChart
        title="Basic Chart"
        data={mockData}
      />
    );

    expect(screen.getByText('Basic Chart')).toBeInTheDocument();
  });
});
