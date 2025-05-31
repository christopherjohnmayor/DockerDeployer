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
} from "@mui/material";
import { DateTimePicker } from "@mui/x-date-pickers/DateTimePicker";
import { LocalizationProvider } from "@mui/x-date-pickers/LocalizationProvider";
import { AdapterDateFns } from "@mui/x-date-pickers/AdapterDateFns";
import { useTheme } from "@mui/material/styles";
import { subHours, subDays, subWeeks } from "date-fns";
import MetricsChart, { MetricDataPoint } from "./MetricsChart";
import { useApiCall } from "../hooks/useApiCall";

interface HistoricalMetric {
  id: number;
  container_id: string;
  container_name: string;
  timestamp: string;
  cpu_percent: number;
  memory_usage: number;
  memory_limit: number;
  memory_percent: number;
  network_rx_bytes: number;
  network_tx_bytes: number;
  block_read_bytes: number;
  block_write_bytes: number;
}

interface MetricsHistoryProps {
  containerId: string;
}

const MetricsHistory: React.FC<MetricsHistoryProps> = ({ containerId }) => {
  const theme = useTheme();
  const [timeRange, setTimeRange] = useState("24h");
  const [customStartDate, setCustomStartDate] = useState<Date | null>(null);
  const [customEndDate, setCustomEndDate] = useState<Date | null>(null);
  const [historicalData, setHistoricalData] = useState<HistoricalMetric[]>([]);
  const [chartData, setChartData] = useState<{
    cpu: MetricDataPoint[];
    memory: MetricDataPoint[];
    networkRx: MetricDataPoint[];
    networkTx: MetricDataPoint[];
    diskRead: MetricDataPoint[];
    diskWrite: MetricDataPoint[];
  }>({
    cpu: [],
    memory: [],
    networkRx: [],
    networkTx: [],
    diskRead: [],
    diskWrite: [],
  });

  const { execute: fetchHistoricalMetrics, loading, error } = useApiCall();

  // Time range options
  const timeRangeOptions = [
    { value: "1h", label: "Last Hour", hours: 1 },
    { value: "6h", label: "Last 6 Hours", hours: 6 },
    { value: "24h", label: "Last 24 Hours", hours: 24 },
    { value: "7d", label: "Last 7 Days", hours: 168 },
    { value: "30d", label: "Last 30 Days", hours: 720 },
    { value: "custom", label: "Custom Range", hours: 0 },
  ];

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

  // Convert historical data to chart format
  const convertToChartData = useCallback((data: HistoricalMetric[]) => {
    const cpu: MetricDataPoint[] = [];
    const memory: MetricDataPoint[] = [];
    const networkRx: MetricDataPoint[] = [];
    const networkTx: MetricDataPoint[] = [];
    const diskRead: MetricDataPoint[] = [];
    const diskWrite: MetricDataPoint[] = [];

    data.forEach((metric) => {
      const timestamp = metric.timestamp;

      cpu.push({
        timestamp,
        value: metric.cpu_percent || 0,
      });

      memory.push({
        timestamp,
        value: metric.memory_percent || 0,
      });

      networkRx.push({
        timestamp,
        value: (metric.network_rx_bytes || 0) / 1024 / 1024, // Convert to MB
      });

      networkTx.push({
        timestamp,
        value: (metric.network_tx_bytes || 0) / 1024 / 1024, // Convert to MB
      });

      diskRead.push({
        timestamp,
        value: (metric.block_read_bytes || 0) / 1024 / 1024, // Convert to MB
      });

      diskWrite.push({
        timestamp,
        value: (metric.block_write_bytes || 0) / 1024 / 1024, // Convert to MB
      });
    });

    setChartData({
      cpu,
      memory,
      networkRx,
      networkTx,
      diskRead,
      diskWrite,
    });
  }, []);

  // Fetch historical metrics
  const fetchMetrics = useCallback(async () => {
    try {
      let hours = 24; // default

      if (timeRange === "custom") {
        if (!customStartDate || !customEndDate) {
          return;
        }
        const diffMs = customEndDate.getTime() - customStartDate.getTime();
        hours = Math.ceil(diffMs / (1000 * 60 * 60));
      } else {
        const selectedRange = timeRangeOptions.find(
          (option) => option.value === timeRange
        );
        hours = selectedRange?.hours || 24;
      }

      const response = await fetchHistoricalMetrics(
        `/api/containers/${containerId}/metrics/history?hours=${hours}&limit=1000`
      );

      if (response && response.metrics) {
        setHistoricalData(response.metrics);
        convertToChartData(response.metrics);
      }
    } catch (err) {
      console.error("Error fetching historical metrics:", err);
    }
  }, [
    containerId,
    timeRange,
    customStartDate,
    customEndDate,
    fetchHistoricalMetrics,
    timeRangeOptions,
    convertToChartData,
  ]);

  // Effect to fetch data when parameters change
  useEffect(() => {
    fetchMetrics();
  }, [fetchMetrics]);

  // Handle time range change
  const handleTimeRangeChange = (value: string) => {
    setTimeRange(value);
    if (value !== "custom") {
      setCustomStartDate(null);
      setCustomEndDate(null);
    }
  };

  // Handle refresh
  const handleRefresh = () => {
    fetchMetrics();
  };

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Box>
        {/* Controls */}
        <Paper elevation={2} sx={{ p: 2, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Historical Metrics
          </Typography>

          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth size="small">
                <InputLabel>Time Range</InputLabel>
                <Select
                  value={timeRange}
                  label="Time Range"
                  onChange={(e) => handleTimeRangeChange(e.target.value)}
                >
                  {timeRangeOptions.map((option) => (
                    <MenuItem key={option.value} value={option.value}>
                      {option.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            {timeRange === "custom" && (
              <>
                <Grid item xs={12} sm={6} md={3}>
                  <DateTimePicker
                    label="Start Date"
                    value={customStartDate}
                    onChange={setCustomStartDate}
                    slotProps={{
                      textField: { size: "small", fullWidth: true },
                    }}
                  />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <DateTimePicker
                    label="End Date"
                    value={customEndDate}
                    onChange={setCustomEndDate}
                    slotProps={{
                      textField: { size: "small", fullWidth: true },
                    }}
                  />
                </Grid>
              </>
            )}

            <Grid item xs={12} sm={6} md={3}>
              <Button
                variant="contained"
                onClick={handleRefresh}
                disabled={loading}
                fullWidth
                aria-label="Refresh metrics data"
              >
                {loading ? <CircularProgress size={20} /> : "Refresh"}
              </Button>
            </Grid>
          </Grid>

          {historicalData.length > 0 && (
            <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
              Showing {historicalData.length} data points
            </Typography>
          )}
        </Paper>

        {/* Error Display */}
        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            Failed to load historical metrics: {error}
          </Alert>
        )}

        {/* Charts */}
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <MetricsChart
              title="CPU Usage History"
              data={chartData.cpu}
              type="area"
              color={theme.palette.error.main}
              unit="%"
              formatValue={formatPercentage}
              loading={loading}
              height={350}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <MetricsChart
              title="Memory Usage History"
              data={chartData.memory}
              type="area"
              color={theme.palette.warning.main}
              unit="%"
              formatValue={formatPercentage}
              loading={loading}
              height={350}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <MetricsChart
              title="Network RX History"
              data={chartData.networkRx}
              type="line"
              color={theme.palette.info.main}
              unit=" MB"
              formatValue={(value) => formatBytes(value * 1024 * 1024)}
              loading={loading}
              height={350}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <MetricsChart
              title="Network TX History"
              data={chartData.networkTx}
              type="line"
              color={theme.palette.info.dark}
              unit=" MB"
              formatValue={(value) => formatBytes(value * 1024 * 1024)}
              loading={loading}
              height={350}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <MetricsChart
              title="Disk Read History"
              data={chartData.diskRead}
              type="line"
              color={theme.palette.success.main}
              unit=" MB"
              formatValue={(value) => formatBytes(value * 1024 * 1024)}
              loading={loading}
              height={350}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <MetricsChart
              title="Disk Write History"
              data={chartData.diskWrite}
              type="line"
              color={theme.palette.success.dark}
              unit=" MB"
              formatValue={(value) => formatBytes(value * 1024 * 1024)}
              loading={loading}
              height={350}
            />
          </Grid>
        </Grid>
      </Box>
    </LocalizationProvider>
  );
};

export default MetricsHistory;
