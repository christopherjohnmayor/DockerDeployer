import React, { useState, useEffect, useContext, useCallback } from "react";
import {
  Badge,
  IconButton,
  Menu,
  MenuItem,
  Typography,
  Box,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
  Button,
  Divider,
  Alert,
  Snackbar,
} from "@mui/material";
import {
  Notifications as NotificationsIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  CheckCircle as CheckCircleIcon,
  Clear as ClearIcon,
} from "@mui/icons-material";
import { format } from "date-fns";

import { AuthContext } from "../contexts/AuthContext";
import { useWebSocket } from "../hooks/useWebSocket";
import { getNotificationWebSocketUrl } from "../utils/websocket";

interface AlertNotification {
  type: string;
  timestamp: string;
  alert?: {
    id: number;
    name: string;
    description: string;
    container_id: string;
    container_name: string;
    metric_type: string;
    threshold_value: number;
    comparison_operator: string;
    current_value: number;
  };
  severity?: string;
  message?: string;
  notification_type?: string;
}

interface AlertNotificationsProps {
  maxNotifications?: number;
}

const AlertNotifications: React.FC<AlertNotificationsProps> = ({
  maxNotifications = 50,
}) => {
  const { user, token } = useContext(AuthContext);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [notifications, setNotifications] = useState<AlertNotification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState("");
  const [snackbarSeverity, setSnackbarSeverity] = useState<
    "success" | "error" | "warning" | "info"
  >("info");

  // WebSocket connection for real-time notifications
  const { isConnected, sendMessage } = useWebSocket(
    user && token ? getNotificationWebSocketUrl(user.id, token) : null,
    {
      onMessage: handleWebSocketMessage,
      onConnect: () => {
        console.log("Connected to notification service");
        // Request notification history when connected
        sendMessage({
          type: "get_notification_history",
          limit: maxNotifications,
        });
      },
      onDisconnect: () => {
        console.log("Disconnected from notification service");
      },
      onError: (error) => {
        console.error("WebSocket error:", error);
        showSnackbar(
          "Connection error. Notifications may be delayed.",
          "error"
        );
      },
    }
  );

  function handleWebSocketMessage(event: MessageEvent) {
    try {
      const data = JSON.parse(event.data);

      switch (data.type) {
        case "connection_established":
          console.log("Notification connection established");
          break;

        case "alert_triggered":
          handleAlertTriggered(data);
          break;

        case "alert_acknowledged":
          handleAlertAcknowledged(data);
          break;

        case "notification_history":
          setNotifications(data.notifications || []);
          setUnreadCount(data.notifications?.length || 0);
          break;

        case "pending_notification":
          addNotification(data);
          break;

        case "system_notification":
        case "user_notification":
          handleSystemNotification(data);
          break;

        case "error":
          console.error("WebSocket error:", data.message);
          showSnackbar(data.message, "error");
          break;

        default:
          console.log("Unknown notification type:", data.type);
      }
    } catch (error) {
      console.error("Error parsing WebSocket message:", error);
    }
  }

  const handleAlertTriggered = useCallback((data: AlertNotification) => {
    addNotification(data);

    // Show browser notification if permission granted
    if (Notification.permission === "granted" && data.alert) {
      new Notification(`DockerDeployer Alert: ${data.alert.name}`, {
        body:
          data.message ||
          `${data.alert.metric_type} is ${data.alert.current_value} (threshold: ${data.alert.comparison_operator} ${data.alert.threshold_value})`,
        icon: "/favicon.ico",
        tag: `alert-${data.alert.id}`,
      });
    }

    // Show snackbar for immediate feedback
    showSnackbar(
      `Alert triggered: ${data.alert?.name || "Unknown alert"}`,
      data.severity === "critical" ? "error" : "warning"
    );
  }, []);

  const handleAlertAcknowledged = useCallback((data: any) => {
    // Update notifications to mark alert as acknowledged
    setNotifications((prev) =>
      prev.map((notification) =>
        notification.alert?.id === data.alert_id
          ? { ...notification, acknowledged: true }
          : notification
      )
    );

    showSnackbar("Alert acknowledged", "success");
  }, []);

  const handleSystemNotification = useCallback((data: AlertNotification) => {
    addNotification(data);
    showSnackbar(
      data.message || "System notification",
      (data.notification_type as any) || "info"
    );
  }, []);

  const addNotification = useCallback(
    (notification: AlertNotification) => {
      setNotifications((prev) => {
        const updated = [notification, ...prev].slice(0, maxNotifications);
        return updated;
      });
      setUnreadCount((prev) => prev + 1);
    },
    [maxNotifications]
  );

  const showSnackbar = useCallback(
    (message: string, severity: "success" | "error" | "warning" | "info") => {
      setSnackbarMessage(message);
      setSnackbarSeverity(severity);
      setSnackbarOpen(true);
    },
    []
  );

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
    setUnreadCount(0); // Mark as read when opened
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const acknowledgeAlert = async (alertId: number) => {
    try {
      sendMessage({
        type: "acknowledge_alert",
        alert_id: alertId,
      });
    } catch (error) {
      console.error("Error acknowledging alert:", error);
      showSnackbar("Failed to acknowledge alert", "error");
    }
  };

  const clearNotifications = () => {
    setNotifications([]);
    setUnreadCount(0);
    handleMenuClose();
  };

  const getSeverityIcon = (severity?: string) => {
    switch (severity) {
      case "critical":
        return <ErrorIcon color="error" />;
      case "warning":
        return <WarningIcon color="warning" />;
      case "info":
        return <InfoIcon color="info" />;
      default:
        return <NotificationsIcon />;
    }
  };

  const getSeverityColor = (severity?: string) => {
    switch (severity) {
      case "critical":
        return "error";
      case "warning":
        return "warning";
      case "info":
        return "info";
      default:
        return "default";
    }
  };

  // Request notification permission on mount
  useEffect(() => {
    if (Notification.permission === "default") {
      Notification.requestPermission();
    }
  }, []);

  if (!user) {
    return null;
  }

  return (
    <>
      <IconButton
        color="inherit"
        onClick={handleMenuOpen}
        aria-label="notifications"
      >
        <Badge badgeContent={unreadCount} color="error">
          <NotificationsIcon />
        </Badge>
      </IconButton>

      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
        PaperProps={{
          style: {
            maxHeight: 400,
            width: 400,
          },
        }}
      >
        <Box sx={{ p: 2, borderBottom: 1, borderColor: "divider" }}>
          <Typography variant="h6">
            Notifications
            {!isConnected && (
              <Chip label="Offline" color="error" size="small" sx={{ ml: 1 }} />
            )}
          </Typography>
        </Box>

        {notifications.length === 0 ? (
          <MenuItem disabled>
            <Typography variant="body2" color="text.secondary">
              No notifications
            </Typography>
          </MenuItem>
        ) : (
          <>
            <List sx={{ maxHeight: 300, overflow: "auto" }}>
              {notifications.map((notification, index) => (
                <ListItem key={index} divider>
                  <ListItemIcon>
                    {getSeverityIcon(notification.severity)}
                  </ListItemIcon>
                  <ListItemText
                    primaryTypographyProps={{ component: "div" }}
                    secondaryTypographyProps={{ component: "div" }}
                    primary={
                      <Box
                        component="div"
                        sx={{ display: "flex", alignItems: "center", gap: 1 }}
                      >
                        <Typography variant="subtitle2" component="span">
                          {notification.alert?.name || "System Notification"}
                        </Typography>
                        <Chip
                          label={notification.severity || "info"}
                          color={getSeverityColor(notification.severity) as any}
                          size="small"
                        />
                      </Box>
                    }
                    secondary={
                      <Box component="div">
                        <Typography
                          variant="body2"
                          color="text.secondary"
                          component="div"
                        >
                          {notification.message ||
                            notification.alert?.description}
                        </Typography>
                        <Typography
                          variant="caption"
                          color="text.secondary"
                          component="div"
                        >
                          {format(
                            new Date(notification.timestamp),
                            "MMM dd, HH:mm"
                          )}
                        </Typography>
                        {notification.alert && !notification.acknowledged && (
                          <Button
                            size="small"
                            startIcon={<CheckCircleIcon />}
                            onClick={() =>
                              acknowledgeAlert(notification.alert!.id)
                            }
                            sx={{ mt: 1 }}
                          >
                            Acknowledge
                          </Button>
                        )}
                      </Box>
                    }
                  />
                </ListItem>
              ))}
            </List>
            <Divider />
            <MenuItem onClick={clearNotifications}>
              <ClearIcon sx={{ mr: 1 }} />
              Clear All
            </MenuItem>
          </>
        )}
      </Menu>

      <Snackbar
        open={snackbarOpen}
        autoHideDuration={6000}
        onClose={() => setSnackbarOpen(false)}
        anchorOrigin={{ vertical: "top", horizontal: "right" }}
      >
        <Alert
          onClose={() => setSnackbarOpen(false)}
          severity={snackbarSeverity}
          variant="filled"
        >
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </>
  );
};

export default AlertNotifications;
