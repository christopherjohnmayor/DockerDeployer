import React, { useState, useEffect, useCallback } from "react";
import {
  Box,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  Tabs,
  Tab,
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
  Chip,
  Divider,
} from "@mui/material";
import {
  Dashboard as DashboardIcon,
  Timeline as TimelineIcon,
  Assessment as AssessmentIcon,
  Refresh as RefreshIcon,
  Settings as SettingsIcon,
  Fullscreen as FullscreenIcon,
  FullscreenExit as FullscreenExitIcon,
} from "@mui/icons-material";
import { useTheme } from "@mui/material/styles";
import { useApiCall } from "../hooks/useApiCall";
import { useWebSocket } from "../hooks/useWebSocket";
import MetricsChart from "./MetricsChart";
import RealTimeMetrics from "./RealTimeMetrics";
import MetricsHistory from "./MetricsHistory";
import ContainerHealthScoreVisualization from "./ContainerHealthScoreVisualization";
import PerformancePredictionCharts from "./PerformancePredictionCharts";
import RealTimeMetricsGrid from "./RealTimeMetricsGrid";
import HistoricalTrendsVisualization from "./HistoricalTrendsVisualization";
import MultiContainerComparisonView from "./MultiContainerComparisonView";
import { formatBytes, formatPercentage } from "../utils/formatters";
import { getEnhancedMetricsWebSocketUrl } from "../utils/websocket";
import {
  EnhancedMetricsData,
  HealthScore,
  PredictionData,
  ContainerMetrics,
  TimeRange,
} from "../types/enhancedMetrics";
import { EnhancedMetricsWebSocketHandler } from "../utils/enhancedWebSocket";

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({
  children,
  value,
  index,
  ...other
}) => {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`metrics-tabpanel-${index}`}
      aria-labelledby={`metrics-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
};

interface MetricsDashboardProps {
  containerId?: string;
  containerName?: string;
  autoRefresh?: boolean;
  refreshInterval?: number;
  showControls?: boolean;
  fullscreen?: boolean;
  onFullscreenToggle?: () => void;
}

interface DashboardMetrics {
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
    total_network_rx_bytes: number;
    total_network_tx_bytes: number;
  };
  top_consumers: {
    cpu: Array<{ container_name: string; value: number }>;
    memory: Array<{ container_name: string; value: number }>;
  };
  alerts_count: number;
  system_health_score: number;
}

const MetricsDashboard: React.FC<MetricsDashboardProps> = ({
  containerId,
  containerName,
  autoRefresh = true,
  refreshInterval = 30000,
  showControls = true,
  fullscreen = false,
  onFullscreenToggle,
}) => {
  const theme = useTheme();
  const [activeTab, setActiveTab] = useState(0);
  const [realTimeEnabled, setRealTimeEnabled] = useState(autoRefresh);
  const [selectedTimeRange, setSelectedTimeRange] = useState<TimeRange>("24h");
  const [selectedMetric, setSelectedMetric] = useState("cpu_percent");
  const [selectedContainers, setSelectedContainers] = useState<string[]>(
    containerId ? [containerId] : []
  );

  // Enhanced metrics state
  const [enhancedMetricsData, setEnhancedMetricsData] =
    useState<EnhancedMetricsData | null>(null);
  const [healthScore, setHealthScore] = useState<HealthScore | null>(null);
  const [predictionData, setPredictionData] = useState<PredictionData | null>(
    null
  );
  const [currentMetrics, setCurrentMetrics] = useState<ContainerMetrics | null>(
    null
  );
  const [enhancedLoading, setEnhancedLoading] = useState(false);
  const [enhancedError, setEnhancedError] = useState<string | null>(null);

  // API calls
  const {
    data: dashboardMetrics,
    loading: dashboardLoading,
    execute: fetchDashboard,
  } = useApiCall();
  const {
    data: systemMetrics,
    loading: systemLoading,
    execute: fetchSystemMetrics,
  } = useApiCall();

  // WebSocket for real-time dashboard updates
  const wsUrl = realTimeEnabled
    ? `ws://localhost:8000/ws/notifications/${localStorage.getItem("userId")}?token=${localStorage.getItem("token")}`
    : null;

  const { isConnected, connectionState } = useWebSocket(wsUrl, {
    onMessage: (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "metrics_update" || data.type === "alert_triggered") {
          // Refresh dashboard data when receiving updates
          fetchDashboard("/api/metrics/summary");
        }
      } catch (error) {
        console.error("Error parsing WebSocket message:", error);
      }
    },
    onConnect: () => {
      console.log("Connected to dashboard WebSocket");
    },
    onError: (error) => {
      console.error("Dashboard WebSocket error:", error);
    },
  });

  // Enhanced WebSocket for container-specific metrics
  const enhancedWsUrl =
    realTimeEnabled && containerId
      ? getEnhancedMetricsWebSocketUrl(
          containerId,
          localStorage.getItem("token") || ""
        )
      : null;

  const { isConnected: enhancedConnected } = useWebSocket(enhancedWsUrl, {
    onMessage: (event) => {
      try {
        const messageHandler = new EnhancedMetricsWebSocketHandler({
          onMetricsUpdate: (data: EnhancedMetricsData) => {
            setEnhancedMetricsData(data);
            setCurrentMetrics(data.current_metrics);
            setEnhancedError(null);
          },
          onHealthScoreUpdate: (data: HealthScore) => {
            setHealthScore(data);
          },
          onPredictionUpdate: (data: PredictionData) => {
            setPredictionData(data);
          },
          onAlertTriggered: (data: any) => {
            console.log("Alert triggered:", data);
          },
          onConnectionStatus: (status: string) => {
            console.log("Enhanced WebSocket status:", status);
          },
          onError: (error: string) => {
            setEnhancedError(error);
          },
        });
        messageHandler.handleMessage(event);
      } catch (error) {
        console.error("Error parsing enhanced WebSocket message:", error);
        setEnhancedError("WebSocket communication error");
      }
    },
    onConnect: () => {
      console.log("Connected to enhanced metrics WebSocket");
      setEnhancedLoading(false);
    },
    onError: (error) => {
      console.error("Enhanced WebSocket error:", error);
      setEnhancedError("Failed to connect to enhanced metrics");
      setEnhancedLoading(false);
    },
  });

  // Fetch initial data
  useEffect(() => {
    fetchDashboard("/api/metrics/summary");
    fetchSystemMetrics("/api/system/metrics");
  }, []);

  // Auto-refresh data
  useEffect(() => {
    if (!realTimeEnabled) return;

    const interval = setInterval(() => {
      fetchDashboard("/api/metrics/summary");
      if (activeTab === 0) {
        fetchSystemMetrics("/api/system/metrics");
      }
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [realTimeEnabled, refreshInterval, activeTab]);

  const handleTabChange = useCallback(
    (event: React.SyntheticEvent, newValue: number) => {
      setActiveTab(newValue);
    },
    []
  );

  const handleRefresh = useCallback(() => {
    fetchDashboard("/api/metrics/summary");
    fetchSystemMetrics("/api/system/metrics");
  }, []);

  const getHealthColor = (score: number) => {
    if (score >= 80) return theme.palette.success.main;
    if (score >= 60) return theme.palette.warning.main;
    return theme.palette.error.main;
  };

  const getHealthLabel = (score: number) => {
    if (score >= 80) return "Healthy";
    if (score >= 60) return "Warning";
    return "Critical";
  };

  return (
    <Box sx={{ width: "100%", height: fullscreen ? "100vh" : "auto" }}>
      {/* Header */}
      <Paper elevation={2} sx={{ p: 2, mb: 2 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Box display="flex" alignItems="center" gap={2}>
            <DashboardIcon color="primary" />
            <Typography variant="h5">
              {containerId
                ? `${containerName || containerId} Metrics`
                : "Metrics Dashboard"}
            </Typography>
            {realTimeEnabled && (
              <Chip
                label={isConnected ? "LIVE" : "CONNECTING"}
                color={isConnected ? "success" : "warning"}
                size="small"
                variant="filled"
              />
            )}
          </Box>

          {showControls && (
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
                    disabled={dashboardLoading}
                  >
                    <RefreshIcon />
                  </IconButton>
                </span>
              </Tooltip>
              {onFullscreenToggle && (
                <Tooltip title={fullscreen ? "Exit Fullscreen" : "Fullscreen"}>
                  <IconButton onClick={onFullscreenToggle}>
                    {fullscreen ? <FullscreenExitIcon /> : <FullscreenIcon />}
                  </IconButton>
                </Tooltip>
              )}
            </Box>
          )}
        </Box>

        {/* System Health Summary */}
        {dashboardMetrics && (
          <Box mt={2}>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6} md={3}>
                <Card variant="outlined">
                  <CardContent sx={{ py: 1 }}>
                    <Typography variant="h6" color="primary">
                      {dashboardMetrics.summary?.total_containers || 0}
                    </Typography>
                    <Typography variant="caption" color="textSecondary">
                      Total Containers
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Card variant="outlined">
                  <CardContent sx={{ py: 1 }}>
                    <Typography variant="h6" color="success.main">
                      {dashboardMetrics.summary?.healthy_containers || 0}
                    </Typography>
                    <Typography variant="caption" color="textSecondary">
                      Healthy
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Card variant="outlined">
                  <CardContent sx={{ py: 1 }}>
                    <Typography variant="h6" color="warning.main">
                      {dashboardMetrics.summary?.warning_containers || 0}
                    </Typography>
                    <Typography variant="caption" color="textSecondary">
                      Warning
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Card variant="outlined">
                  <CardContent sx={{ py: 1 }}>
                    <Typography variant="h6" color="error.main">
                      {dashboardMetrics.summary?.critical_containers || 0}
                    </Typography>
                    <Typography variant="caption" color="textSecondary">
                      Critical
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Box>
        )}
      </Paper>

      {/* Navigation Tabs */}
      <Paper elevation={1} sx={{ mb: 2 }}>
        <Tabs
          value={activeTab}
          onChange={handleTabChange}
          aria-label="metrics dashboard tabs"
          variant="scrollable"
          scrollButtons="auto"
        >
          <Tab
            icon={<DashboardIcon />}
            label="Overview"
            id="metrics-tab-0"
            aria-controls="metrics-tabpanel-0"
          />
          <Tab
            icon={<TimelineIcon />}
            label="Real-time"
            id="metrics-tab-1"
            aria-controls="metrics-tabpanel-1"
          />
          <Tab
            icon={<AssessmentIcon />}
            label="History"
            id="metrics-tab-2"
            aria-controls="metrics-tabpanel-2"
          />
          <Tab
            icon={<SettingsIcon />}
            label="Health Score"
            id="metrics-tab-3"
            aria-controls="metrics-tabpanel-3"
          />
          <Tab
            icon={<TimelineIcon />}
            label="Predictions"
            id="metrics-tab-4"
            aria-controls="metrics-tabpanel-4"
          />
          <Tab
            icon={<AssessmentIcon />}
            label="Comparison"
            id="metrics-tab-5"
            aria-controls="metrics-tabpanel-5"
          />
        </Tabs>
      </Paper>

      {/* Tab Content */}
      <TabPanel value={activeTab} index={0}>
        {/* Overview Tab */}
        {dashboardLoading ? (
          <Box display="flex" justifyContent="center" p={4}>
            <CircularProgress />
          </Box>
        ) : dashboardMetrics ? (
          <Grid container spacing={3}>
            {/* System Metrics Overview */}
            <Grid item xs={12} md={6}>
              <Paper elevation={2} sx={{ p: 3, height: "100%" }}>
                <Typography variant="h6" gutterBottom>
                  System Performance
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Box textAlign="center">
                      <Typography variant="h4" color="error.main">
                        {dashboardMetrics.aggregated_metrics?.avg_cpu_percent?.toFixed(
                          1
                        ) || "0.0"}
                        %
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        Average CPU
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={6}>
                    <Box textAlign="center">
                      <Typography variant="h4" color="warning.main">
                        {dashboardMetrics.aggregated_metrics?.avg_memory_percent?.toFixed(
                          1
                        ) || "0.0"}
                        %
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        Average Memory
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>
              </Paper>
            </Grid>

            {/* Network Activity */}
            <Grid item xs={12} md={6}>
              <Paper elevation={2} sx={{ p: 3, height: "100%" }}>
                <Typography variant="h6" gutterBottom>
                  Network Activity
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Box textAlign="center">
                      <Typography variant="h6" color="info.main">
                        {formatBytes(
                          dashboardMetrics.aggregated_metrics
                            ?.total_network_rx_bytes || 0
                        )}
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        Total RX
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={6}>
                    <Box textAlign="center">
                      <Typography variant="h6" color="info.main">
                        {formatBytes(
                          dashboardMetrics.aggregated_metrics
                            ?.total_network_tx_bytes || 0
                        )}
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        Total TX
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>
              </Paper>
            </Grid>
          </Grid>
        ) : (
          <Alert severity="error">
            Failed to load dashboard metrics. Please try refreshing.
          </Alert>
        )}
      </TabPanel>

      <TabPanel value={activeTab} index={1}>
        {/* Real-time Tab */}
        {containerId ? (
          <RealTimeMetricsGrid
            containerId={containerId}
            containerName={containerName}
            metricsData={currentMetrics}
            autoRefresh={realTimeEnabled}
            refreshInterval={3000}
            onRefresh={handleRefresh}
            onAutoRefreshToggle={setRealTimeEnabled}
            loading={enhancedLoading}
            error={enhancedError}
          />
        ) : (
          <Alert severity="info">
            Select a container to view real-time metrics.
          </Alert>
        )}
      </TabPanel>

      <TabPanel value={activeTab} index={2}>
        {/* History Tab */}
        {containerId ? (
          <HistoricalTrendsVisualization
            containerId={containerId}
            containerName={containerName}
            initialTimeRange={selectedTimeRange}
            onTimeRangeChange={setSelectedTimeRange}
            height={500}
            showBrush={true}
            showThresholds={true}
          />
        ) : (
          <Alert severity="info">
            Select a container to view historical metrics.
          </Alert>
        )}
      </TabPanel>

      <TabPanel value={activeTab} index={3}>
        {/* Health Score Tab */}
        {containerId ? (
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <ContainerHealthScoreVisualization
                healthScore={healthScore}
                loading={enhancedLoading}
                error={enhancedError}
                showRecommendations={true}
                showComponentBreakdown={true}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              {enhancedMetricsData && (
                <Paper elevation={2} sx={{ p: 2, height: 400 }}>
                  <Typography variant="h6" gutterBottom>
                    Health Trends
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Health score trends and analysis will be displayed here.
                    This could include historical health score data over time.
                  </Typography>
                </Paper>
              )}
            </Grid>
          </Grid>
        ) : (
          <Alert severity="info">
            Select a container to view health score analysis.
          </Alert>
        )}
      </TabPanel>

      <TabPanel value={activeTab} index={4}>
        {/* Predictions Tab */}
        {containerId ? (
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <PerformancePredictionCharts
                predictionData={predictionData}
                loading={enhancedLoading}
                error={enhancedError}
                showConfidenceIntervals={true}
                showThresholds={true}
                height={400}
              />
            </Grid>
            {predictionData && (
              <Grid item xs={12}>
                <Paper elevation={2} sx={{ p: 2 }}>
                  <Typography variant="h6" gutterBottom>
                    Prediction Summary
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={6} md={3}>
                      <Typography variant="body2" color="text.secondary">
                        Prediction Horizon
                      </Typography>
                      <Typography variant="h6">
                        {predictionData.prediction_horizon_hours}h
                      </Typography>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Typography variant="body2" color="text.secondary">
                        Confidence Level
                      </Typography>
                      <Typography variant="h6">
                        {Math.round(predictionData.confidence_level * 100)}%
                      </Typography>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Typography variant="body2" color="text.secondary">
                        Model Accuracy
                      </Typography>
                      <Typography variant="h6">
                        {Math.round(predictionData.model_accuracy * 100)}%
                      </Typography>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Typography variant="body2" color="text.secondary">
                        Last Updated
                      </Typography>
                      <Typography variant="body2">
                        {new Date(
                          predictionData.prediction_timestamp
                        ).toLocaleTimeString()}
                      </Typography>
                    </Grid>
                  </Grid>
                </Paper>
              </Grid>
            )}
          </Grid>
        ) : (
          <Alert severity="info">
            Select a container to view performance predictions.
          </Alert>
        )}
      </TabPanel>

      <TabPanel value={activeTab} index={5}>
        {/* Comparison Tab */}
        <MultiContainerComparisonView
          selectedContainers={selectedContainers}
          onContainerSelectionChange={setSelectedContainers}
          height={600}
          showRanking={true}
          showRadarChart={true}
        />
      </TabPanel>
    </Box>
  );
};

export default MetricsDashboard;
