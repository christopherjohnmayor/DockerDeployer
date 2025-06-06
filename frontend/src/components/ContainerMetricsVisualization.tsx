import React, { useState, useEffect, useCallback } from "react";
import {
  Box,
  Grid,
  Paper,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  CircularProgress,
  Alert,
  Card,
  CardContent,
  Chip,
  LinearProgress,
  Tooltip,
  IconButton,
  Switch,
  FormControlLabel,
} from "@mui/material";
import { useTheme } from "@mui/material/styles";
import RefreshIcon from "@mui/icons-material/Refresh";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import TrendingDownIcon from "@mui/icons-material/TrendingDown";
import TrendingFlatIcon from "@mui/icons-material/TrendingFlat";
import HealthAndSafetyIcon from "@mui/icons-material/HealthAndSafety";
import PredictionsIcon from "@mui/icons-material/Timeline";
import MetricsChart, { MetricDataPoint } from "./MetricsChart";
import { useApiCall } from "../hooks/useApiCall";
import { formatBytes, formatPercentage } from "../utils/formatters";

interface ContainerMetricsVisualizationProps {
  containerId: string;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

interface HealthScore {
  overall_health_score: number;
  health_status: string;
  component_scores: {
    cpu_health: number;
    memory_health: number;
    network_health: number;
    disk_health: number;
  };
  recommendations: string[];
}

interface Prediction {
  cpu_percent: {
    values: number[];
    timestamps: string[];
    confidence: number;
  };
  memory_percent: {
    values: number[];
    timestamps: string[];
    confidence: number;
  };
  trend_analysis: {
    cpu_trend: string;
    memory_trend: string;
  };
  alerts: Array<{
    type: string;
    metric: string;
    message: string;
    severity: string;
  }>;
}

interface EnhancedMetrics {
  health_score: HealthScore;
  historical_metrics: any[];
  predictions: Prediction;
  trends: {
    cpu_trend: {
      direction: string;
      average: number;
      volatility: string;
    };
    memory_trend: {
      direction: string;
      average: number;
      volatility: string;
    };
    overall_stability: string;
  };
  visualization_config: {
    chart_type: string;
    refresh_interval: number;
    show_predictions: boolean;
  };
}

const ContainerMetricsVisualization: React.FC<
  ContainerMetricsVisualizationProps
> = ({ containerId, autoRefresh = true, refreshInterval = 30000 }) => {
  const theme = useTheme();
  const [timeRange, setTimeRange] = useState("24h");
  const [showPredictions, setShowPredictions] = useState(true);
  const [realTimeEnabled, setRealTimeEnabled] = useState(autoRefresh);

  // API calls
  const {
    data: enhancedMetrics,
    loading: metricsLoading,
    error: metricsError,
    execute: fetchEnhancedMetrics,
  } = useApiCall<EnhancedMetrics>();

  const {
    data: healthScore,
    loading: healthLoading,
    execute: fetchHealthScore,
  } = useApiCall<HealthScore>();

  const {
    data: predictions,
    loading: predictionsLoading,
    execute: fetchPredictions,
  } = useApiCall<Prediction>();

  // Fetch data
  const fetchData = useCallback(async () => {
    if (!containerId) return;

    try {
      // Fetch enhanced metrics
      await fetchEnhancedMetrics(
        `/api/containers/${containerId}/metrics/visualization?time_range=${timeRange}&hours=${getHoursFromTimeRange(timeRange)}`
      );

      // Fetch health score
      await fetchHealthScore(
        `/api/containers/${containerId}/health-score?hours=1`
      );

      // Fetch predictions if enabled
      if (showPredictions) {
        await fetchPredictions(
          `/api/containers/${containerId}/metrics/predictions?hours=24&prediction_hours=6`
        );
      }
    } catch (error) {
      console.error("Error fetching metrics data:", error);
    }
  }, [
    containerId,
    timeRange,
    showPredictions,
    fetchEnhancedMetrics,
    fetchHealthScore,
    fetchPredictions,
  ]);

  // Auto-refresh effect
  useEffect(() => {
    fetchData();

    if (realTimeEnabled) {
      const interval = setInterval(fetchData, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [fetchData, realTimeEnabled, refreshInterval]);

  const getHoursFromTimeRange = (range: string): number => {
    switch (range) {
      case "1h":
        return 1;
      case "6h":
        return 6;
      case "24h":
        return 24;
      case "7d":
        return 168;
      case "30d":
        return 720;
      default:
        return 24;
    }
  };

  const getHealthColor = (score: number): string => {
    if (score >= 80) return theme.palette.success.main;
    if (score >= 60) return theme.palette.warning.main;
    return theme.palette.error.main;
  };

  const getHealthIcon = (status: string) => {
    switch (status) {
      case "excellent":
        return (
          <HealthAndSafetyIcon sx={{ color: theme.palette.success.main }} />
        );
      case "good":
        return <HealthAndSafetyIcon sx={{ color: theme.palette.info.main }} />;
      case "warning":
        return (
          <HealthAndSafetyIcon sx={{ color: theme.palette.warning.main }} />
        );
      case "critical":
        return <HealthAndSafetyIcon sx={{ color: theme.palette.error.main }} />;
      default:
        return <HealthAndSafetyIcon />;
    }
  };

  const getTrendIcon = (direction: string) => {
    switch (direction) {
      case "increasing":
        return <TrendingUpIcon sx={{ color: theme.palette.error.main }} />;
      case "decreasing":
        return <TrendingDownIcon sx={{ color: theme.palette.success.main }} />;
      case "stable":
        return <TrendingFlatIcon sx={{ color: theme.palette.info.main }} />;
      default:
        return <TrendingFlatIcon />;
    }
  };

  const formatChartData = (metrics: any[]): MetricDataPoint[] => {
    if (!metrics || !Array.isArray(metrics)) return [];

    return metrics.map((metric) => ({
      timestamp: metric.timestamp,
      value: metric.cpu_percent || 0,
    }));
  };

  const formatMemoryChartData = (metrics: any[]): MetricDataPoint[] => {
    if (!metrics || !Array.isArray(metrics)) return [];

    return metrics.map((metric) => ({
      timestamp: metric.timestamp,
      value: metric.memory_percent || 0,
    }));
  };

  const formatPredictionData = (
    prediction: Prediction | null
  ): MetricDataPoint[] => {
    if (!prediction?.cpu_percent?.values) return [];

    return prediction.cpu_percent.values.map((value, index) => ({
      timestamp: prediction.cpu_percent.timestamps[index] || "",
      value: value,
    }));
  };

  if (metricsError) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        Failed to load metrics visualization: {metricsError}
      </Alert>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header Controls */}
      <Box
        display="flex"
        justifyContent="space-between"
        alignItems="center"
        mb={3}
      >
        <Typography variant="h5" component="h1">
          Container Metrics Visualization
        </Typography>

        <Box display="flex" gap={2} alignItems="center">
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Time Range</InputLabel>
            <Select
              value={timeRange}
              label="Time Range"
              onChange={(e) => setTimeRange(e.target.value)}
            >
              <MenuItem value="1h">1 Hour</MenuItem>
              <MenuItem value="6h">6 Hours</MenuItem>
              <MenuItem value="24h">24 Hours</MenuItem>
              <MenuItem value="7d">7 Days</MenuItem>
              <MenuItem value="30d">30 Days</MenuItem>
            </Select>
          </FormControl>

          <FormControlLabel
            control={
              <Switch
                checked={showPredictions}
                onChange={(e) => setShowPredictions(e.target.checked)}
              />
            }
            label="Predictions"
          />

          <FormControlLabel
            control={
              <Switch
                checked={realTimeEnabled}
                onChange={(e) => setRealTimeEnabled(e.target.checked)}
              />
            }
            label="Auto Refresh"
          />

          <Tooltip title="Refresh Data">
            <span>
              <IconButton onClick={fetchData} disabled={metricsLoading}>
                <RefreshIcon />
              </IconButton>
            </span>
          </Tooltip>
        </Box>
      </Box>

      {/* Health Score Card */}
      {healthScore && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box display="flex" alignItems="center" gap={2} mb={2}>
              {getHealthIcon(healthScore.health_status)}
              <Typography variant="h6">Container Health Score</Typography>
              <Chip
                label={`${healthScore.overall_health_score}/100`}
                color={
                  healthScore.overall_health_score >= 80
                    ? "success"
                    : healthScore.overall_health_score >= 60
                      ? "warning"
                      : "error"
                }
                variant="outlined"
              />
            </Box>

            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Box>
                  <Typography
                    variant="body2"
                    color="text.secondary"
                    gutterBottom
                  >
                    Component Health Scores
                  </Typography>

                  {Object.entries(healthScore.component_scores).map(
                    ([component, score]) => (
                      <Box key={component} sx={{ mb: 1 }}>
                        <Box
                          display="flex"
                          justifyContent="space-between"
                          alignItems="center"
                        >
                          <Typography
                            variant="body2"
                            sx={{ textTransform: "capitalize" }}
                          >
                            {component.replace("_", " ")}
                          </Typography>
                          <Typography variant="body2" fontWeight="bold">
                            {score}/100
                          </Typography>
                        </Box>
                        <LinearProgress
                          variant="determinate"
                          value={score}
                          sx={{
                            height: 6,
                            borderRadius: 3,
                            backgroundColor: theme.palette.grey[200],
                            "& .MuiLinearProgress-bar": {
                              backgroundColor: getHealthColor(score),
                            },
                          }}
                        />
                      </Box>
                    )
                  )}
                </Box>
              </Grid>

              <Grid item xs={12} md={6}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Recommendations
                </Typography>
                {healthScore.recommendations.map((recommendation, index) => (
                  <Typography key={index} variant="body2" sx={{ mb: 1 }}>
                    • {recommendation}
                  </Typography>
                ))}
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Performance Trends */}
      {enhancedMetrics?.trends && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Performance Trends
            </Typography>

            <Grid container spacing={3}>
              <Grid item xs={12} md={4}>
                <Box display="flex" alignItems="center" gap={1}>
                  {getTrendIcon(enhancedMetrics.trends.cpu_trend.direction)}
                  <Typography variant="body2">
                    CPU Trend: {enhancedMetrics.trends.cpu_trend.direction}
                  </Typography>
                </Box>
                <Typography variant="body2" color="text.secondary">
                  Average:{" "}
                  {formatPercentage(enhancedMetrics.trends.cpu_trend.average)}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Volatility: {enhancedMetrics.trends.cpu_trend.volatility}
                </Typography>
              </Grid>

              <Grid item xs={12} md={4}>
                <Box display="flex" alignItems="center" gap={1}>
                  {getTrendIcon(enhancedMetrics.trends.memory_trend.direction)}
                  <Typography variant="body2">
                    Memory Trend:{" "}
                    {enhancedMetrics.trends.memory_trend.direction}
                  </Typography>
                </Box>
                <Typography variant="body2" color="text.secondary">
                  Average:{" "}
                  {formatPercentage(
                    enhancedMetrics.trends.memory_trend.average
                  )}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Volatility: {enhancedMetrics.trends.memory_trend.volatility}
                </Typography>
              </Grid>

              <Grid item xs={12} md={4}>
                <Typography variant="body2">
                  Overall Stability: {enhancedMetrics.trends.overall_stability}
                </Typography>
                <Chip
                  label={enhancedMetrics.trends.overall_stability}
                  color={
                    enhancedMetrics.trends.overall_stability === "excellent"
                      ? "success"
                      : enhancedMetrics.trends.overall_stability === "good"
                        ? "info"
                        : enhancedMetrics.trends.overall_stability === "fair"
                          ? "warning"
                          : "error"
                  }
                  size="small"
                  sx={{ mt: 1 }}
                />
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Prediction Alerts */}
      {predictions?.alerts && predictions.alerts.length > 0 && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          <Typography variant="body2" fontWeight="bold" gutterBottom>
            Prediction Alerts:
          </Typography>
          {predictions.alerts.map((alert, index) => (
            <Typography key={index} variant="body2">
              • {alert.message}
            </Typography>
          ))}
        </Alert>
      )}

      {/* Charts Grid */}
      {enhancedMetrics?.historical_metrics && (
        <Grid container spacing={3}>
          {/* CPU Usage Chart */}
          <Grid item xs={12} md={6}>
            <MetricsChart
              title="CPU Usage History"
              data={formatChartData(enhancedMetrics.historical_metrics)}
              type="area"
              color={theme.palette.error.main}
              unit="%"
              formatValue={formatPercentage}
              loading={metricsLoading}
              height={350}
            />
          </Grid>

          {/* Memory Usage Chart */}
          <Grid item xs={12} md={6}>
            <MetricsChart
              title="Memory Usage History"
              data={formatMemoryChartData(enhancedMetrics.historical_metrics)}
              type="area"
              color={theme.palette.warning.main}
              unit="%"
              formatValue={formatPercentage}
              loading={metricsLoading}
              height={350}
            />
          </Grid>

          {/* CPU Predictions Chart */}
          {showPredictions && predictions && (
            <Grid item xs={12} md={6}>
              <Paper elevation={2} sx={{ p: 2, height: 350 }}>
                <Box display="flex" alignItems="center" gap={1} mb={2}>
                  <PredictionsIcon />
                  <Typography variant="h6">CPU Usage Predictions</Typography>
                  <Chip
                    label={`${Math.round(predictions.cpu_percent.confidence * 100)}% confidence`}
                    size="small"
                    color={
                      predictions.cpu_percent.confidence > 0.7
                        ? "success"
                        : "warning"
                    }
                  />
                </Box>

                <MetricsChart
                  title=""
                  data={formatPredictionData(predictions)}
                  type="line"
                  color={theme.palette.info.main}
                  unit="%"
                  formatValue={formatPercentage}
                  loading={predictionsLoading}
                  height={280}
                />
              </Paper>
            </Grid>
          )}

          {/* Memory Predictions Chart */}
          {showPredictions && predictions && (
            <Grid item xs={12} md={6}>
              <Paper elevation={2} sx={{ p: 2, height: 350 }}>
                <Box display="flex" alignItems="center" gap={1} mb={2}>
                  <PredictionsIcon />
                  <Typography variant="h6">Memory Usage Predictions</Typography>
                  <Chip
                    label={`${Math.round(predictions.memory_percent.confidence * 100)}% confidence`}
                    size="small"
                    color={
                      predictions.memory_percent.confidence > 0.7
                        ? "success"
                        : "warning"
                    }
                  />
                </Box>

                <MetricsChart
                  title=""
                  data={predictions.memory_percent.values.map(
                    (value, index) => ({
                      timestamp:
                        predictions.memory_percent.timestamps[index] || "",
                      value: value,
                    })
                  )}
                  type="line"
                  color={theme.palette.secondary.main}
                  unit="%"
                  formatValue={formatPercentage}
                  loading={predictionsLoading}
                  height={280}
                />
              </Paper>
            </Grid>
          )}
        </Grid>
      )}

      {/* Loading State */}
      {(metricsLoading || healthLoading) && (
        <Box
          display="flex"
          justifyContent="center"
          alignItems="center"
          minHeight={200}
        >
          <CircularProgress />
        </Box>
      )}
    </Box>
  );
};

export default ContainerMetricsVisualization;
