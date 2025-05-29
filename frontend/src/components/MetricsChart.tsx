import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
} from 'recharts';
import { Box, Typography, Paper, useTheme } from '@mui/material';
import { format } from 'date-fns';

export interface MetricDataPoint {
  timestamp: string;
  value: number;
  label?: string;
}

export interface MetricsChartProps {
  title: string;
  data: MetricDataPoint[];
  type?: 'line' | 'area' | 'bar';
  color?: string;
  unit?: string;
  height?: number;
  formatValue?: (value: number) => string;
  showGrid?: boolean;
  showLegend?: boolean;
  loading?: boolean;
  error?: string;
}

const MetricsChart: React.FC<MetricsChartProps> = ({
  title,
  data,
  type = 'line',
  color,
  unit = '',
  height = 300,
  formatValue,
  showGrid = true,
  showLegend = true,
  loading = false,
  error,
}) => {
  const theme = useTheme();
  
  // Default color based on theme
  const defaultColor = color || theme.palette.primary.main;
  
  // Format timestamp for display
  const formatTimestamp = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      return format(date, 'HH:mm');
    } catch {
      return timestamp;
    }
  };
  
  // Format value for tooltip and axis
  const formatValueDisplay = (value: number) => {
    if (formatValue) {
      return formatValue(value);
    }
    return `${value.toFixed(2)}${unit}`;
  };
  
  // Custom tooltip component
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0];
      return (
        <Paper
          elevation={3}
          sx={{
            p: 1.5,
            backgroundColor: theme.palette.background.paper,
            border: `1px solid ${theme.palette.divider}`,
          }}
        >
          <Typography variant="body2" color="textSecondary">
            {format(new Date(label), 'MMM dd, HH:mm:ss')}
          </Typography>
          <Typography variant="body1" sx={{ color: data.color }}>
            {`${title}: ${formatValueDisplay(data.value)}`}
          </Typography>
        </Paper>
      );
    }
    return null;
  };
  
  // Render loading state
  if (loading) {
    return (
      <Paper elevation={2} sx={{ p: 2, height }}>
        <Typography variant="h6" gutterBottom>
          {title}
        </Typography>
        <Box
          display="flex"
          alignItems="center"
          justifyContent="center"
          height={height - 80}
        >
          <Typography color="textSecondary">Loading metrics...</Typography>
        </Box>
      </Paper>
    );
  }
  
  // Render error state
  if (error) {
    return (
      <Paper elevation={2} sx={{ p: 2, height }}>
        <Typography variant="h6" gutterBottom>
          {title}
        </Typography>
        <Box
          display="flex"
          alignItems="center"
          justifyContent="center"
          height={height - 80}
        >
          <Typography color="error">{error}</Typography>
        </Box>
      </Paper>
    );
  }
  
  // Render empty state
  if (!data || data.length === 0) {
    return (
      <Paper elevation={2} sx={{ p: 2, height }}>
        <Typography variant="h6" gutterBottom>
          {title}
        </Typography>
        <Box
          display="flex"
          alignItems="center"
          justifyContent="center"
          height={height - 80}
        >
          <Typography color="textSecondary">No data available</Typography>
        </Box>
      </Paper>
    );
  }
  
  // Render chart based on type
  const renderChart = () => {
    const commonProps = {
      data,
      margin: { top: 5, right: 30, left: 20, bottom: 5 },
    };
    
    switch (type) {
      case 'area':
        return (
          <AreaChart {...commonProps}>
            {showGrid && <CartesianGrid strokeDasharray="3 3" />}
            <XAxis
              dataKey="timestamp"
              tickFormatter={formatTimestamp}
              tick={{ fontSize: 12 }}
            />
            <YAxis
              tickFormatter={(value) => formatValueDisplay(value)}
              tick={{ fontSize: 12 }}
            />
            <Tooltip content={<CustomTooltip />} />
            {showLegend && <Legend />}
            <Area
              type="monotone"
              dataKey="value"
              stroke={defaultColor}
              fill={defaultColor}
              fillOpacity={0.3}
              strokeWidth={2}
              name={title}
            />
          </AreaChart>
        );
        
      case 'bar':
        return (
          <BarChart {...commonProps}>
            {showGrid && <CartesianGrid strokeDasharray="3 3" />}
            <XAxis
              dataKey="timestamp"
              tickFormatter={formatTimestamp}
              tick={{ fontSize: 12 }}
            />
            <YAxis
              tickFormatter={(value) => formatValueDisplay(value)}
              tick={{ fontSize: 12 }}
            />
            <Tooltip content={<CustomTooltip />} />
            {showLegend && <Legend />}
            <Bar
              dataKey="value"
              fill={defaultColor}
              name={title}
            />
          </BarChart>
        );
        
      default: // line
        return (
          <LineChart {...commonProps}>
            {showGrid && <CartesianGrid strokeDasharray="3 3" />}
            <XAxis
              dataKey="timestamp"
              tickFormatter={formatTimestamp}
              tick={{ fontSize: 12 }}
            />
            <YAxis
              tickFormatter={(value) => formatValueDisplay(value)}
              tick={{ fontSize: 12 }}
            />
            <Tooltip content={<CustomTooltip />} />
            {showLegend && <Legend />}
            <Line
              type="monotone"
              dataKey="value"
              stroke={defaultColor}
              strokeWidth={2}
              dot={{ fill: defaultColor, strokeWidth: 2, r: 4 }}
              activeDot={{ r: 6 }}
              name={title}
            />
          </LineChart>
        );
    }
  };
  
  return (
    <Paper elevation={2} sx={{ p: 2, height }}>
      <Typography variant="h6" gutterBottom>
        {title}
      </Typography>
      <ResponsiveContainer width="100%" height={height - 60}>
        {renderChart()}
      </ResponsiveContainer>
    </Paper>
  );
};

export default MetricsChart;
