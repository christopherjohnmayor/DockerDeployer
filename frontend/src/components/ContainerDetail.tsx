import React, { useState, useEffect } from "react";
import {
  Box,
  Paper,
  Typography,
  Grid,
  Chip,
  CircularProgress,
  Alert,
  Button,
  Tabs,
  Tab,
  IconButton,
  Tooltip,
} from "@mui/material";
import axios from "axios";
import RefreshIcon from "@mui/icons-material/Refresh";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import StopIcon from "@mui/icons-material/Stop";
import RestartAltIcon from "@mui/icons-material/RestartAlt";
import RealTimeMetrics from "./RealTimeMetrics";
import MetricsHistory from "./MetricsHistory";
import AlertsManager from "./AlertsManager";

/**
 * Props for the ContainerDetail component.
 *
 * @interface ContainerDetailProps
 * @property {string} containerId - The unique identifier of the Docker container to display
 */
interface ContainerDetailProps {
  containerId: string;
}

/**
 * Props for the TabPanel component used within ContainerDetail.
 *
 * @interface TabPanelProps
 * @property {React.ReactNode} [children] - The content to display in the tab panel
 * @property {number} index - The index of this tab panel
 * @property {number} value - The currently active tab index
 */
interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

/**
 * TabPanel component for organizing content in tabs within the ContainerDetail view.
 *
 * This component provides a standard Material-UI tab panel implementation with
 * proper accessibility attributes and conditional rendering based on the active tab.
 *
 * @param {TabPanelProps} props - The props for the TabPanel component
 * @returns {JSX.Element} A tab panel that shows/hides content based on the active tab
 */
function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`container-tabpanel-${index}`}
      aria-labelledby={`container-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

/**
 * ContainerDetail component displays comprehensive information about a Docker container.
 *
 * This component provides a detailed view of a Docker container including its status,
 * metadata, logs, and metrics. It features:
 *
 * - **Real-time status display** with color-coded status indicators
 * - **Container logs viewer** with automatic fetching and display
 * - **Action buttons** for container lifecycle management (start, stop, restart)
 * - **Resource usage metrics** showing CPU and memory consumption
 * - **Tabbed interface** for organizing different types of information
 * - **Auto-refresh capabilities** for keeping data current
 *
 * The component automatically fetches container data when mounted and provides
 * interactive controls for managing the container's lifecycle.
 *
 * @component
 * @example
 * ```tsx
 * // Basic usage
 * <ContainerDetail containerId="abc123def456" />
 *
 * // In a route
 * <Route path="/containers/:id" element={
 *   <ContainerDetail containerId={params.id} />
 * } />
 * ```
 *
 * @param {ContainerDetailProps} props - The props for the ContainerDetail component
 * @param {string} props.containerId - The unique identifier of the Docker container
 * @returns {JSX.Element} The rendered ContainerDetail component with tabs and controls
 */
const ContainerDetail: React.FC<ContainerDetailProps> = ({ containerId }) => {
  const [container, setContainer] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [logs, setLogs] = useState<string>("");
  const [logsLoading, setLogsLoading] = useState<boolean>(false);
  const [tabValue, setTabValue] = useState(0);

  const fetchContainer = async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await axios.get(`/api/containers/${containerId}`);
      setContainer(resp.data);
    } catch (err: any) {
      setError(
        err?.response?.data?.detail ||
          err.message ||
          "Failed to fetch container details."
      );
    } finally {
      setLoading(false);
    }
  };

  const fetchLogs = async () => {
    setLogsLoading(true);
    try {
      const resp = await axios.get(`/api/logs/${containerId}`);
      setLogs(resp.data.logs || "No logs available.");
    } catch (err: any) {
      setLogs(
        `Error fetching logs: ${
          err?.response?.data?.detail || err.message || "Unknown error"
        }`
      );
    } finally {
      setLogsLoading(false);
    }
  };

  useEffect(() => {
    fetchContainer();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [containerId]);

  useEffect(() => {
    if (tabValue === 1) {
      fetchLogs();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tabValue]);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleAction = async (action: "start" | "stop" | "restart") => {
    try {
      await axios.post(`/api/containers/${containerId}/action`, { action });
      fetchContainer();
    } catch (err: any) {
      setError(
        err?.response?.data?.detail ||
          err.message ||
          `Failed to ${action} container.`
      );
    }
  };

  if (loading) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight={200}
      >
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  if (!container) {
    return <Alert severity="info">Container not found.</Alert>;
  }

  return (
    <Box>
      <Paper sx={{ p: 3, mb: 3 }}>
        <Box
          display="flex"
          justifyContent="space-between"
          alignItems="center"
          mb={2}
        >
          <Typography variant="h5">{container.name}</Typography>
          <Box>
            <Tooltip title="Refresh">
              <IconButton onClick={fetchContainer} size="small">
                <RefreshIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Start">
              <span>
                <IconButton
                  color="success"
                  disabled={container.status === "running"}
                  onClick={() => handleAction("start")}
                  size="small"
                >
                  <PlayArrowIcon />
                </IconButton>
              </span>
            </Tooltip>
            <Tooltip title="Stop">
              <span>
                <IconButton
                  color="error"
                  disabled={container.status !== "running"}
                  onClick={() => handleAction("stop")}
                  size="small"
                >
                  <StopIcon />
                </IconButton>
              </span>
            </Tooltip>
            <Tooltip title="Restart">
              <span>
                <IconButton
                  color="primary"
                  disabled={container.status !== "running"}
                  onClick={() => handleAction("restart")}
                  size="small"
                >
                  <RestartAltIcon />
                </IconButton>
              </span>
            </Tooltip>
          </Box>
        </Box>

        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle2" color="text.secondary">
              Status
            </Typography>
            <Chip
              label={container.status}
              color={
                container.status === "running"
                  ? "success"
                  : container.status === "exited"
                    ? "default"
                    : "warning"
              }
              size="small"
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle2" color="text.secondary">
              ID
            </Typography>
            <Typography variant="body2">{container.id}</Typography>
          </Grid>
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle2" color="text.secondary">
              Image
            </Typography>
            <Typography variant="body2">
              {container.image && container.image.length > 0
                ? container.image.join(", ")
                : "-"}
            </Typography>
          </Grid>
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle2" color="text.secondary">
              Ports
            </Typography>
            <Typography variant="body2">
              {container.ports
                ? Object.keys(container.ports).length > 0
                  ? Object.entries(container.ports)
                      .map(
                        ([k, v]) =>
                          `${k} → ${Array.isArray(v) ? v.join(",") : v}`
                      )
                      .join(", ")
                  : "-"
                : "-"}
            </Typography>
          </Grid>
        </Grid>
      </Paper>

      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          aria-label="container tabs"
        >
          <Tab label="Overview" />
          <Tab label="Logs" />
          <Tab label="Real-time Metrics" />
          <Tab label="Metrics History" />
          <Tab label="Alerts" />
          <Tab label="Environment" />
        </Tabs>

        <TabPanel value={tabValue} index={0}>
          <Typography variant="h6" gutterBottom>
            Container Details
          </Typography>
          <Grid container spacing={2}>
            {/* Additional container details can be added here */}
            <Grid item xs={12}>
              <Typography variant="subtitle2" color="text.secondary">
                Labels
              </Typography>
              <Box sx={{ mt: 1 }}>
                {container.labels &&
                Object.keys(container.labels).length > 0 ? (
                  Object.entries(container.labels).map(([key, value]) => (
                    <Chip
                      key={key}
                      label={`${key}: ${value}`}
                      size="small"
                      sx={{ mr: 1, mb: 1 }}
                    />
                  ))
                ) : (
                  <Typography variant="body2">No labels</Typography>
                )}
              </Box>
            </Grid>
          </Grid>
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <Box
            display="flex"
            justifyContent="space-between"
            alignItems="center"
            mb={2}
          >
            <Typography variant="h6">Container Logs</Typography>
            <Button
              startIcon={<RefreshIcon />}
              onClick={fetchLogs}
              disabled={logsLoading}
              size="small"
            >
              Refresh Logs
            </Button>
          </Box>
          {logsLoading ? (
            <Box
              display="flex"
              justifyContent="center"
              alignItems="center"
              minHeight={100}
            >
              <CircularProgress size={24} />
            </Box>
          ) : (
            <Box
              component="pre"
              sx={{
                background: "#111",
                color: "#fff",
                borderRadius: 1,
                p: 2,
                minHeight: 200,
                maxHeight: 400,
                overflow: "auto",
                fontSize: "0.95em",
              }}
            >
              {logs}
            </Box>
          )}
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <RealTimeMetrics containerId={containerId} />
        </TabPanel>

        <TabPanel value={tabValue} index={3}>
          <MetricsHistory containerId={containerId} />
        </TabPanel>

        <TabPanel value={tabValue} index={4}>
          <AlertsManager containerId={containerId} />
        </TabPanel>

        <TabPanel value={tabValue} index={5}>
          <Typography variant="h6" gutterBottom>
            Environment Variables
          </Typography>
          {/* Environment variables would be displayed here */}
          <Alert severity="info">
            Environment variables are not available in the current API response.
          </Alert>
        </TabPanel>
      </Paper>
    </Box>
  );
};

export default ContainerDetail;
