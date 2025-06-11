/**
 * Real-Time Metrics Grid Component
 * 
 * Enhanced real-time metrics display with CPU, memory, network, and disk I/O charts
 * featuring live data updates, trend indicators, and responsive design.
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  IconButton,
  Switch,
  FormControlLabel,
  Chip,
  Alert,
  useTheme,
  Tooltip,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  TrendingFlat as TrendingFlatIcon,
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { format } from 'date-fns';
import { ContainerMetrics } from '../types/enhancedMetrics';
import { formatBytes, formatPercentage } from '../utils/formatters';

interface MetricDataPoint {
  timestamp: string;
  value: number;
  time: string;
}

interface RealTimeMetricsGridProps {
  containerId: string;
  containerName?: string;
  metricsData: ContainerMetrics | null;
  autoRefresh?: boolean;
  refreshInterval?: number;
  onRefresh?: () => void;
  onAutoRefreshToggle?: (enabled: boolean) => void;
  loading?: boolean;
  error?: string;
  maxDataPoints?: number;
}

const RealTimeMetricsGrid: React.FC<RealTimeMetricsGridProps> = ({
  containerId,
  containerName,
  metricsData,
  autoRefresh = true,
  refreshInterval = 3000,
  onRefresh,
  onAutoRefreshToggle,
  loading = false,
  error,
  maxDataPoints = 50,
}) => {
  const theme = useTheme();
  const [metricsHistory, setMetricsHistory] = useState<{
    cpu: MetricDataPoint[];
    memory: MetricDataPoint[];
    network: MetricDataPoint[];
    disk: MetricDataPoint[];
  }>({
    cpu: [],
    memory: [],
    network: [],
    disk: [],
  });

  // Update metrics history when new data arrives
  useEffect(() => {
    if (metricsData) {
      const timestamp = metricsData.timestamp;
      const time = format(new Date(timestamp), 'HH:mm:ss');

      setMetricsHistory((prev) => {
        const newCpuPoint: MetricDataPoint = {
          timestamp,
          value: metricsData.cpu_percent || 0,
          time,
        };

        const newMemoryPoint: MetricDataPoint = {
          timestamp,
          value: metricsData.memory_percent || 0,
          time,
        };

        const newNetworkPoint: MetricDataPoint = {
          timestamp,
          value: (metricsData.network_rx_bytes + metricsData.network_tx_bytes) / 1024 / 1024, // MB/s
          time,
        };

        const newDiskPoint: MetricDataPoint = {
          timestamp,
          value: (metricsData.block_read_bytes + metricsData.block_write_bytes) / 1024 / 1024, // MB/s
          time,
        };

        return {
          cpu: [...prev.cpu.slice(-maxDataPoints + 1), newCpuPoint],
          memory: [...prev.memory.slice(-maxDataPoints + 1), newMemoryPoint],
          network: [...prev.network.slice(-maxDataPoints + 1), newNetworkPoint],
          disk: [...prev.disk.slice(-maxDataPoints + 1), newDiskPoint],
        };
      });
    }
  }, [metricsData, maxDataPoints]);

  // Get trend direction for a metric
  const getTrend = (data: MetricDataPoint[]) => {
    if (data.length < 2) return 'stable';
    
    const recent = data.slice(-5); // Last 5 data points
    const first = recent[0]?.value || 0;
    const last = recent[recent.length - 1]?.value || 0;
    const diff = last - first;
    
    if (Math.abs(diff) < 2) return 'stable';
    return diff > 0 ? 'increasing' : 'decreasing';
  };

  // Get trend icon
  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'increasing':
        return <TrendingUpIcon fontSize="small" color="error" />;
      case 'decreasing':
        return <TrendingDownIcon fontSize="small" color="success" />;
      default:
        return <TrendingFlatIcon fontSize="small" color="info" />;
    }
  };

  // Get current value with formatting
  const getCurrentValue = (metric: string) => {
    if (!metricsData) return 'N/A';
    
    switch (metric) {
      case 'cpu':
        return formatPercentage(metricsData.cpu_percent);
      case 'memory':
        return formatPercentage(metricsData.memory_percent);
      case 'network':
        return formatBytes((metricsData.network_rx_bytes + metricsData.network_tx_bytes));
      case 'disk':
        return formatBytes((metricsData.block_read_bytes + metricsData.block_write_bytes));
      default:
        return 'N/A';
    }
  };

  // Custom tooltip for charts
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0];
      return (
        <Paper sx={{ p: 1, border: 1, borderColor: 'divider' }}>
          <Typography variant="body2" fontWeight="bold">
            {label}
          </Typography>
          <Typography variant="body2" sx={{ color: data.color }}>
            {data.name}: {data.payload.value.toFixed(2)}
            {data.name.includes('CPU') || data.name.includes('Memory') ? '%' : ' MB/s'}
          </Typography>
        </Paper>
      );
    }
    return null;
  };

  // Metric chart component
  const MetricChart = ({ 
    title, 
    data, 
    color, 
    unit, 
    threshold 
  }: { 
    title: string; 
    data: MetricDataPoint[]; 
    color: string; 
    unit: string;
    threshold?: number;
  }) => {
    const trend = getTrend(data);
    const currentValue = data[data.length - 1]?.value || 0;

    return (
      <Paper elevation={2} sx={{ p: 2, height: 280 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
          <Typography variant="subtitle1" fontWeight="bold">
            {title}
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {getTrendIcon(trend)}
            <Typography variant="h6" sx={{ color }}>
              {currentValue.toFixed(1)}{unit}
            </Typography>
          </Box>
        </Box>
        
        <Box sx={{ height: 200 }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="time"
                tick={{ fontSize: 10 }}
                interval="preserveStartEnd"
              />
              <YAxis
                tick={{ fontSize: 10 }}
                domain={['dataMin - 5', 'dataMax + 5']}
              />
              <RechartsTooltip content={<CustomTooltip />} />
              <Line
                type="monotone"
                dataKey="value"
                stroke={color}
                strokeWidth={2}
                dot={false}
                name={title}
                connectNulls={false}
              />
              {threshold && (
                <ReferenceLine
                  y={threshold}
                  stroke={theme.palette.warning.main}
                  strokeDasharray="5 5"
                />
              )}
            </LineChart>
          </ResponsiveContainer>
        </Box>
        
        <Typography variant="caption" color="text.secondary">
          Trend: {trend} | Points: {data.length}
        </Typography>
      </Paper>
    );
  };

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
      </Alert>
    );
  }

  return (
    <Box>
      {/* Controls */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Box>
          <Typography variant="h6">
            Real-Time Metrics
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
          <FormControlLabel
            control={
              <Switch
                checked={autoRefresh}
                onChange={(e) => onAutoRefreshToggle?.(e.target.checked)}
                size="small"
              />
            }
            label="Auto-refresh"
          />
          
          <Tooltip title="Manual refresh">
            <IconButton
              onClick={onRefresh}
              disabled={loading}
              size="small"
            >
              {autoRefresh ? <PauseIcon /> : <PlayIcon />}
              <RefreshIcon sx={{ ml: 0.5 }} />
            </IconButton>
          </Tooltip>
          
          <Chip
            label={`${refreshInterval / 1000}s interval`}
            size="small"
            variant="outlined"
          />
        </Box>
      </Box>

      {/* Metrics Grid */}
      <Grid container spacing={2}>
        <Grid item xs={12} md={6}>
          <MetricChart
            title="CPU Usage"
            data={metricsHistory.cpu}
            color={theme.palette.primary.main}
            unit="%"
            threshold={80}
          />
        </Grid>
        
        <Grid item xs={12} md={6}>
          <MetricChart
            title="Memory Usage"
            data={metricsHistory.memory}
            color={theme.palette.secondary.main}
            unit="%"
            threshold={85}
          />
        </Grid>
        
        <Grid item xs={12} md={6}>
          <MetricChart
            title="Network I/O"
            data={metricsHistory.network}
            color={theme.palette.info.main}
            unit=" MB/s"
          />
        </Grid>
        
        <Grid item xs={12} md={6}>
          <MetricChart
            title="Disk I/O"
            data={metricsHistory.disk}
            color={theme.palette.success.main}
            unit=" MB/s"
          />
        </Grid>
      </Grid>

      {/* Status */}
      {metricsData && (
        <Box sx={{ mt: 2, p: 1, backgroundColor: 'background.paper', borderRadius: 1 }}>
          <Typography variant="caption" color="text.secondary">
            Last updated: {format(new Date(metricsData.timestamp), 'MMM dd, HH:mm:ss')} |
            Status: {metricsData.status} |
            CPU: {getCurrentValue('cpu')} |
            Memory: {getCurrentValue('memory')} |
            Network: {getCurrentValue('network')} |
            Disk: {getCurrentValue('disk')}
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default RealTimeMetricsGrid;
