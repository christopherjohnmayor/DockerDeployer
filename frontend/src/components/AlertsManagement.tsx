import React, { useState, useEffect, useCallback } from "react";
import {
  Box,
  Paper,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Chip,
  Alert,
  CircularProgress,
  Tooltip,
  Grid,
  Card,
  CardContent,
  Divider,
} from "@mui/material";
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  NotificationsActive as AlertIcon,
  NotificationsOff as AlertOffIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  CheckCircle as CheckCircleIcon,
} from "@mui/icons-material";
import { useTheme } from "@mui/material/styles";
import { useApiCall } from "../hooks/useApiCall";
import { useWebSocket } from "../hooks/useWebSocket";

interface Alert {
  id: number;
  name: string;
  description?: string;
  container_id: string;
  container_name: string;
  metric_type: string;
  threshold_value: number;
  comparison_operator: string;
  is_active: boolean;
  is_triggered: boolean;
  last_triggered_at?: string;
  trigger_count: number;
  created_at: string;
  updated_at: string;
}

interface AlertFormData {
  name: string;
  description: string;
  container_id: string;
  metric_type: string;
  threshold_value: number;
  comparison_operator: string;
  is_active: boolean;
}

interface AlertFormProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: AlertFormData) => void;
  alert?: Alert;
  containers: Array<{ id: string; name: string }>;
  loading?: boolean;
}

const AlertForm: React.FC<AlertFormProps> = ({
  open,
  onClose,
  onSubmit,
  alert,
  containers,
  loading = false,
}) => {
  const [formData, setFormData] = useState<AlertFormData>({
    name: "",
    description: "",
    container_id: "",
    metric_type: "cpu_percent",
    threshold_value: 80,
    comparison_operator: ">",
    is_active: true,
  });

  useEffect(() => {
    if (alert) {
      setFormData({
        name: alert.name,
        description: alert.description || "",
        container_id: alert.container_id,
        metric_type: alert.metric_type,
        threshold_value: alert.threshold_value,
        comparison_operator: alert.comparison_operator,
        is_active: alert.is_active,
      });
    } else {
      setFormData({
        name: "",
        description: "",
        container_id: "",
        metric_type: "cpu_percent",
        threshold_value: 80,
        comparison_operator: ">",
        is_active: true,
      });
    }
  }, [alert, open]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  const handleChange =
    (field: keyof AlertFormData) =>
    (event: React.ChangeEvent<HTMLInputElement | { value: unknown }>) => {
      setFormData((prev) => ({
        ...prev,
        [field]: event.target.value,
      }));
    };

  const metricTypes = [
    { value: "cpu_percent", label: "CPU Usage (%)" },
    { value: "memory_percent", label: "Memory Usage (%)" },
    { value: "network_rx_bytes", label: "Network RX (bytes)" },
    { value: "network_tx_bytes", label: "Network TX (bytes)" },
    { value: "block_read_bytes", label: "Disk Read (bytes)" },
    { value: "block_write_bytes", label: "Disk Write (bytes)" },
  ];

  const operators = [
    { value: ">", label: "Greater than (>)" },
    { value: "<", label: "Less than (<)" },
    { value: ">=", label: "Greater than or equal (>=)" },
    { value: "<=", label: "Less than or equal (<=)" },
    { value: "==", label: "Equal to (==)" },
    { value: "!=", label: "Not equal to (!=)" },
  ];

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <form onSubmit={handleSubmit}>
        <DialogTitle>{alert ? "Edit Alert" : "Create New Alert"}</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Alert Name"
                value={formData.name}
                onChange={handleChange("name")}
                required
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Description"
                value={formData.description}
                onChange={handleChange("description")}
                multiline
                rows={2}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth required>
                <InputLabel>Container</InputLabel>
                <Select
                  value={formData.container_id}
                  label="Container"
                  onChange={handleChange("container_id")}
                >
                  {containers.map((container) => (
                    <MenuItem key={container.id} value={container.id}>
                      {container.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth required>
                <InputLabel>Metric Type</InputLabel>
                <Select
                  value={formData.metric_type}
                  label="Metric Type"
                  onChange={handleChange("metric_type")}
                >
                  {metricTypes.map((metric) => (
                    <MenuItem key={metric.value} value={metric.value}>
                      {metric.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth required>
                <InputLabel>Operator</InputLabel>
                <Select
                  value={formData.comparison_operator}
                  label="Operator"
                  onChange={handleChange("comparison_operator")}
                >
                  {operators.map((operator) => (
                    <MenuItem key={operator.value} value={operator.value}>
                      {operator.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Threshold Value"
                type="number"
                value={formData.threshold_value}
                onChange={handleChange("threshold_value")}
                required
                inputProps={{ min: 0, step: 0.1 }}
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.is_active}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        is_active: e.target.checked,
                      }))
                    }
                  />
                }
                label="Active"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>Cancel</Button>
          <Button type="submit" variant="contained" disabled={loading}>
            {loading ? (
              <CircularProgress size={20} />
            ) : alert ? (
              "Update"
            ) : (
              "Create"
            )}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};

const AlertsManagement: React.FC = () => {
  const theme = useTheme();
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [containers, setContainers] = useState<
    Array<{ id: string; name: string }>
  >([]);
  const [formOpen, setFormOpen] = useState(false);
  const [editingAlert, setEditingAlert] = useState<Alert | undefined>();
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [alertToDelete, setAlertToDelete] = useState<Alert | undefined>();

  // API calls
  const {
    data: alertsData,
    loading: alertsLoading,
    execute: fetchAlerts,
  } = useApiCall();
  const {
    data: containersData,
    loading: containersLoading,
    execute: fetchContainers,
  } = useApiCall();
  const { loading: createLoading, execute: createAlert } = useApiCall();
  const { loading: updateLoading, execute: updateAlert } = useApiCall();
  const { loading: deleteLoading, execute: deleteAlert } = useApiCall();

  // WebSocket for real-time alert updates
  const wsUrl = `ws://localhost:8000/ws/notifications/${localStorage.getItem("userId")}?token=${localStorage.getItem("token")}`;

  const { isConnected } = useWebSocket(wsUrl, {
    onMessage: (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "alert_triggered" || data.type === "alert_updated") {
          // Refresh alerts when receiving updates
          fetchAlerts("/api/alerts");
        }
      } catch (error) {
        console.error("Error parsing WebSocket message:", error);
      }
    },
  });

  // Fetch initial data
  useEffect(() => {
    fetchAlerts("/api/alerts");
    fetchContainers("/api/containers");
  }, []);

  // Update state when data is fetched
  useEffect(() => {
    if (alertsData) {
      setAlerts(alertsData);
    }
  }, [alertsData]);

  useEffect(() => {
    if (containersData) {
      setContainers(
        containersData.map((c: any) => ({ id: c.id, name: c.name }))
      );
    }
  }, [containersData]);

  const handleCreateAlert = useCallback(
    async (data: AlertFormData) => {
      try {
        await createAlert("/api/alerts", {
          method: "POST",
          data,
        });
        setFormOpen(false);
        fetchAlerts("/api/alerts");
      } catch (error) {
        console.error("Error creating alert:", error);
      }
    },
    [createAlert, fetchAlerts]
  );

  const handleUpdateAlert = useCallback(
    async (data: AlertFormData) => {
      if (!editingAlert) return;

      try {
        await updateAlert(`/api/alerts/${editingAlert.id}`, {
          method: "PUT",
          data,
        });
        setFormOpen(false);
        setEditingAlert(undefined);
        fetchAlerts("/api/alerts");
      } catch (error) {
        console.error("Error updating alert:", error);
      }
    },
    [editingAlert, updateAlert, fetchAlerts]
  );

  const handleDeleteAlert = useCallback(async () => {
    if (!alertToDelete) return;

    try {
      await deleteAlert(`/api/alerts/${alertToDelete.id}`, {
        method: "DELETE",
      });
      setDeleteConfirmOpen(false);
      setAlertToDelete(undefined);
      fetchAlerts("/api/alerts");
    } catch (error) {
      console.error("Error deleting alert:", error);
    }
  }, [alertToDelete, deleteAlert, fetchAlerts]);

  const getAlertStatusIcon = (alert: Alert) => {
    if (!alert.is_active) {
      return <AlertOffIcon color="disabled" />;
    }
    if (alert.is_triggered) {
      return <ErrorIcon color="error" />;
    }
    return <CheckCircleIcon color="success" />;
  };

  const getAlertStatusColor = (alert: Alert) => {
    if (!alert.is_active) return "default";
    if (alert.is_triggered) return "error";
    return "success";
  };

  const getAlertStatusLabel = (alert: Alert) => {
    if (!alert.is_active) return "Inactive";
    if (alert.is_triggered) return "Triggered";
    return "Active";
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="h4">Alerts Management</Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setFormOpen(true)}
            disabled={containersLoading}
          >
            Create Alert
          </Button>
        </Box>
        <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
          Configure and manage container metrics alerts with real-time
          notifications.
        </Typography>
      </Paper>

      {/* Alerts Summary */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h4" color="primary">
                {alerts.length}
              </Typography>
              <Typography color="textSecondary">Total Alerts</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h4" color="success.main">
                {alerts.filter((a) => a.is_active && !a.is_triggered).length}
              </Typography>
              <Typography color="textSecondary">Active</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h4" color="error.main">
                {alerts.filter((a) => a.is_triggered).length}
              </Typography>
              <Typography color="textSecondary">Triggered</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h4" color="text.disabled">
                {alerts.filter((a) => !a.is_active).length}
              </Typography>
              <Typography color="textSecondary">Inactive</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Alerts Table */}
      <Paper elevation={2}>
        {alertsLoading ? (
          <Box display="flex" justifyContent="center" p={4}>
            <CircularProgress />
          </Box>
        ) : alerts.length === 0 ? (
          <Box p={4} textAlign="center">
            <AlertIcon color="disabled" sx={{ fontSize: 48, mb: 2 }} />
            <Typography variant="h6" color="textSecondary" gutterBottom>
              No alerts configured
            </Typography>
            <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
              Create your first alert to monitor container metrics.
            </Typography>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setFormOpen(true)}
            >
              Create Alert
            </Button>
          </Box>
        ) : (
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Status</TableCell>
                  <TableCell>Name</TableCell>
                  <TableCell>Container</TableCell>
                  <TableCell>Metric</TableCell>
                  <TableCell>Condition</TableCell>
                  <TableCell>Triggers</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {alerts.map((alert) => (
                  <TableRow key={alert.id}>
                    <TableCell>
                      <Box display="flex" alignItems="center" gap={1}>
                        {getAlertStatusIcon(alert)}
                        <Chip
                          label={getAlertStatusLabel(alert)}
                          color={getAlertStatusColor(alert)}
                          size="small"
                          variant="outlined"
                        />
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Typography variant="subtitle2">{alert.name}</Typography>
                      {alert.description && (
                        <Typography variant="caption" color="textSecondary">
                          {alert.description}
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {alert.container_name}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {alert.metric_type?.replace("_", " ") ||
                          "Unknown Metric"}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {alert.comparison_operator} {alert.threshold_value}
                        {alert.metric_type?.includes("percent") ? "%" : ""}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {alert.trigger_count}
                      </Typography>
                      {alert.last_triggered_at && (
                        <Typography variant="caption" color="textSecondary">
                          Last:{" "}
                          {new Date(alert.last_triggered_at).toLocaleString()}
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      <Box display="flex" gap={1}>
                        <Tooltip title="Edit">
                          <IconButton
                            size="small"
                            onClick={() => {
                              setEditingAlert(alert);
                              setFormOpen(true);
                            }}
                          >
                            <EditIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Delete">
                          <IconButton
                            size="small"
                            onClick={() => {
                              setAlertToDelete(alert);
                              setDeleteConfirmOpen(true);
                            }}
                          >
                            <DeleteIcon />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>

      {/* Alert Form Dialog */}
      <AlertForm
        open={formOpen}
        onClose={() => {
          setFormOpen(false);
          setEditingAlert(undefined);
        }}
        onSubmit={editingAlert ? handleUpdateAlert : handleCreateAlert}
        alert={editingAlert}
        containers={containers}
        loading={createLoading || updateLoading}
      />

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteConfirmOpen}
        onClose={() => setDeleteConfirmOpen(false)}
      >
        <DialogTitle>Delete Alert</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete the alert "{alertToDelete?.name}"?
            This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteConfirmOpen(false)}>Cancel</Button>
          <Button
            onClick={handleDeleteAlert}
            color="error"
            variant="contained"
            disabled={deleteLoading}
          >
            {deleteLoading ? <CircularProgress size={20} /> : "Delete"}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AlertsManagement;
