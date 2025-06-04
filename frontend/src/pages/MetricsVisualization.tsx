import React, { useState, useEffect, useCallback } from "react";
import {
  Box,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  Chip,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Alert,
  CircularProgress,
  Tooltip,
  IconButton,
  Divider,
  LinearProgress,
} from "@mui/material";
import {
  Refresh as RefreshIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  TrendingFlat as TrendingFlatIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  Settings as SettingsIcon,
} from "@mui/icons-material";
import { useTheme } from "@mui/material/styles";
import { useApiCall } from "../hooks/useApiCall";
import { useWebSocket } from "../hooks/useWebSocket";
import { getMetricsWebSocketUrl } from "../utils/websocket";
import MetricsChart from "../components/MetricsChart";
import { formatBytes, formatPercentage } from "../utils/formatters";

interface ContainerMetrics {
  container_id: string;
  container_name: string;
  cpu_percent: number;
  memory_percent: number;
  memory_usage: number;
  memory_limit: number;
  network_rx_bytes: number;
  network_tx_bytes: number;
  block_read_bytes: number;
  block_write_bytes: number;
  status: string;
  timestamp: string;
}

interface AggregatedMetrics {
  timestamp: string;
  container_count: number;
  total_containers: number;
  aggregated_metrics: {
    avg_cpu_percent: number;
    total_memory_usage: number;
    total_memory_limit: number;
    avg_memory_percent: number;
    total_network_rx_bytes: number;
    total_network_tx_bytes: number;
    total_block_read_bytes: number;
    total_block_write_bytes: number;
  };
  individual_stats: Record<string, ContainerMetrics>;
}

interface MetricsTrends {
  container_id: string;
  metric_type: string;
  analysis_period_hours: number;
  data_points: number;
  statistics: {
    average: number;
    minimum: number;
    maximum: number;
    volatility: number;
  };
  trend: {
    direction: "increasing" | "decreasing" | "stable";
    slope: number;
    strength: "high" | "medium" | "low";
  };
  recent_values: number[];
  timestamps: string[];
}

interface MetricsSummary {
  timestamp: string;
  summary: {
    total_containers: number;
    healthy_containers: number;
    warning_containers: number;
    critical_containers: number;
  };
  aggregated_metrics: {
    avg_cpu_percent: number;
    avg_memory_percent: number;
  };
  alerts: {
    high_cpu_containers: Array<{
      container_id: string;
      container_name: string;
      cpu_percent: number;
    }>;
    high_memory_containers: Array<{
      container_id: string;
      container_name: string;
      memory_percent: number;
    }>;
  };
  health_scores: Record<string, number>;
  individual_metrics: Record<string, ContainerMetrics>;
}

interface HealthScoreCardProps {
  score: number;
  containerName: string;
  containerId: string;
}

const HealthScoreCard: React.FC<HealthScoreCardProps> = ({
  score,
  containerName,
  containerId,
}) => {
  const getHealthColor = (score: number) => {
    if (score >= 80) return "success";
    if (score >= 60) return "warning";
    return "error";
  };

  const getHealthIcon = (score: number) => {
    if (score >= 80) return <CheckCircleIcon color="success" />;
    if (score >= 60) return <WarningIcon color="warning" />;
    return <ErrorIcon color="error" />;
  };

  return (
    <Card sx={{ height: "100%" }}>
      <CardContent>
        <Box
          display="flex"
          alignItems="center"
          justifyContent="space-between"
          mb={1}
        >
          <Typography variant="subtitle2" noWrap>
            {containerName}
          </Typography>
          {getHealthIcon(score)}
        </Box>
        <Typography
          variant="h4"
          color={`${getHealthColor(score)}.main`}
          gutterBottom
        >
          {score}
        </Typography>
        <LinearProgress
          variant="determinate"
          value={score}
          color={getHealthColor(score)}
          sx={{ height: 8, borderRadius: 4 }}
        />
        <Typography
          variant="caption"
          color="textSecondary"
          sx={{ mt: 1, display: "block" }}
        >
          Health Score
        </Typography>
      </CardContent>
    </Card>
  );
};

interface TrendIndicatorProps {
  trend: MetricsTrends["trend"];
  value: number;
  unit?: string;
}

const TrendIndicator: React.FC<TrendIndicatorProps> = ({
  trend,
  value,
  unit = "",
}) => {
  const getTrendIcon = () => {
    switch (trend.direction) {
      case "increasing":
        return <TrendingUpIcon color="error" />;
      case "decreasing":
        return <TrendingDownIcon color="success" />;
      default:
        return <TrendingFlatIcon color="info" />;
    }
  };

  const getTrendColor = () => {
    switch (trend.direction) {
      case "increasing":
        return "error";
      case "decreasing":
        return "success";
      default:
        return "info";
    }
  };

  return (
    <Box display="flex" alignItems="center" gap={1}>
      <Tooltip title={`${trend.direction} trend (${trend.strength} strength)`}>
        {getTrendIcon()}
      </Tooltip>
      <Typography variant="body2" color={`${getTrendColor()}.main`}>
        {value.toFixed(2)}
        {unit}
      </Typography>
      <Chip
        label={trend.strength}
        size="small"
        color={getTrendColor()}
        variant="outlined"
      />
    </Box>
  );
};

const MetricsVisualization: React.FC = () => {
  const theme = useTheme();
  const [selectedContainers, setSelectedContainers] = useState<string[]>([]);
  const [realTimeEnabled, setRealTimeEnabled] = useState(true);
  const [timeRange, setTimeRange] = useState(24); // hours
  const [metricType, setMetricType] = useState("cpu_percent");
  const [refreshInterval, setRefreshInterval] = useState(5000); // ms

  // API calls
  const {
    data: containers,
    loading: containersLoading,
    execute: fetchContainers,
  } = useApiCall();
  const {
    data: metricsSummary,
    loading: summaryLoading,
    execute: fetchMetricsSummary,
  } = useApiCall();
  const {
    data: aggregatedMetrics,
    loading: aggregatedLoading,
    execute: fetchAggregatedMetrics,
  } = useApiCall();
  const {
    data: metricsTrends,
    loading: trendsLoading,
    execute: fetchMetricsTrends,
  } = useApiCall();

  // WebSocket for real-time updates
  const wsUrl =
    realTimeEnabled && selectedContainers.length > 0
      ? getMetricsWebSocketUrl(localStorage.getItem("token") || "")
      : null;

  const [realTimeData, setRealTimeData] = useState<
    Record<string, ContainerMetrics>
  >({});

  const { isConnected, sendMessage, connectionState } = useWebSocket(wsUrl, {
    onMessage: (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "multiple_metrics_update") {
          setRealTimeData(data.metrics);
        }
      } catch (error) {
        console.error("Error parsing WebSocket message:", error);
      }
    },
    onConnect: () => {
      console.log("Connected to metrics WebSocket");
      if (selectedContainers.length > 0) {
        sendMessage({
          type: "subscribe",
          container_ids: selectedContainers,
        });
      }
    },
    onError: (error) => {
      console.error("WebSocket error:", error);
    },
  });

  // Fetch initial data
  useEffect(() => {
    fetchContainers("/api/containers");
    fetchMetricsSummary("/api/metrics/summary");
  }, []);

  // Update WebSocket subscription when containers change
  useEffect(() => {
    if (isConnected && selectedContainers.length > 0) {
      sendMessage({
        type: "subscribe",
        container_ids: selectedContainers,
      });
    }
  }, [selectedContainers, isConnected, sendMessage]);

  // Fetch aggregated metrics when containers are selected
  useEffect(() => {
    if (selectedContainers.length > 0) {
      fetchAggregatedMetrics(
        `/api/containers/metrics/aggregated?container_ids=${selectedContainers.join(",")}`
      );
    }
  }, [selectedContainers]);

  // Fetch trends for selected metric type
  useEffect(() => {
    if (selectedContainers.length > 0) {
      selectedContainers.forEach((containerId) => {
        fetchMetricsTrends(
          `/api/containers/${containerId}/metrics/trends?hours=${timeRange}&metric_type=${metricType}`
        );
      });
    }
  }, [selectedContainers, timeRange, metricType]);

  const handleContainerSelection = useCallback((containerId: string) => {
    setSelectedContainers((prev) => {
      if (prev.includes(containerId)) {
        return prev.filter((id) => id !== containerId);
      } else {
        return [...prev, containerId];
      }
    });
  }, []);

  const handleRefresh = useCallback(() => {
    fetchMetricsSummary("/api/metrics/summary");
    if (selectedContainers.length > 0) {
      fetchAggregatedMetrics(
        `/api/containers/metrics/aggregated?container_ids=${selectedContainers.join(",")}`
      );
    }
  }, [selectedContainers]);

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
        <Box
          display="flex"
          justifyContent="space-between"
          alignItems="center"
          mb={2}
        >
          <Typography variant="h4">Advanced Metrics Visualization</Typography>
          <Box display="flex" gap={2} alignItems="center">
            <FormControlLabel
              control={
                <Switch
                  checked={realTimeEnabled}
                  onChange={(e) => setRealTimeEnabled(e.target.checked)}
                />
              }
              label="Real-time Updates"
            />
            <Tooltip title="Refresh Data">
              <IconButton onClick={handleRefresh} disabled={summaryLoading}>
                <RefreshIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        {/* Connection Status */}
        {realTimeEnabled && (
          <Box display="flex" alignItems="center" gap={1} mb={2}>
            <Typography variant="body2" color="textSecondary">
              WebSocket Status:
            </Typography>
            <Chip
              label={connectionState}
              color={isConnected ? "success" : "error"}
              size="small"
              variant="outlined"
            />
          </Box>
        )}

        {/* Controls */}
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth size="small">
              <InputLabel>Time Range</InputLabel>
              <Select
                value={timeRange}
                label="Time Range"
                onChange={(e) => setTimeRange(Number(e.target.value))}
              >
                <MenuItem value={1}>Last Hour</MenuItem>
                <MenuItem value={6}>Last 6 Hours</MenuItem>
                <MenuItem value={24}>Last 24 Hours</MenuItem>
                <MenuItem value={168}>Last Week</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth size="small">
              <InputLabel>Metric Type</InputLabel>
              <Select
                value={metricType}
                label="Metric Type"
                onChange={(e) => setMetricType(e.target.value)}
              >
                <MenuItem value="cpu_percent">CPU Usage</MenuItem>
                <MenuItem value="memory_percent">Memory Usage</MenuItem>
                <MenuItem value="network_rx_bytes">Network RX</MenuItem>
                <MenuItem value="network_tx_bytes">Network TX</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>
      </Paper>

      {/* Loading State */}
      {summaryLoading && (
        <Box display="flex" justifyContent="center" p={4}>
          <CircularProgress />
        </Box>
      )}

      {/* Error State */}
      {!summaryLoading && !metricsSummary && (
        <Alert severity="error" sx={{ mb: 3 }}>
          Failed to load metrics data. Please try refreshing the page.
        </Alert>
      )}

      {/* Content */}
      {metricsSummary && (
        <Grid container spacing={3}>
          {/* System Overview */}
          <Grid item xs={12}>
            <Paper elevation={2} sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                System Overview
              </Typography>
              <Grid container spacing={3}>
                <Grid item xs={12} sm={6} md={3}>
                  <Card>
                    <CardContent>
                      <Typography variant="h4" color="primary">
                        {metricsSummary.summary.total_containers}
                      </Typography>
                      <Typography color="textSecondary">
                        Total Containers
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Card>
                    <CardContent>
                      <Typography variant="h4" color="success.main">
                        {metricsSummary.summary.healthy_containers}
                      </Typography>
                      <Typography color="textSecondary">
                        Healthy Containers
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Card>
                    <CardContent>
                      <Typography variant="h4" color="warning.main">
                        {metricsSummary.summary.warning_containers}
                      </Typography>
                      <Typography color="textSecondary">
                        Warning Containers
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Card>
                    <CardContent>
                      <Typography variant="h4" color="error.main">
                        {metricsSummary.summary.critical_containers}
                      </Typography>
                      <Typography color="textSecondary">
                        Critical Containers
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            </Paper>
          </Grid>

          {/* Health Scores */}
          <Grid item xs={12}>
            <Paper elevation={2} sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Container Health Scores
              </Typography>
              <Grid container spacing={2}>
                {Object.entries(metricsSummary.health_scores).map(
                  ([containerId, score]) => {
                    const containerMetrics =
                      metricsSummary.individual_metrics[containerId];
                    return (
                      <Grid item xs={12} sm={6} md={4} lg={3} key={containerId}>
                        <HealthScoreCard
                          score={score}
                          containerName={
                            containerMetrics?.container_name || containerId
                          }
                          containerId={containerId}
                        />
                      </Grid>
                    );
                  }
                )}
              </Grid>
            </Paper>
          </Grid>

          {/* Container Selection */}
          <Grid item xs={12}>
            <Paper elevation={2} sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Select Containers for Detailed Analysis
              </Typography>
              <Grid container spacing={1}>
                {Object.entries(metricsSummary.individual_metrics).map(
                  ([containerId, metrics]) => (
                    <Grid item key={containerId}>
                      <Chip
                        label={metrics.container_name || containerId}
                        onClick={() => handleContainerSelection(containerId)}
                        color={
                          selectedContainers.includes(containerId)
                            ? "primary"
                            : "default"
                        }
                        variant={
                          selectedContainers.includes(containerId)
                            ? "filled"
                            : "outlined"
                        }
                        clickable
                      />
                    </Grid>
                  )
                )}
              </Grid>
            </Paper>
          </Grid>

          {/* Alerts */}
          {(metricsSummary.alerts.high_cpu_containers.length > 0 ||
            metricsSummary.alerts.high_memory_containers.length > 0) && (
            <Grid item xs={12}>
              <Paper elevation={2} sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom color="error">
                  Active Alerts
                </Typography>
                <Grid container spacing={2}>
                  {metricsSummary.alerts.high_cpu_containers.length > 0 && (
                    <Grid item xs={12} md={6}>
                      <Alert severity="error" sx={{ mb: 2 }}>
                        <Typography variant="subtitle2" gutterBottom>
                          High CPU Usage Containers
                        </Typography>
                        {metricsSummary.alerts.high_cpu_containers.map(
                          (container) => (
                            <Typography
                              key={container.container_id}
                              variant="body2"
                            >
                              {container.container_name}:{" "}
                              {container.cpu_percent.toFixed(1)}%
                            </Typography>
                          )
                        )}
                      </Alert>
                    </Grid>
                  )}
                  {metricsSummary.alerts.high_memory_containers.length > 0 && (
                    <Grid item xs={12} md={6}>
                      <Alert severity="warning" sx={{ mb: 2 }}>
                        <Typography variant="subtitle2" gutterBottom>
                          High Memory Usage Containers
                        </Typography>
                        {metricsSummary.alerts.high_memory_containers.map(
                          (container) => (
                            <Typography
                              key={container.container_id}
                              variant="body2"
                            >
                              {container.container_name}:{" "}
                              {container.memory_percent.toFixed(1)}%
                            </Typography>
                          )
                        )}
                      </Alert>
                    </Grid>
                  )}
                </Grid>
              </Paper>
            </Grid>
          )}

          {/* Aggregated Metrics Charts */}
          {selectedContainers.length > 0 && aggregatedMetrics && (
            <Grid item xs={12}>
              <Paper elevation={2} sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Aggregated Metrics for Selected Containers
                </Typography>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <Card>
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          Average CPU Usage
                        </Typography>
                        <Typography variant="h3" color="error.main">
                          {aggregatedMetrics.aggregated_metrics.avg_cpu_percent.toFixed(
                            1
                          )}
                          %
                        </Typography>
                        <Typography variant="body2" color="textSecondary">
                          Across {aggregatedMetrics.container_count} containers
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Card>
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          Average Memory Usage
                        </Typography>
                        <Typography variant="h3" color="warning.main">
                          {aggregatedMetrics.aggregated_metrics.avg_memory_percent.toFixed(
                            1
                          )}
                          %
                        </Typography>
                        <Typography variant="body2" color="textSecondary">
                          {formatBytes(
                            aggregatedMetrics.aggregated_metrics
                              .total_memory_usage
                          )}{" "}
                          /{" "}
                          {formatBytes(
                            aggregatedMetrics.aggregated_metrics
                              .total_memory_limit
                          )}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>
              </Paper>
            </Grid>
          )}

          {/* Real-time Data Display */}
          {realTimeEnabled && Object.keys(realTimeData).length > 0 && (
            <Grid item xs={12}>
              <Paper elevation={2} sx={{ p: 3 }}>
                <Box display="flex" alignItems="center" gap={1} mb={2}>
                  <Typography variant="h6">Real-time Metrics</Typography>
                  <Chip
                    label="LIVE"
                    color="success"
                    size="small"
                    variant="filled"
                  />
                </Box>
                <Grid container spacing={2}>
                  {Object.entries(realTimeData).map(
                    ([containerId, metrics]) => (
                      <Grid item xs={12} sm={6} md={4} key={containerId}>
                        <Card>
                          <CardContent>
                            <Typography variant="subtitle2" gutterBottom noWrap>
                              {metrics.container_name}
                            </Typography>
                            <Box
                              display="flex"
                              justifyContent="space-between"
                              mb={1}
                            >
                              <Typography variant="body2">CPU:</Typography>
                              <Typography variant="body2" color="error.main">
                                {metrics.cpu_percent.toFixed(1)}%
                              </Typography>
                            </Box>
                            <Box
                              display="flex"
                              justifyContent="space-between"
                              mb={1}
                            >
                              <Typography variant="body2">Memory:</Typography>
                              <Typography variant="body2" color="warning.main">
                                {metrics.memory_percent.toFixed(1)}%
                              </Typography>
                            </Box>
                            <Box display="flex" justifyContent="space-between">
                              <Typography variant="body2">Status:</Typography>
                              <Chip
                                label={metrics.status}
                                size="small"
                                color={
                                  metrics.status === "running"
                                    ? "success"
                                    : "error"
                                }
                                variant="outlined"
                              />
                            </Box>
                          </CardContent>
                        </Card>
                      </Grid>
                    )
                  )}
                </Grid>
              </Paper>
            </Grid>
          )}

          {/* Trends Analysis */}
          {metricsTrends && selectedContainers.length > 0 && (
            <Grid item xs={12}>
              <Paper elevation={2} sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Trends Analysis - {metricType.replace("_", " ").toUpperCase()}
                </Typography>
                {trendsLoading ? (
                  <Box display="flex" justifyContent="center" p={4}>
                    <CircularProgress />
                  </Box>
                ) : (
                  <Grid container spacing={2}>
                    {selectedContainers.map((containerId) => {
                      const containerMetrics =
                        metricsSummary.individual_metrics[containerId];
                      const currentValue =
                        (containerMetrics?.[
                          metricType as keyof ContainerMetrics
                        ] as number) || 0;

                      return (
                        <Grid item xs={12} sm={6} md={4} key={containerId}>
                          <Card>
                            <CardContent>
                              <Typography
                                variant="subtitle2"
                                gutterBottom
                                noWrap
                              >
                                {containerMetrics?.container_name ||
                                  containerId}
                              </Typography>
                              <TrendIndicator
                                trend={{
                                  direction:
                                    currentValue > 50
                                      ? "increasing"
                                      : currentValue > 20
                                        ? "stable"
                                        : "decreasing",
                                  slope: 0.1,
                                  strength: "medium",
                                }}
                                value={currentValue}
                                unit={metricType.includes("percent") ? "%" : ""}
                              />
                              <Typography
                                variant="caption"
                                color="textSecondary"
                                sx={{ mt: 1, display: "block" }}
                              >
                                Last {timeRange} hours analysis
                              </Typography>
                            </CardContent>
                          </Card>
                        </Grid>
                      );
                    })}
                  </Grid>
                )}
              </Paper>
            </Grid>
          )}
        </Grid>
      )}
    </Box>
  );
};

export default MetricsVisualization;
