import React, { useState, useEffect, useCallback } from "react";
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  CircularProgress,
  Chip,
  IconButton,
  Tooltip,
  Switch,
  FormControlLabel,
} from "@mui/material";
import {
  Refresh as RefreshIcon,
  Pause as PauseIcon,
} from "@mui/icons-material";
import { useTheme } from "@mui/material/styles";
import MetricsChart, { MetricDataPoint } from "./MetricsChart";
import { useApiCall } from "../hooks/useApiCall";

interface ContainerStats {
  container_id: string;
  container_name: string;
  timestamp: string;
  status: string;
  cpu_percent: number;
  memory_usage: number;
  memory_limit: number;
  memory_percent: number;
  network_rx_bytes: number;
  network_tx_bytes: number;
  block_read_bytes: number;
  block_write_bytes: number;
}

interface RealTimeMetricsProps {
  containerId: string;
  refreshInterval?: number;
  maxDataPoints?: number;
}

const RealTimeMetrics: React.FC<RealTimeMetricsProps> = ({
  containerId,
  refreshInterval = 5000, // 5 seconds
  maxDataPoints = 50,
}) => {
  const theme = useTheme();
  const [isAutoRefresh, setIsAutoRefresh] = useState(true);
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

  const { execute: fetchStats, loading, error } = useApiCall();

  // Format bytes to human readable format
  const formatBytes = useCallback((bytes: number): string => {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB", "TB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
  }, []);

  // Format percentage
  const formatPercentage = useCallback((value: number): string => {
    return `${value.toFixed(1)}%`;
  }, []);

  // Fetch current stats
  const fetchCurrentStats = useCallback(async () => {
    try {
      const response = await fetchStats(`/api/containers/${containerId}/stats`);
      if (response && !response.error) {
        const stats: ContainerStats = response;
        const timestamp = new Date().toISOString();

        // Add new data points
        setMetricsHistory((prev) => {
          const newCpuPoint: MetricDataPoint = {
            timestamp,
            value: stats.cpu_percent || 0,
          };

          const newMemoryPoint: MetricDataPoint = {
            timestamp,
            value: stats.memory_percent || 0,
          };

          const newNetworkPoint: MetricDataPoint = {
            timestamp,
            value:
              (stats.network_rx_bytes + stats.network_tx_bytes) / 1024 / 1024, // MB
          };

          const newDiskPoint: MetricDataPoint = {
            timestamp,
            value:
              (stats.block_read_bytes + stats.block_write_bytes) / 1024 / 1024, // MB
          };

          return {
            cpu: [...prev.cpu.slice(-maxDataPoints + 1), newCpuPoint],
            memory: [...prev.memory.slice(-maxDataPoints + 1), newMemoryPoint],
            network: [
              ...prev.network.slice(-maxDataPoints + 1),
              newNetworkPoint,
            ],
            disk: [...prev.disk.slice(-maxDataPoints + 1), newDiskPoint],
          };
        });
      }
    } catch (err) {
      console.error("Error fetching container stats:", err);
    }
  }, [containerId, fetchStats, maxDataPoints]);

  // Auto-refresh effect
  useEffect(() => {
    if (!isAutoRefresh) return;

    const interval = setInterval(fetchCurrentStats, refreshInterval);

    // Initial fetch
    fetchCurrentStats();

    return () => clearInterval(interval);
  }, [isAutoRefresh, refreshInterval, fetchCurrentStats]);

  // Manual refresh
  const handleManualRefresh = () => {
    fetchCurrentStats();
  };

  // Toggle auto-refresh
  const handleToggleAutoRefresh = () => {
    setIsAutoRefresh(!isAutoRefresh);
  };

  // Get current stats for display
  const currentStats =
    metricsHistory.cpu.length > 0
      ? {
          cpu: metricsHistory.cpu[metricsHistory.cpu.length - 1]?.value || 0,
          memory:
            metricsHistory.memory[metricsHistory.memory.length - 1]?.value || 0,
          network:
            metricsHistory.network[metricsHistory.network.length - 1]?.value ||
            0,
          disk: metricsHistory.disk[metricsHistory.disk.length - 1]?.value || 0,
        }
      : null;

  return (
    <Box>
      {/* Controls */}
      <Box
        display="flex"
        justifyContent="space-between"
        alignItems="center"
        mb={2}
      >
        <Typography variant="h6">Real-time Metrics</Typography>
        <Box display="flex" alignItems="center" gap={1}>
          <FormControlLabel
            control={
              <Switch
                checked={isAutoRefresh}
                onChange={handleToggleAutoRefresh}
                size="small"
              />
            }
            label="Auto-refresh"
          />
          <Tooltip title="Refresh now">
            <span>
              <IconButton
                onClick={handleManualRefresh}
                disabled={loading}
                size="small"
              >
                {loading ? (
                  <CircularProgress size={20} />
                ) : isAutoRefresh ? (
                  <PauseIcon />
                ) : (
                  <RefreshIcon />
                )}
              </IconButton>
            </span>
          </Tooltip>
        </Box>
      </Box>

      {/* Current Stats Cards */}
      {currentStats && (
        <Grid container spacing={2} mb={3}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom variant="body2">
                  CPU Usage
                </Typography>
                <Typography variant="h5" component="div">
                  {formatPercentage(currentStats.cpu)}
                </Typography>
                <Chip
                  label={
                    currentStats.cpu > 80
                      ? "High"
                      : currentStats.cpu > 50
                        ? "Medium"
                        : "Low"
                  }
                  color={
                    currentStats.cpu > 80
                      ? "error"
                      : currentStats.cpu > 50
                        ? "warning"
                        : "success"
                  }
                  size="small"
                />
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom variant="body2">
                  Memory Usage
                </Typography>
                <Typography variant="h5" component="div">
                  {formatPercentage(currentStats.memory)}
                </Typography>
                <Chip
                  label={
                    currentStats.memory > 80
                      ? "High"
                      : currentStats.memory > 50
                        ? "Medium"
                        : "Low"
                  }
                  color={
                    currentStats.memory > 80
                      ? "error"
                      : currentStats.memory > 50
                        ? "warning"
                        : "success"
                  }
                  size="small"
                />
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom variant="body2">
                  Network I/O
                </Typography>
                <Typography variant="h5" component="div">
                  {formatBytes(currentStats.network * 1024 * 1024)}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Total
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom variant="body2">
                  Disk I/O
                </Typography>
                <Typography variant="h5" component="div">
                  {formatBytes(currentStats.disk * 1024 * 1024)}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Total
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Charts */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <MetricsChart
            title="CPU Usage"
            data={metricsHistory.cpu}
            type="area"
            color={theme.palette.error.main}
            unit="%"
            formatValue={formatPercentage}
            loading={loading && metricsHistory.cpu.length === 0}
            error={error}
          />
        </Grid>

        <Grid item xs={12} md={6}>
          <MetricsChart
            title="Memory Usage"
            data={metricsHistory.memory}
            type="area"
            color={theme.palette.warning.main}
            unit="%"
            formatValue={formatPercentage}
            loading={loading && metricsHistory.memory.length === 0}
            error={error}
          />
        </Grid>

        <Grid item xs={12} md={6}>
          <MetricsChart
            title="Network I/O"
            data={metricsHistory.network}
            type="line"
            color={theme.palette.info.main}
            unit=" MB"
            formatValue={(value) => formatBytes(value * 1024 * 1024)}
            loading={loading && metricsHistory.network.length === 0}
            error={error}
          />
        </Grid>

        <Grid item xs={12} md={6}>
          <MetricsChart
            title="Disk I/O"
            data={metricsHistory.disk}
            type="line"
            color={theme.palette.success.main}
            unit=" MB"
            formatValue={(value) => formatBytes(value * 1024 * 1024)}
            loading={loading && metricsHistory.disk.length === 0}
            error={error}
          />
        </Grid>
      </Grid>
    </Box>
  );
};

export default RealTimeMetrics;
