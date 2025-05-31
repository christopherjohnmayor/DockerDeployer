import React, { useState, useEffect } from "react";
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
  // Switch,
  // FormControlLabel,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Chip,
  Alert,
  Grid,
} from "@mui/material";
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Notifications as NotificationsIcon,
  NotificationsOff as NotificationsOffIcon,
} from "@mui/icons-material";
import { useApiCall } from "../hooks/useApiCall";

interface MetricsAlert {
  id: number;
  name: string;
  description?: string;
  container_id: string;
  container_name?: string;
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

interface AlertsManagerProps {
  containerId?: string;
}

const AlertsManager: React.FC<AlertsManagerProps> = ({ containerId }) => {
  const [alerts, setAlerts] = useState<MetricsAlert[]>([]);
  const [openDialog, setOpenDialog] = useState(false);
  const [editingAlert, setEditingAlert] = useState<MetricsAlert | null>(null);
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    container_id: containerId || "",
    metric_type: "cpu_percent",
    threshold_value: 80,
    comparison_operator: ">",
  });

  const {
    execute: fetchAlerts,
    loading: alertsLoading,
    error: alertsError,
  } = useApiCall();
  const { execute: createAlert, loading: createLoading } = useApiCall();
  const { execute: updateAlert, loading: updateLoading } = useApiCall();
  const { execute: deleteAlert, loading: deleteLoading } = useApiCall();

  const metricTypes = [
    { value: "cpu_percent", label: "CPU Usage (%)" },
    { value: "memory_percent", label: "Memory Usage (%)" },
    { value: "network_rx", label: "Network RX (MB)" },
    { value: "network_tx", label: "Network TX (MB)" },
    { value: "block_read", label: "Disk Read (MB)" },
    { value: "block_write", label: "Disk Write (MB)" },
  ];

  const comparisonOperators = [
    { value: ">", label: "Greater than (>)" },
    { value: "<", label: "Less than (<)" },
    { value: ">=", label: "Greater than or equal (>=)" },
    { value: "<=", label: "Less than or equal (<=)" },
    { value: "==", label: "Equal to (==)" },
    { value: "!=", label: "Not equal to (!=)" },
  ];

  // Fetch alerts on component mount
  useEffect(() => {
    loadAlerts();
  }, []);

  const loadAlerts = async () => {
    try {
      const response = await fetchAlerts("/api/alerts");
      if (response && Array.isArray(response)) {
        setAlerts(response);
      }
    } catch (error) {
      console.error("Error loading alerts:", error);
    }
  };

  const handleOpenDialog = (alert?: MetricsAlert) => {
    if (alert) {
      setEditingAlert(alert);
      setFormData({
        name: alert.name,
        description: alert.description || "",
        container_id: alert.container_id,
        metric_type: alert.metric_type,
        threshold_value: alert.threshold_value,
        comparison_operator: alert.comparison_operator,
      });
    } else {
      setEditingAlert(null);
      setFormData({
        name: "",
        description: "",
        container_id: containerId || "",
        metric_type: "cpu_percent",
        threshold_value: 80,
        comparison_operator: ">",
      });
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setEditingAlert(null);
  };

  const handleSaveAlert = async () => {
    try {
      if (editingAlert) {
        // Update existing alert
        await updateAlert(`/api/alerts/${editingAlert.id}`, {
          method: "PUT",
          body: JSON.stringify(formData),
          headers: { "Content-Type": "application/json" },
        });
      } else {
        // Create new alert
        await createAlert("/api/alerts", {
          method: "POST",
          body: JSON.stringify(formData),
          headers: { "Content-Type": "application/json" },
        });
      }

      handleCloseDialog();
      loadAlerts();
    } catch (error) {
      console.error("Error saving alert:", error);
    }
  };

  const handleDeleteAlert = async (alertId: number) => {
    if (window.confirm("Are you sure you want to delete this alert?")) {
      try {
        await deleteAlert(`/api/alerts/${alertId}`, { method: "DELETE" });
        loadAlerts();
      } catch (error) {
        console.error("Error deleting alert:", error);
      }
    }
  };

  const handleToggleAlert = async (alert: MetricsAlert) => {
    try {
      await updateAlert(`/api/alerts/${alert.id}`, {
        method: "PUT",
        body: JSON.stringify({ ...alert, is_active: !alert.is_active }),
        headers: { "Content-Type": "application/json" },
      });
      loadAlerts();
    } catch (error) {
      console.error("Error toggling alert:", error);
    }
  };

  const getStatusColor = (alert: MetricsAlert) => {
    if (!alert.is_active) return "default";
    if (alert.is_triggered) return "error";
    return "success";
  };

  const getStatusLabel = (alert: MetricsAlert) => {
    if (!alert.is_active) return "Disabled";
    if (alert.is_triggered) return "Triggered";
    return "Active";
  };

  return (
    <Box>
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box
          display="flex"
          justifyContent="space-between"
          alignItems="center"
          mb={3}
        >
          <Typography variant="h6">
            Metrics Alerts
            {containerId && ` for Container ${containerId}`}
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => handleOpenDialog()}
            disabled={createLoading}
          >
            Create Alert
          </Button>
        </Box>

        {alertsError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            Failed to load alerts: {alertsError}
          </Alert>
        )}

        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>Container</TableCell>
                <TableCell>Metric</TableCell>
                <TableCell>Condition</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Triggers</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {alerts
                .filter(
                  (alert) => !containerId || alert.container_id === containerId
                )
                .map((alert) => (
                  <TableRow key={alert.id}>
                    <TableCell>
                      <Typography variant="body2" fontWeight="medium">
                        {alert.name}
                      </Typography>
                      {alert.description && (
                        <Typography variant="caption" color="textSecondary">
                          {alert.description}
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {alert.container_name || alert.container_id}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {metricTypes.find((m) => m.value === alert.metric_type)
                          ?.label || alert.metric_type}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {alert.comparison_operator} {alert.threshold_value}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={getStatusLabel(alert)}
                        color={getStatusColor(alert)}
                        size="small"
                        icon={
                          alert.is_active ? (
                            <NotificationsIcon />
                          ) : (
                            <NotificationsOffIcon />
                          )
                        }
                      />
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
                      <IconButton
                        size="small"
                        onClick={() => handleToggleAlert(alert)}
                        color={alert.is_active ? "primary" : "default"}
                        aria-label={
                          alert.is_active ? "Disable alert" : "Enable alert"
                        }
                      >
                        {alert.is_active ? (
                          <NotificationsIcon />
                        ) : (
                          <NotificationsOffIcon />
                        )}
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => handleOpenDialog(alert)}
                        aria-label="Edit alert"
                      >
                        <EditIcon />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => handleDeleteAlert(alert.id)}
                        color="error"
                        aria-label="Delete alert"
                      >
                        <DeleteIcon />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
            </TableBody>
          </Table>
        </TableContainer>

        {alerts.length === 0 && !alertsLoading && (
          <Box textAlign="center" py={4}>
            <Typography color="textSecondary">
              No alerts configured. Create your first alert to get notified
              about container metrics.
            </Typography>
          </Box>
        )}
      </Paper>

      {/* Create/Edit Alert Dialog */}
      <Dialog
        open={openDialog}
        onClose={handleCloseDialog}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          {editingAlert ? "Edit Alert" : "Create New Alert"}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Alert Name"
                value={formData.name}
                onChange={(e) =>
                  setFormData({ ...formData, name: e.target.value })
                }
                required
              />
            </Grid>

            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Description"
                value={formData.description}
                onChange={(e) =>
                  setFormData({ ...formData, description: e.target.value })
                }
                multiline
                rows={2}
              />
            </Grid>

            {!containerId && (
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Container ID"
                  value={formData.container_id}
                  onChange={(e) =>
                    setFormData({ ...formData, container_id: e.target.value })
                  }
                  required
                />
              </Grid>
            )}

            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Metric Type</InputLabel>
                <Select
                  value={formData.metric_type}
                  label="Metric Type"
                  onChange={(e) =>
                    setFormData({ ...formData, metric_type: e.target.value })
                  }
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
              <FormControl fullWidth>
                <InputLabel>Condition</InputLabel>
                <Select
                  value={formData.comparison_operator}
                  label="Condition"
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      comparison_operator: e.target.value,
                    })
                  }
                >
                  {comparisonOperators.map((op) => (
                    <MenuItem key={op.value} value={op.value}>
                      {op.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Threshold Value"
                type="number"
                value={formData.threshold_value}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    threshold_value: Number(e.target.value),
                  })
                }
                required
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button
            onClick={handleSaveAlert}
            variant="contained"
            disabled={
              createLoading ||
              updateLoading ||
              !formData.name ||
              !formData.container_id
            }
          >
            {editingAlert ? "Update" : "Create"}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AlertsManager;
