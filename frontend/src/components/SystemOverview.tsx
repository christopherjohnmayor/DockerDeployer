import React, { useState, useEffect, useCallback } from "react";
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  CircularProgress,
  Chip,
  LinearProgress,
  IconButton,
  Tooltip,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
} from "@mui/material";
import {
  Refresh as RefreshIcon,
  Computer as ComputerIcon,
  Memory as MemoryIcon,
  Storage as StorageIcon,
  Speed as SpeedIcon,
  Inventory as ContainerIcon,
} from "@mui/icons-material";
import { useTheme } from "@mui/material/styles";
import { useApiCall } from "../hooks/useApiCall";
import axios from "axios";

interface SystemMetrics {
  timestamp: string;
  containers_total: number;
  containers_running: number;
  containers_by_status: Record<string, number>;
  system_info: {
    docker_version: string;
    total_memory: number;
    cpus: number;
    kernel_version: string;
    operating_system: string;
    architecture: string;
  };
}

interface SystemOverviewProps {
  refreshInterval?: number;
}

const SystemOverview: React.FC<SystemOverviewProps> = ({
  refreshInterval = 30000, // 30 seconds
}) => {
  const theme = useTheme();
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics | null>(
    null
  );
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  // API function for fetching system metrics
  const fetchSystemMetricsApi = useCallback(async () => {
    const response = await axios.get("/api/system/metrics");
    return response.data;
  }, []);

  const {
    execute: fetchSystemMetrics,
    loading,
    error,
  } = useApiCall(fetchSystemMetricsApi);

  // Format bytes to human readable format
  const formatBytes = useCallback((bytes: number): string => {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB", "TB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
  }, []);

  // Fetch system metrics
  const fetchMetrics = useCallback(async () => {
    try {
      const response = await fetchSystemMetrics();
      if (response && !response.error) {
        setSystemMetrics(response);
        setLastUpdated(new Date());
      }
    } catch (err) {
      console.error("Error fetching system metrics:", err);
    }
  }, [fetchSystemMetrics]);

  // Auto-refresh effect
  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, refreshInterval);
    return () => clearInterval(interval);
  }, [fetchMetrics, refreshInterval]);

  // Manual refresh
  const handleRefresh = () => {
    fetchMetrics();
  };

  // Get status color for containers
  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case "running":
        return "success";
      case "stopped":
      case "exited":
        return "error";
      case "paused":
        return "warning";
      case "restarting":
        return "info";
      default:
        return "default";
    }
  };

  // Calculate container health percentage
  const getContainerHealthPercentage = () => {
    if (!systemMetrics) return 0;
    const { containers_total, containers_running } = systemMetrics;
    return containers_total > 0
      ? (containers_running / containers_total) * 100
      : 0;
  };

  if (error) {
    return (
      <Paper elevation={2} sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          System Overview
        </Typography>
        <Typography color="error">
          Failed to load system metrics: {error.message}
        </Typography>
      </Paper>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box
        display="flex"
        justifyContent="space-between"
        alignItems="center"
        mb={3}
      >
        <Typography variant="h5">System Overview</Typography>
        <Box display="flex" alignItems="center" gap={1}>
          {lastUpdated && (
            <Typography variant="body2" color="textSecondary">
              Last updated: {lastUpdated.toLocaleTimeString()}
            </Typography>
          )}
          <Tooltip title="Refresh">
            <IconButton onClick={handleRefresh} disabled={loading}>
              {loading ? <CircularProgress size={20} /> : <RefreshIcon />}
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {loading && !systemMetrics ? (
        <Box display="flex" justifyContent="center" p={4}>
          <CircularProgress />
        </Box>
      ) : systemMetrics ? (
        <Grid container spacing={3}>
          {/* Container Status Overview */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={2}>
                  <ContainerIcon sx={{ mr: 1 }} />
                  <Typography variant="h6">Container Status</Typography>
                </Box>

                <Box mb={2}>
                  <Typography variant="h3" color="primary">
                    {systemMetrics.containers_running}
                  </Typography>
                  <Typography color="textSecondary">
                    of {systemMetrics.containers_total} containers running
                  </Typography>
                </Box>

                <Box mb={2}>
                  <Typography variant="body2" gutterBottom>
                    Health: {getContainerHealthPercentage().toFixed(1)}%
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={getContainerHealthPercentage()}
                    color={
                      getContainerHealthPercentage() > 80
                        ? "success"
                        : getContainerHealthPercentage() > 50
                          ? "warning"
                          : "error"
                    }
                    sx={{ height: 8, borderRadius: 4 }}
                  />
                </Box>

                <Box display="flex" flexWrap="wrap" gap={1}>
                  {Object.entries(systemMetrics.containers_by_status).map(
                    ([status, count]) => (
                      <Chip
                        key={status}
                        label={`${status}: ${count}`}
                        color={getStatusColor(status)}
                        size="small"
                        variant="outlined"
                      />
                    )
                  )}
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* System Resources */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={2}>
                  <ComputerIcon sx={{ mr: 1 }} />
                  <Typography variant="h6">System Resources</Typography>
                </Box>

                <List dense>
                  <ListItem>
                    <ListItemIcon>
                      <SpeedIcon />
                    </ListItemIcon>
                    <ListItemText
                      primary="CPU Cores"
                      secondary={`${systemMetrics.system_info.cpus} cores`}
                    />
                  </ListItem>

                  <ListItem>
                    <ListItemIcon>
                      <MemoryIcon />
                    </ListItemIcon>
                    <ListItemText
                      primary="Total Memory"
                      secondary={formatBytes(
                        systemMetrics.system_info.total_memory
                      )}
                    />
                  </ListItem>

                  <ListItem>
                    <ListItemIcon>
                      <StorageIcon />
                    </ListItemIcon>
                    <ListItemText
                      primary="Architecture"
                      secondary={systemMetrics.system_info.architecture}
                    />
                  </ListItem>
                </List>
              </CardContent>
            </Card>
          </Grid>

          {/* System Information */}
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  System Information
                </Typography>

                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6} md={3}>
                    <Typography variant="body2" color="textSecondary">
                      Docker Version
                    </Typography>
                    <Typography variant="body1">
                      {systemMetrics.system_info.docker_version}
                    </Typography>
                  </Grid>

                  <Grid item xs={12} sm={6} md={3}>
                    <Typography variant="body2" color="textSecondary">
                      Operating System
                    </Typography>
                    <Typography variant="body1">
                      {systemMetrics.system_info.operating_system}
                    </Typography>
                  </Grid>

                  <Grid item xs={12} sm={6} md={3}>
                    <Typography variant="body2" color="textSecondary">
                      Kernel Version
                    </Typography>
                    <Typography variant="body1">
                      {systemMetrics.system_info.kernel_version}
                    </Typography>
                  </Grid>

                  <Grid item xs={12} sm={6} md={3}>
                    <Typography variant="body2" color="textSecondary">
                      Last Updated
                    </Typography>
                    <Typography variant="body1">
                      {new Date(systemMetrics.timestamp).toLocaleString()}
                    </Typography>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      ) : null}
    </Box>
  );
};

export default SystemOverview;
