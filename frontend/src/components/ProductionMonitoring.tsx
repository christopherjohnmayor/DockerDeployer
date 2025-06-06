import React, { useState, useEffect, useCallback } from "react";
import {
  Box,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  Alert,
  CircularProgress,
  Chip,
  LinearProgress,
  IconButton,
  Tooltip,
  Switch,
  FormControlLabel,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Badge,
} from "@mui/material";
import {
  Dashboard as DashboardIcon,
  Speed as SpeedIcon,
  Memory as MemoryIcon,
  Storage as StorageIcon,
  NetworkCheck as NetworkIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  CheckCircle as CheckCircleIcon,
  Refresh as RefreshIcon,
  Timeline as TimelineIcon,
  Notifications as NotificationsIcon,
} from "@mui/icons-material";
import { useTheme } from "@mui/material/styles";
import { useApiCall } from "../hooks/useApiCall";
import { useWebSocket } from "../hooks/useWebSocket";
import { formatBytes, formatPercentage } from "../utils/formatters";

interface ProductionMetrics {
  timestamp: string;
  api_performance: {
    avg_response_time: number;
    p95_response_time: number;
    p99_response_time: number;
    requests_per_minute: number;
    error_rate: number;
  };
  system_health: {
    cpu_usage: number;
    memory_usage: number;
    disk_usage: number;
    network_latency: number;
    uptime_percentage: number;
  };
  container_metrics: {
    total_containers: number;
    running_containers: number;
    failed_containers: number;
    resource_alerts: number;
  };
  alerts: Array<{
    id: string;
    type: "warning" | "error" | "info";
    message: string;
    timestamp: string;
    container_id?: string;
  }>;
  health_score: number;
}

interface ProductionMonitoringProps {
  autoRefresh?: boolean;
  refreshInterval?: number;
}

const ProductionMonitoring: React.FC<ProductionMonitoringProps> = ({
  autoRefresh = true,
  refreshInterval = 30000,
}) => {
  const theme = useTheme();
  const [realTimeEnabled, setRealTimeEnabled] = useState(autoRefresh);
  const [alertsCount, setAlertsCount] = useState(0);

  // API calls
  const {
    data: productionMetrics,
    loading: metricsLoading,
    error: metricsError,
    execute: fetchProductionMetrics,
  } = useApiCall();

  const {
    data: systemHealth,
    loading: healthLoading,
    execute: fetchSystemHealth,
  } = useApiCall();

  // WebSocket for real-time production monitoring
  const wsUrl = realTimeEnabled
    ? `ws://localhost:8000/ws/notifications/${localStorage.getItem("userId")}?token=${localStorage.getItem("token")}`
    : null;

  const { isConnected, connectionState } = useWebSocket(wsUrl, {
    onMessage: (event) => {
      try {
        const data = JSON.parse(event.data);
        if (
          data.type === "production_alert" ||
          data.type === "system_health_update"
        ) {
          // Refresh production metrics when receiving critical updates
          fetchProductionMetrics("/api/production/metrics");
          fetchSystemHealth("/api/system/health");

          // Update alerts count
          if (data.type === "production_alert") {
            setAlertsCount((prev) => prev + 1);
          }
        }
      } catch (error) {
        console.error("Error parsing WebSocket message:", error);
      }
    },
    onConnect: () => {
      console.log("Connected to production monitoring WebSocket");
    },
    onError: (error) => {
      console.error("Production monitoring WebSocket error:", error);
    },
  });

  // Fetch initial data
  useEffect(() => {
    fetchProductionMetrics("/api/production/metrics");
    fetchSystemHealth("/api/system/health");
  }, []);

  // Auto-refresh data
  useEffect(() => {
    if (!realTimeEnabled) return;

    const interval = setInterval(() => {
      fetchProductionMetrics("/api/production/metrics");
      fetchSystemHealth("/api/system/health");
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [realTimeEnabled, refreshInterval]);

  const handleRefresh = useCallback(() => {
    fetchProductionMetrics("/api/production/metrics");
    fetchSystemHealth("/api/system/health");
    setAlertsCount(0); // Reset alerts count on manual refresh
  }, []);

  const getHealthColor = (score: number) => {
    if (score >= 90) return theme.palette.success.main;
    if (score >= 70) return theme.palette.warning.main;
    return theme.palette.error.main;
  };

  const getHealthLabel = (score: number) => {
    if (score >= 90) return "Excellent";
    if (score >= 70) return "Good";
    if (score >= 50) return "Warning";
    return "Critical";
  };

  const getResponseTimeColor = (responseTime: number) => {
    if (responseTime <= 200) return theme.palette.success.main;
    if (responseTime <= 500) return theme.palette.warning.main;
    return theme.palette.error.main;
  };

  const getAlertIcon = (type: string) => {
    switch (type) {
      case "error":
        return <ErrorIcon color="error" />;
      case "warning":
        return <WarningIcon color="warning" />;
      default:
        return <CheckCircleIcon color="info" />;
    }
  };

  return (
    <Box sx={{ width: "100%" }}>
      {/* Header */}
      <Paper elevation={2} sx={{ p: 2, mb: 3 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Box display="flex" alignItems="center" gap={2}>
            <DashboardIcon color="primary" />
            <Typography variant="h5">Production Monitoring</Typography>
            {realTimeEnabled && (
              <Chip
                label={isConnected ? "LIVE" : "CONNECTING"}
                color={isConnected ? "success" : "warning"}
                size="small"
                variant="filled"
              />
            )}
            {alertsCount > 0 && (
              <Badge badgeContent={alertsCount} color="error">
                <NotificationsIcon color="action" />
              </Badge>
            )}
          </Box>

          <Box display="flex" alignItems="center" gap={1}>
            <FormControlLabel
              control={
                <Switch
                  checked={realTimeEnabled}
                  onChange={(e) => setRealTimeEnabled(e.target.checked)}
                  size="small"
                />
              }
              label="Real-time"
            />
            <Tooltip title="Refresh">
              <span>
                <IconButton
                  onClick={handleRefresh}
                  disabled={metricsLoading || healthLoading}
                >
                  <RefreshIcon />
                </IconButton>
              </span>
            </Tooltip>
          </Box>
        </Box>
      </Paper>

      {/* Error Display */}
      {metricsError && (
        <Alert severity="error" sx={{ mb: 3 }}>
          Failed to load production metrics: {metricsError}
        </Alert>
      )}

      {/* Loading State */}
      {(metricsLoading || healthLoading) && (
        <Box display="flex" justifyContent="center" p={4}>
          <CircularProgress />
        </Box>
      )}

      {/* Production Metrics Dashboard */}
      {productionMetrics && (
        <Grid container spacing={3}>
          {/* Overall Health Score */}
          <Grid item xs={12} md={4}>
            <Card elevation={2}>
              <CardContent>
                <Box display="flex" alignItems="center" gap={2} mb={2}>
                  <SpeedIcon color="primary" />
                  <Typography variant="h6">System Health</Typography>
                </Box>
                <Box textAlign="center">
                  <Typography
                    variant="h2"
                    sx={{
                      color: getHealthColor(
                        productionMetrics.health_score || 0
                      ),
                    }}
                  >
                    {productionMetrics.health_score || 0}
                  </Typography>
                  <Typography variant="body1" color="textSecondary">
                    {getHealthLabel(productionMetrics.health_score || 0)}
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={productionMetrics.health_score || 0}
                    sx={{
                      mt: 2,
                      height: 8,
                      borderRadius: 4,
                      backgroundColor: theme.palette.grey[200],
                      "& .MuiLinearProgress-bar": {
                        backgroundColor: getHealthColor(
                          productionMetrics.health_score || 0
                        ),
                      },
                    }}
                  />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* API Performance */}
          <Grid item xs={12} md={8}>
            <Card elevation={2}>
              <CardContent>
                <Box display="flex" alignItems="center" gap={2} mb={2}>
                  <TimelineIcon color="primary" />
                  <Typography variant="h6">API Performance</Typography>
                </Box>
                <Grid container spacing={2}>
                  <Grid item xs={6} sm={3}>
                    <Box textAlign="center">
                      <Typography
                        variant="h5"
                        sx={{
                          color: getResponseTimeColor(
                            productionMetrics.api_performance
                              ?.avg_response_time || 0
                          ),
                        }}
                      >
                        {productionMetrics.api_performance?.avg_response_time ||
                          0}
                        ms
                      </Typography>
                      <Typography variant="caption" color="textSecondary">
                        Avg Response
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Box textAlign="center">
                      <Typography variant="h5" color="warning.main">
                        {productionMetrics.api_performance?.p95_response_time ||
                          0}
                        ms
                      </Typography>
                      <Typography variant="caption" color="textSecondary">
                        P95 Response
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Box textAlign="center">
                      <Typography variant="h5" color="primary">
                        {productionMetrics.api_performance
                          ?.requests_per_minute || 0}
                      </Typography>
                      <Typography variant="caption" color="textSecondary">
                        Requests/min
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Box textAlign="center">
                      <Typography
                        variant="h5"
                        color={
                          (productionMetrics.api_performance?.error_rate || 0) >
                          5
                            ? "error"
                            : "success"
                        }
                      >
                        {formatPercentage(
                          productionMetrics.api_performance?.error_rate || 0
                        )}
                      </Typography>
                      <Typography variant="caption" color="textSecondary">
                        Error Rate
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* System Resources and Container Status */}
      {productionMetrics && (
        <Grid container spacing={3} sx={{ mt: 1 }}>
          {/* System Resources */}
          <Grid item xs={12} md={6}>
            <Card elevation={2}>
              <CardContent>
                <Box display="flex" alignItems="center" gap={2} mb={2}>
                  <MemoryIcon color="primary" />
                  <Typography variant="h6">System Resources</Typography>
                </Box>
                <Grid container spacing={2}>
                  <Grid item xs={12}>
                    <Box mb={2}>
                      <Box display="flex" justifyContent="space-between" mb={1}>
                        <Typography variant="body2">CPU Usage</Typography>
                        <Typography variant="body2" fontWeight="bold">
                          {formatPercentage(
                            productionMetrics.system_health?.cpu_usage || 0
                          )}
                        </Typography>
                      </Box>
                      <LinearProgress
                        variant="determinate"
                        value={productionMetrics.system_health?.cpu_usage || 0}
                        sx={{
                          height: 6,
                          borderRadius: 3,
                          backgroundColor: theme.palette.grey[200],
                          "& .MuiLinearProgress-bar": {
                            backgroundColor:
                              (productionMetrics.system_health?.cpu_usage ||
                                0) > 80
                                ? theme.palette.error.main
                                : (productionMetrics.system_health?.cpu_usage ||
                                      0) > 60
                                  ? theme.palette.warning.main
                                  : theme.palette.success.main,
                          },
                        }}
                      />
                    </Box>
                  </Grid>
                  <Grid item xs={12}>
                    <Box mb={2}>
                      <Box display="flex" justifyContent="space-between" mb={1}>
                        <Typography variant="body2">Memory Usage</Typography>
                        <Typography variant="body2" fontWeight="bold">
                          {formatPercentage(
                            productionMetrics.system_health?.memory_usage || 0
                          )}
                        </Typography>
                      </Box>
                      <LinearProgress
                        variant="determinate"
                        value={
                          productionMetrics.system_health?.memory_usage || 0
                        }
                        sx={{
                          height: 6,
                          borderRadius: 3,
                          backgroundColor: theme.palette.grey[200],
                          "& .MuiLinearProgress-bar": {
                            backgroundColor:
                              (productionMetrics.system_health?.memory_usage ||
                                0) > 80
                                ? theme.palette.error.main
                                : (productionMetrics.system_health
                                      ?.memory_usage || 0) > 60
                                  ? theme.palette.warning.main
                                  : theme.palette.success.main,
                          },
                        }}
                      />
                    </Box>
                  </Grid>
                  <Grid item xs={12}>
                    <Box mb={2}>
                      <Box display="flex" justifyContent="space-between" mb={1}>
                        <Typography variant="body2">Disk Usage</Typography>
                        <Typography variant="body2" fontWeight="bold">
                          {formatPercentage(
                            productionMetrics.system_health?.disk_usage || 0
                          )}
                        </Typography>
                      </Box>
                      <LinearProgress
                        variant="determinate"
                        value={productionMetrics.system_health?.disk_usage || 0}
                        sx={{
                          height: 6,
                          borderRadius: 3,
                          backgroundColor: theme.palette.grey[200],
                          "& .MuiLinearProgress-bar": {
                            backgroundColor:
                              (productionMetrics.system_health?.disk_usage ||
                                0) > 80
                                ? theme.palette.error.main
                                : (productionMetrics.system_health
                                      ?.disk_usage || 0) > 60
                                  ? theme.palette.warning.main
                                  : theme.palette.success.main,
                          },
                        }}
                      />
                    </Box>
                  </Grid>
                  <Grid item xs={6}>
                    <Box textAlign="center">
                      <Typography variant="h6" color="info.main">
                        {productionMetrics.system_health?.network_latency || 0}
                        ms
                      </Typography>
                      <Typography variant="caption" color="textSecondary">
                        Network Latency
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={6}>
                    <Box textAlign="center">
                      <Typography variant="h6" color="success.main">
                        {formatPercentage(
                          productionMetrics.system_health?.uptime_percentage ||
                            0
                        )}
                      </Typography>
                      <Typography variant="caption" color="textSecondary">
                        Uptime
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>

          {/* Container Status */}
          <Grid item xs={12} md={6}>
            <Card elevation={2}>
              <CardContent>
                <Box display="flex" alignItems="center" gap={2} mb={2}>
                  <StorageIcon color="primary" />
                  <Typography variant="h6">Container Status</Typography>
                </Box>
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Box textAlign="center">
                      <Typography variant="h4" color="primary">
                        {productionMetrics.container_metrics
                          ?.total_containers || 0}
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        Total Containers
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={6}>
                    <Box textAlign="center">
                      <Typography variant="h4" color="success.main">
                        {productionMetrics.container_metrics
                          ?.running_containers || 0}
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        Running
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={6}>
                    <Box textAlign="center">
                      <Typography variant="h4" color="error.main">
                        {productionMetrics.container_metrics
                          ?.failed_containers || 0}
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        Failed
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={6}>
                    <Box textAlign="center">
                      <Typography variant="h4" color="warning.main">
                        {productionMetrics.container_metrics?.resource_alerts ||
                          0}
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        Resource Alerts
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Recent Alerts */}
      {productionMetrics?.alerts && productionMetrics.alerts.length > 0 && (
        <Paper elevation={2} sx={{ mt: 3, p: 2 }}>
          <Box display="flex" alignItems="center" gap={2} mb={2}>
            <WarningIcon color="warning" />
            <Typography variant="h6">Recent Alerts</Typography>
            <Chip
              label={productionMetrics.alerts.length}
              color="warning"
              size="small"
            />
          </Box>
          <Divider sx={{ mb: 2 }} />
          <List dense>
            {productionMetrics.alerts.slice(0, 5).map((alert, index) => (
              <ListItem key={alert.id || index}>
                <ListItemIcon>{getAlertIcon(alert.type)}</ListItemIcon>
                <ListItemText
                  primary={alert.message}
                  secondary={`${new Date(alert.timestamp).toLocaleString()}${
                    alert.container_id
                      ? ` - Container: ${alert.container_id}`
                      : ""
                  }`}
                />
              </ListItem>
            ))}
          </List>
        </Paper>
      )}
    </Box>
  );
};

export default ProductionMonitoring;
