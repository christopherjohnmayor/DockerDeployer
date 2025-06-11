/**
 * Historical Trends Visualization Component
 * 
 * Displays historical metrics data with configurable time ranges (1h, 6h, 24h, 7d)
 * and multi-metric overlay charts for trend analysis.
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  ToggleButton,
  ToggleButtonGroup,
  Chip,
  Alert,
  useTheme,
  SelectChangeEvent,
} from '@mui/material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Brush,
  ReferenceLine,
} from 'recharts';
import { format, subHours, subDays } from 'date-fns';
import { TimeRange, HistoricalMetrics } from '../types/enhancedMetrics';
import { formatBytes, formatPercentage } from '../utils/formatters';
import { useApiCall } from '../hooks/useApiCall';

interface HistoricalTrendsVisualizationProps {
  containerId: string;
  containerName?: string;
  initialTimeRange?: TimeRange;
  height?: number;
  showBrush?: boolean;
  showThresholds?: boolean;
  onTimeRangeChange?: (timeRange: TimeRange) => void;
}

const HistoricalTrendsVisualization: React.FC<HistoricalTrendsVisualizationProps> = ({
  containerId,
  containerName,
  initialTimeRange = '24h',
  height = 400,
  showBrush = true,
  showThresholds = true,
  onTimeRangeChange,
}) => {
  const theme = useTheme();
  const [timeRange, setTimeRange] = useState<TimeRange>(initialTimeRange);
  const [selectedMetrics, setSelectedMetrics] = useState<string[]>(['cpu_percent', 'memory_percent']);
  const [chartData, setChartData] = useState<any[]>([]);

  // API call for historical data
  const {
    data: historicalData,
    loading,
    error,
    execute: fetchHistoricalData,
  } = useApiCall<HistoricalMetrics>();

  // Fetch historical data when time range or container changes
  useEffect(() => {
    if (containerId) {
      const hours = getHoursFromTimeRange(timeRange);
      fetchHistoricalData(
        `/api/containers/${containerId}/metrics/historical?time_range=${timeRange}&hours=${hours}`
      );
    }
  }, [containerId, timeRange, fetchHistoricalData]);

  // Process historical data for charts
  useEffect(() => {
    if (historicalData?.data_points) {
      const processedData = historicalData.data_points.map((point) => ({
        timestamp: point.timestamp,
        time: formatTimeLabel(point.timestamp, timeRange),
        fullTime: format(new Date(point.timestamp), 'MMM dd, HH:mm'),
        cpu_percent: point.value, // This would need to be expanded for multiple metrics
        memory_percent: point.value * 0.8, // Mock data - in real implementation, fetch all metrics
        network_io: point.value * 10, // Mock data
        disk_io: point.value * 5, // Mock data
      }));
      setChartData(processedData);
    }
  }, [historicalData, timeRange]);

  // Get hours from time range
  const getHoursFromTimeRange = (range: TimeRange): number => {
    switch (range) {
      case '1h': return 1;
      case '6h': return 6;
      case '24h': return 24;
      case '7d': return 168;
      case '30d': return 720;
      default: return 24;
    }
  };

  // Format time label based on time range
  const formatTimeLabel = (timestamp: string, range: TimeRange): string => {
    const date = new Date(timestamp);
    switch (range) {
      case '1h':
      case '6h':
        return format(date, 'HH:mm');
      case '24h':
        return format(date, 'HH:mm');
      case '7d':
        return format(date, 'MMM dd');
      case '30d':
        return format(date, 'MMM dd');
      default:
        return format(date, 'HH:mm');
    }
  };

  // Handle time range change
  const handleTimeRangeChange = (
    event: React.MouseEvent<HTMLElement>,
    newTimeRange: TimeRange | null,
  ) => {
    if (newTimeRange !== null) {
      setTimeRange(newTimeRange);
      onTimeRangeChange?.(newTimeRange);
    }
  };

  // Handle metric selection change
  const handleMetricSelectionChange = (event: SelectChangeEvent<string[]>) => {
    const value = event.target.value;
    setSelectedMetrics(typeof value === 'string' ? value.split(',') : value);
  };

  // Get metric configuration
  const getMetricConfig = (metric: string) => {
    const configs = {
      cpu_percent: {
        name: 'CPU Usage',
        color: theme.palette.primary.main,
        unit: '%',
        formatter: formatPercentage,
        threshold: 80,
      },
      memory_percent: {
        name: 'Memory Usage',
        color: theme.palette.secondary.main,
        unit: '%',
        formatter: formatPercentage,
        threshold: 85,
      },
      network_io: {
        name: 'Network I/O',
        color: theme.palette.info.main,
        unit: ' MB/s',
        formatter: (value: number) => formatBytes(value * 1024 * 1024),
        threshold: 100,
      },
      disk_io: {
        name: 'Disk I/O',
        color: theme.palette.success.main,
        unit: ' MB/s',
        formatter: (value: number) => formatBytes(value * 1024 * 1024),
        threshold: 50,
      },
    };
    return configs[metric as keyof typeof configs];
  };

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <Paper sx={{ p: 1, border: 1, borderColor: 'divider' }}>
          <Typography variant="body2" fontWeight="bold">
            {payload[0]?.payload?.fullTime}
          </Typography>
          {payload.map((entry: any, index: number) => {
            const config = getMetricConfig(entry.dataKey);
            return (
              <Typography
                key={index}
                variant="body2"
                sx={{ color: entry.color }}
              >
                {config?.name}: {config?.formatter(entry.value)}
              </Typography>
            );
          })}
        </Paper>
      );
    }
    return null;
  };

  if (loading) {
    return (
      <Paper elevation={2} sx={{ p: 2, height }}>
        <Typography variant="h6" gutterBottom>
          Historical Trends
        </Typography>
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '80%' }}>
          <Typography variant="body2" color="text.secondary">
            Loading historical data...
          </Typography>
        </Box>
      </Paper>
    );
  }

  if (error) {
    return (
      <Paper elevation={2} sx={{ p: 2, height }}>
        <Typography variant="h6" gutterBottom>
          Historical Trends
        </Typography>
        <Alert severity="error">{error}</Alert>
      </Paper>
    );
  }

  return (
    <Paper elevation={2} sx={{ p: 2, height }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Box>
          <Typography variant="h6">
            Historical Trends
            {containerName && (
              <Chip
                label={containerName}
                size="small"
                sx={{ ml: 1 }}
                color="primary"
              />
            )}
          </Typography>
        </Box>
        
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          {historicalData && (
            <Chip
              label={`${historicalData.total_points} data points`}
              size="small"
              variant="outlined"
            />
          )}
        </Box>
      </Box>

      {/* Controls */}
      <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap' }}>
        {/* Time Range Selector */}
        <ToggleButtonGroup
          value={timeRange}
          exclusive
          onChange={handleTimeRangeChange}
          size="small"
        >
          <ToggleButton value="1h">1H</ToggleButton>
          <ToggleButton value="6h">6H</ToggleButton>
          <ToggleButton value="24h">24H</ToggleButton>
          <ToggleButton value="7d">7D</ToggleButton>
          <ToggleButton value="30d">30D</ToggleButton>
        </ToggleButtonGroup>

        {/* Metric Selector */}
        <FormControl size="small" sx={{ minWidth: 200 }}>
          <InputLabel>Metrics</InputLabel>
          <Select
            multiple
            value={selectedMetrics}
            label="Metrics"
            onChange={handleMetricSelectionChange}
            renderValue={(selected) => (
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                {selected.map((value) => (
                  <Chip key={value} label={getMetricConfig(value)?.name} size="small" />
                ))}
              </Box>
            )}
          >
            <MenuItem value="cpu_percent">CPU Usage</MenuItem>
            <MenuItem value="memory_percent">Memory Usage</MenuItem>
            <MenuItem value="network_io">Network I/O</MenuItem>
            <MenuItem value="disk_io">Disk I/O</MenuItem>
          </Select>
        </FormControl>
      </Box>

      {/* Chart */}
      <Box sx={{ height: height - 140 }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="time"
              tick={{ fontSize: 12 }}
            />
            <YAxis
              tick={{ fontSize: 12 }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            
            {selectedMetrics.map((metric) => {
              const config = getMetricConfig(metric);
              return (
                <Line
                  key={metric}
                  type="monotone"
                  dataKey={metric}
                  stroke={config?.color}
                  strokeWidth={2}
                  dot={false}
                  name={config?.name}
                  connectNulls={false}
                />
              );
            })}
            
            {/* Threshold lines */}
            {showThresholds && selectedMetrics.map((metric) => {
              const config = getMetricConfig(metric);
              return config?.threshold ? (
                <ReferenceLine
                  key={`${metric}-threshold`}
                  y={config.threshold}
                  stroke={theme.palette.warning.main}
                  strokeDasharray="5 5"
                  label={`${config.name} Threshold`}
                />
              ) : null;
            })}
            
            {/* Brush for zooming */}
            {showBrush && chartData.length > 20 && (
              <Brush
                dataKey="time"
                height={30}
                stroke={theme.palette.primary.main}
              />
            )}
          </LineChart>
        </ResponsiveContainer>
      </Box>

      {/* Summary */}
      {historicalData && (
        <Typography variant="caption" color="text.secondary">
          Time range: {timeRange} | 
          Aggregation: {historicalData.aggregation_level} | 
          Data points: {historicalData.total_points}
        </Typography>
      )}
    </Paper>
  );
};

export default HistoricalTrendsVisualization;
