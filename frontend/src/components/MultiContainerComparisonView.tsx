/**
 * Multi-Container Comparison View Component
 *
 * Provides side-by-side container metrics comparison with normalized scales,
 * performance ranking, and aggregate statistics.
 */

import React, { useState, useEffect } from "react";
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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Alert,
  useTheme,
  SelectChangeEvent,
  Avatar,
} from "@mui/material";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from "recharts";
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Star as StarIcon,
} from "@mui/icons-material";
import {
  ContainerComparison,
  ContainerMetrics,
} from "../types/enhancedMetrics";
import { formatBytes, formatPercentage } from "../utils/formatters";
import { useApiCall } from "../hooks/useApiCall";

interface MultiContainerComparisonViewProps {
  selectedContainers: string[];
  onContainerSelectionChange?: (containers: string[]) => void;
  height?: number;
  showRanking?: boolean;
  showRadarChart?: boolean;
}

const MultiContainerComparisonView: React.FC<
  MultiContainerComparisonViewProps
> = ({
  selectedContainers,
  onContainerSelectionChange,
  height = 500,
  showRanking = true,
  showRadarChart = true,
}) => {
  const theme = useTheme();
  const [comparisonMetric, setComparisonMetric] =
    useState<string>("cpu_percent");
  const [availableContainers, setAvailableContainers] = useState<any[]>([]);

  // API calls
  const {
    data: containers,
    loading: containersLoading,
    execute: fetchContainers,
  } = useApiCall();

  const {
    data: comparisonData,
    loading: comparisonLoading,
    error: comparisonError,
    execute: fetchComparison,
  } = useApiCall<ContainerComparison>();

  // Fetch available containers
  useEffect(() => {
    fetchContainers("/api/containers");
  }, [fetchContainers]);

  // Update available containers
  useEffect(() => {
    if (containers) {
      setAvailableContainers(containers);
    }
  }, [containers]);

  // Fetch comparison data when containers change
  useEffect(() => {
    if (selectedContainers.length > 1) {
      fetchComparison(
        `/api/containers/metrics/comparison?container_ids=${selectedContainers.join(",")}`
      );
    }
  }, [selectedContainers, fetchComparison]);

  // Handle container selection change
  const handleContainerSelectionChange = (
    event: SelectChangeEvent<string[]>
  ) => {
    const value = event.target.value;
    const newSelection = typeof value === "string" ? value.split(",") : value;
    onContainerSelectionChange?.(newSelection);
  };

  // Handle comparison metric change
  const handleComparisonMetricChange = (event: SelectChangeEvent) => {
    setComparisonMetric(event.target.value);
  };

  // Prepare chart data
  const prepareChartData = () => {
    if (!comparisonData || !comparisonData.metrics_comparison) return [];

    return Object.entries(comparisonData.metrics_comparison).map(
      ([containerId, data]) => ({
        container: data.container_name,
        containerId,
        cpu_percent: data.current_metrics.cpu_percent,
        memory_percent: data.current_metrics.memory_percent,
        network_io:
          (data.current_metrics.network_rx_bytes +
            data.current_metrics.network_tx_bytes) /
          1024 /
          1024,
        disk_io:
          (data.current_metrics.block_read_bytes +
            data.current_metrics.block_write_bytes) /
          1024 /
          1024,
        health_score: data.health_score,
        performance_rank: data.performance_rank,
      })
    );
  };

  // Prepare radar chart data
  const prepareRadarData = () => {
    if (!comparisonData || !comparisonData.metrics_comparison) return [];

    const chartData = prepareChartData();
    return chartData.map((container) => ({
      container: container.container,
      CPU: container.cpu_percent,
      Memory: container.memory_percent,
      Network: Math.min(container.network_io, 100), // Normalize to 0-100
      Disk: Math.min(container.disk_io, 100), // Normalize to 0-100
      Health: container.health_score,
    }));
  };

  // Get performance rank color
  const getRankColor = (rank: number) => {
    if (rank === 1) return theme.palette.success.main;
    if (rank === 2) return theme.palette.info.main;
    if (rank === 3) return theme.palette.warning.main;
    return theme.palette.grey[500];
  };

  // Get metric configuration
  const getMetricConfig = (metric: string) => {
    const configs = {
      cpu_percent: {
        name: "CPU Usage",
        color: theme.palette.primary.main,
        unit: "%",
        formatter: formatPercentage,
      },
      memory_percent: {
        name: "Memory Usage",
        color: theme.palette.secondary.main,
        unit: "%",
        formatter: formatPercentage,
      },
      network_io: {
        name: "Network I/O",
        color: theme.palette.info.main,
        unit: " MB/s",
        formatter: (value: number) => formatBytes(value * 1024 * 1024),
      },
      disk_io: {
        name: "Disk I/O",
        color: theme.palette.success.main,
        unit: " MB/s",
        formatter: (value: number) => formatBytes(value * 1024 * 1024),
      },
      health_score: {
        name: "Health Score",
        color: theme.palette.warning.main,
        unit: "/100",
        formatter: (value: number) => value.toFixed(1),
      },
    };
    return configs[metric as keyof typeof configs] || configs.cpu_percent;
  };

  // Custom tooltip for charts
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const config = getMetricConfig(comparisonMetric);
      return (
        <Paper sx={{ p: 1, border: 1, borderColor: "divider" }}>
          <Typography variant="body2" fontWeight="bold">
            {label}
          </Typography>
          <Typography variant="body2" sx={{ color: config.color }}>
            {config.name}: {config.formatter(payload[0].value)}
          </Typography>
        </Paper>
      );
    }
    return null;
  };

  const chartData = prepareChartData();
  const radarData = prepareRadarData();
  const config = getMetricConfig(comparisonMetric);

  if (selectedContainers.length < 2) {
    return (
      <Paper elevation={2} sx={{ p: 2, height }}>
        <Typography variant="h6" gutterBottom>
          Container Comparison
        </Typography>
        <Alert severity="info">
          Select at least 2 containers to compare their performance metrics.
        </Alert>
      </Paper>
    );
  }

  if (comparisonError) {
    return (
      <Paper elevation={2} sx={{ p: 2, height }}>
        <Typography variant="h6" gutterBottom>
          Container Comparison
        </Typography>
        <Alert severity="error">{comparisonError}</Alert>
      </Paper>
    );
  }

  return (
    <Paper elevation={2} sx={{ p: 2, height }}>
      {/* Header */}
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          mb: 2,
        }}
      >
        <Typography variant="h6">Container Comparison</Typography>
        <Chip
          label={`${selectedContainers.length} containers`}
          size="small"
          color="primary"
        />
      </Box>

      {/* Controls */}
      <Box sx={{ display: "flex", gap: 2, mb: 2, flexWrap: "wrap" }}>
        {/* Container Selector */}
        <FormControl size="small" sx={{ minWidth: 300 }}>
          <InputLabel>Containers</InputLabel>
          <Select
            multiple
            value={selectedContainers}
            label="Containers"
            onChange={handleContainerSelectionChange}
            renderValue={(selected) => (
              <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5 }}>
                {selected.map((value) => {
                  const container = Array.isArray(availableContainers)
                    ? availableContainers.find((c) => c.id === value)
                    : null;
                  return (
                    <Chip
                      key={value}
                      label={container?.name || value}
                      size="small"
                    />
                  );
                })}
              </Box>
            )}
          >
            {Array.isArray(availableContainers) &&
              availableContainers.map((container) => (
                <MenuItem key={container.id} value={container.id}>
                  {container.name}
                </MenuItem>
              ))}
          </Select>
        </FormControl>

        {/* Metric Selector */}
        <FormControl size="small" sx={{ minWidth: 150 }}>
          <InputLabel>Metric</InputLabel>
          <Select
            value={comparisonMetric}
            label="Metric"
            onChange={handleComparisonMetricChange}
          >
            <MenuItem value="cpu_percent">CPU Usage</MenuItem>
            <MenuItem value="memory_percent">Memory Usage</MenuItem>
            <MenuItem value="network_io">Network I/O</MenuItem>
            <MenuItem value="disk_io">Disk I/O</MenuItem>
            <MenuItem value="health_score">Health Score</MenuItem>
          </Select>
        </FormControl>
      </Box>

      {comparisonLoading ? (
        <Box
          sx={{
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            height: "60%",
          }}
        >
          <Typography variant="body2" color="text.secondary">
            Loading comparison data...
          </Typography>
        </Box>
      ) : (
        <Grid container spacing={2}>
          {/* Bar Chart */}
          <Grid item xs={12} md={showRadarChart ? 6 : 12}>
            <Box sx={{ height: 250 }}>
              <Typography variant="subtitle2" gutterBottom>
                {config.name} Comparison
              </Typography>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="container"
                    tick={{ fontSize: 12 }}
                    angle={-45}
                    textAnchor="end"
                    height={60}
                  />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar
                    dataKey={comparisonMetric}
                    fill={config.color}
                    name={config.name}
                  />
                </BarChart>
              </ResponsiveContainer>
            </Box>
          </Grid>

          {/* Radar Chart */}
          {showRadarChart && (
            <Grid item xs={12} md={6}>
              <Box sx={{ height: 250 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Performance Overview
                </Typography>
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart data={radarData}>
                    <PolarGrid />
                    <PolarAngleAxis tick={{ fontSize: 10 }} />
                    <PolarRadiusAxis
                      angle={90}
                      domain={[0, 100]}
                      tick={{ fontSize: 8 }}
                    />
                    {chartData.map((container, index) => (
                      <Radar
                        key={container.containerId}
                        name={container.container}
                        dataKey={container.container}
                        stroke={theme.palette.primary.main}
                        fill={theme.palette.primary.main}
                        fillOpacity={0.1 + index * 0.1}
                      />
                    ))}
                    <Legend />
                  </RadarChart>
                </ResponsiveContainer>
              </Box>
            </Grid>
          )}

          {/* Performance Ranking Table */}
          {showRanking && comparisonData && (
            <Grid item xs={12}>
              <Typography variant="subtitle2" gutterBottom>
                Performance Ranking
              </Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Rank</TableCell>
                      <TableCell>Container</TableCell>
                      <TableCell align="right">CPU %</TableCell>
                      <TableCell align="right">Memory %</TableCell>
                      <TableCell align="right">Network I/O</TableCell>
                      <TableCell align="right">Disk I/O</TableCell>
                      <TableCell align="right">Health Score</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {chartData
                      .sort((a, b) => a.performance_rank - b.performance_rank)
                      .map((container) => (
                        <TableRow key={container.containerId}>
                          <TableCell>
                            <Box sx={{ display: "flex", alignItems: "center" }}>
                              <Avatar
                                sx={{
                                  width: 24,
                                  height: 24,
                                  bgcolor: getRankColor(
                                    container.performance_rank
                                  ),
                                  fontSize: "0.8rem",
                                }}
                              >
                                {container.performance_rank}
                              </Avatar>
                              {container.performance_rank === 1 && (
                                <StarIcon
                                  fontSize="small"
                                  sx={{ ml: 0.5, color: "gold" }}
                                />
                              )}
                            </Box>
                          </TableCell>
                          <TableCell>{container.container}</TableCell>
                          <TableCell align="right">
                            {formatPercentage(container.cpu_percent)}
                          </TableCell>
                          <TableCell align="right">
                            {formatPercentage(container.memory_percent)}
                          </TableCell>
                          <TableCell align="right">
                            {formatBytes(container.network_io * 1024 * 1024)}
                          </TableCell>
                          <TableCell align="right">
                            {formatBytes(container.disk_io * 1024 * 1024)}
                          </TableCell>
                          <TableCell align="right">
                            <Chip
                              label={container.health_score.toFixed(1)}
                              size="small"
                              color={
                                container.health_score >= 80
                                  ? "success"
                                  : container.health_score >= 60
                                    ? "warning"
                                    : "error"
                              }
                            />
                          </TableCell>
                        </TableRow>
                      ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Grid>
          )}

          {/* Aggregate Statistics */}
          {comparisonData && comparisonData.aggregated_stats && (
            <Grid item xs={12}>
              <Box
                sx={{
                  mt: 2,
                  p: 1,
                  backgroundColor: "background.paper",
                  borderRadius: 1,
                }}
              >
                <Typography variant="subtitle2" gutterBottom>
                  Aggregate Statistics
                </Typography>
                <Box sx={{ display: "flex", gap: 3, flexWrap: "wrap" }}>
                  <Typography variant="body2">
                    Avg CPU:{" "}
                    {formatPercentage(
                      comparisonData.aggregated_stats.avg_cpu_percent
                    )}
                  </Typography>
                  <Typography variant="body2">
                    Avg Memory:{" "}
                    {formatPercentage(
                      comparisonData.aggregated_stats.avg_memory_percent
                    )}
                  </Typography>
                  <Typography variant="body2">
                    Total Network I/O:{" "}
                    {formatBytes(
                      comparisonData.aggregated_stats.total_network_io
                    )}
                  </Typography>
                  <Typography variant="body2">
                    Total Disk I/O:{" "}
                    {formatBytes(comparisonData.aggregated_stats.total_disk_io)}
                  </Typography>
                </Box>
              </Box>
            </Grid>
          )}
        </Grid>
      )}
    </Paper>
  );
};

export default MultiContainerComparisonView;
