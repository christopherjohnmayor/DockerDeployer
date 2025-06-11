/**
 * Performance Prediction Charts Component
 * 
 * Displays resource usage forecasts with confidence intervals
 * and trend analysis for container performance prediction.
 */

import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
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
  Area,
  AreaChart,
  ReferenceLine,
} from 'recharts';
import { format } from 'date-fns';
import { PredictionData, PredictionPoint } from '../types/enhancedMetrics';
import { formatBytes, formatPercentage } from '../utils/formatters';

interface PerformancePredictionChartsProps {
  predictionData: PredictionData | null;
  loading?: boolean;
  error?: string;
  showConfidenceIntervals?: boolean;
  showThresholds?: boolean;
  height?: number;
}

const PerformancePredictionCharts: React.FC<PerformancePredictionChartsProps> = ({
  predictionData,
  loading = false,
  error,
  showConfidenceIntervals = true,
  showThresholds = true,
  height = 300,
}) => {
  const theme = useTheme();
  const [selectedMetric, setSelectedMetric] = useState<string>('cpu_percent');

  const handleMetricChange = (event: SelectChangeEvent) => {
    setSelectedMetric(event.target.value);
  };

  // Format prediction data for charts
  const formatPredictionData = (predictions: PredictionPoint[]) => {
    return predictions.map((point) => ({
      timestamp: point.timestamp,
      time: format(new Date(point.timestamp), 'HH:mm'),
      predicted: point.predicted_value,
      lower: point.confidence_lower,
      upper: point.confidence_upper,
      trend: point.trend,
    }));
  };

  // Get metric configuration
  const getMetricConfig = (metric: string) => {
    const configs = {
      cpu_percent: {
        title: 'CPU Usage Prediction',
        color: theme.palette.primary.main,
        unit: '%',
        formatter: formatPercentage,
        threshold: 80,
      },
      memory_percent: {
        title: 'Memory Usage Prediction',
        color: theme.palette.secondary.main,
        unit: '%',
        formatter: formatPercentage,
        threshold: 85,
      },
      network_io: {
        title: 'Network I/O Prediction',
        color: theme.palette.info.main,
        unit: ' MB/s',
        formatter: (value: number) => formatBytes(value * 1024 * 1024),
        threshold: 100,
      },
      disk_io: {
        title: 'Disk I/O Prediction',
        color: theme.palette.success.main,
        unit: ' MB/s',
        formatter: (value: number) => formatBytes(value * 1024 * 1024),
        threshold: 50,
      },
    };
    return configs[metric as keyof typeof configs] || configs.cpu_percent;
  };

  // Get trend color
  const getTrendColor = (trend: string) => {
    switch (trend) {
      case 'increasing':
        return theme.palette.error.main;
      case 'decreasing':
        return theme.palette.success.main;
      case 'stable':
        return theme.palette.info.main;
      default:
        return theme.palette.grey[500];
    }
  };

  // Custom tooltip for prediction charts
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      const config = getMetricConfig(selectedMetric);
      
      return (
        <Paper sx={{ p: 1, border: 1, borderColor: 'divider' }}>
          <Typography variant="body2" fontWeight="bold">
            {format(new Date(data.timestamp), 'MMM dd, HH:mm')}
          </Typography>
          <Typography variant="body2" color={config.color}>
            Predicted: {config.formatter(data.predicted)}
          </Typography>
          {showConfidenceIntervals && (
            <>
              <Typography variant="body2" color="text.secondary">
                Range: {config.formatter(data.lower)} - {config.formatter(data.upper)}
              </Typography>
              <Chip
                label={data.trend}
                size="small"
                sx={{
                  mt: 0.5,
                  backgroundColor: getTrendColor(data.trend),
                  color: 'white',
                  fontSize: '0.7rem',
                }}
              />
            </>
          )}
        </Paper>
      );
    }
    return null;
  };

  if (loading) {
    return (
      <Paper elevation={2} sx={{ p: 2, height }}>
        <Typography variant="h6" gutterBottom>
          Performance Predictions
        </Typography>
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '80%' }}>
          <Typography variant="body2" color="text.secondary">
            Loading predictions...
          </Typography>
        </Box>
      </Paper>
    );
  }

  if (error) {
    return (
      <Paper elevation={2} sx={{ p: 2, height }}>
        <Typography variant="h6" gutterBottom>
          Performance Predictions
        </Typography>
        <Alert severity="error">{error}</Alert>
      </Paper>
    );
  }

  if (!predictionData) {
    return (
      <Paper elevation={2} sx={{ p: 2, height }}>
        <Typography variant="h6" gutterBottom>
          Performance Predictions
        </Typography>
        <Alert severity="info">No prediction data available</Alert>
      </Paper>
    );
  }

  const config = getMetricConfig(selectedMetric);
  const chartData = formatPredictionData(
    predictionData.predictions[selectedMetric as keyof typeof predictionData.predictions] || []
  );

  return (
    <Paper elevation={2} sx={{ p: 2, height }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">
          Performance Predictions
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Chip
            label={`${predictionData.prediction_horizon_hours}h forecast`}
            size="small"
            color="primary"
          />
          <Chip
            label={`${Math.round(predictionData.confidence_level * 100)}% confidence`}
            size="small"
            color="info"
          />
        </Box>
      </Box>

      {/* Metric Selector */}
      <Box sx={{ mb: 2 }}>
        <FormControl size="small" sx={{ minWidth: 200 }}>
          <InputLabel>Metric</InputLabel>
          <Select
            value={selectedMetric}
            label="Metric"
            onChange={handleMetricChange}
          >
            <MenuItem value="cpu_percent">CPU Usage</MenuItem>
            <MenuItem value="memory_percent">Memory Usage</MenuItem>
            <MenuItem value="network_io">Network I/O</MenuItem>
            <MenuItem value="disk_io">Disk I/O</MenuItem>
          </Select>
        </FormControl>
      </Box>

      {/* Prediction Chart */}
      <Box sx={{ height: height - 120 }}>
        <ResponsiveContainer width="100%" height="100%">
          {showConfidenceIntervals ? (
            <AreaChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="time"
                tick={{ fontSize: 12 }}
              />
              <YAxis
                tickFormatter={(value) => config.formatter(value)}
                tick={{ fontSize: 12 }}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              
              {/* Confidence interval area */}
              <Area
                type="monotone"
                dataKey="upper"
                stackId="1"
                stroke="none"
                fill={config.color}
                fillOpacity={0.1}
                name="Confidence Upper"
              />
              <Area
                type="monotone"
                dataKey="lower"
                stackId="1"
                stroke="none"
                fill="white"
                fillOpacity={1}
                name="Confidence Lower"
              />
              
              {/* Predicted value line */}
              <Line
                type="monotone"
                dataKey="predicted"
                stroke={config.color}
                strokeWidth={2}
                dot={{ fill: config.color, strokeWidth: 2, r: 3 }}
                name={`Predicted ${config.title.split(' ')[0]}`}
              />
              
              {/* Threshold line */}
              {showThresholds && (
                <ReferenceLine
                  y={config.threshold}
                  stroke={theme.palette.warning.main}
                  strokeDasharray="5 5"
                  label="Threshold"
                />
              )}
            </AreaChart>
          ) : (
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="time"
                tick={{ fontSize: 12 }}
              />
              <YAxis
                tickFormatter={(value) => config.formatter(value)}
                tick={{ fontSize: 12 }}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              
              <Line
                type="monotone"
                dataKey="predicted"
                stroke={config.color}
                strokeWidth={2}
                dot={{ fill: config.color, strokeWidth: 2, r: 4 }}
                name={`Predicted ${config.title.split(' ')[0]}`}
              />
              
              {showThresholds && (
                <ReferenceLine
                  y={config.threshold}
                  stroke={theme.palette.warning.main}
                  strokeDasharray="5 5"
                  label="Threshold"
                />
              )}
            </LineChart>
          )}
        </ResponsiveContainer>
      </Box>

      {/* Model Info */}
      <Box sx={{ mt: 1, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="caption" color="text.secondary">
          Model Accuracy: {Math.round(predictionData.model_accuracy * 100)}%
        </Typography>
        <Typography variant="caption" color="text.secondary">
          Updated: {format(new Date(predictionData.prediction_timestamp), 'HH:mm:ss')}
        </Typography>
      </Box>
    </Paper>
  );
};

export default PerformancePredictionCharts;
