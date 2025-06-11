import React from "react";
import {
  render,
  screen,
  fireEvent,
  waitFor,
  act,
} from "@testing-library/react";
import { ThemeProvider } from "@mui/material/styles";
import AlertNotifications from "../AlertNotifications";
import { AuthContext } from "../../contexts/AuthContext";
import { useWebSocket } from "../../hooks/useWebSocket";
import theme from "../../theme";

// Mock the useWebSocket hook
jest.mock("../../hooks/useWebSocket");
const mockUseWebSocket = useWebSocket as jest.MockedFunction<
  typeof useWebSocket
>;

// Mock the websocket utility
jest.mock("../../utils/websocket", () => ({
  getNotificationWebSocketUrl: jest.fn(
    (userId: number, token: string) =>
      `ws://localhost:8000/ws/notifications/${userId}?token=${token}`
  ),
}));

// Mock date-fns format function
jest.mock("date-fns", () => ({
  format: jest.fn((date: Date, formatStr: string) => {
    if (formatStr === "MMM dd, HH:mm") {
      return "Dec 11, 14:30";
    }
    return date.toISOString();
  }),
}));

// Mock browser Notification API
const mockNotification = jest.fn();
Object.defineProperty(window, "Notification", {
  value: mockNotification,
  configurable: true,
});

Object.defineProperty(mockNotification, "permission", {
  value: "granted",
  configurable: true,
});

Object.defineProperty(mockNotification, "requestPermission", {
  value: jest.fn().mockResolvedValue("granted"),
  configurable: true,
});

const renderWithTheme = (component: React.ReactElement) => {
  return render(<ThemeProvider theme={theme}>{component}</ThemeProvider>);
};

const mockAuthContextValue = {
  isAuthenticated: true,
  user: { id: 1, username: "testuser", role: "user" },
  token: "mock-jwt-token",
  login: jest.fn(),
  logout: jest.fn(),
  refreshAuth: jest.fn(),
};

const mockWebSocketReturn = {
  isConnected: true,
  sendMessage: jest.fn(),
  disconnect: jest.fn(),
  reconnect: jest.fn(),
  connectionState: "connected" as const,
};

const mockAlertNotification = {
  type: "alert_triggered",
  timestamp: new Date().toISOString(),
  severity: "critical",
  message: "High CPU usage detected",
  alert: {
    id: 1,
    name: "CPU Alert",
    description: "CPU usage is above threshold",
    container_id: "container123",
    container_name: "web-server",
    metric_type: "cpu_percent",
    threshold_value: 80,
    comparison_operator: ">",
    current_value: 95.5,
  },
};

const mockSystemNotification = {
  type: "system_notification",
  timestamp: new Date().toISOString(),
  severity: "info",
  message: "System maintenance scheduled",
  notification_type: "info",
};

const renderAlertNotifications = (props = {}) => {
  return renderWithTheme(
    <AuthContext.Provider value={mockAuthContextValue}>
      <AlertNotifications {...props} />
    </AuthContext.Provider>
  );
};

describe("AlertNotifications", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseWebSocket.mockReturnValue(mockWebSocketReturn);

    // Reset Notification mock
    mockNotification.mockClear();
    Object.defineProperty(mockNotification, "permission", {
      value: "granted",
      configurable: true,
    });
  });

  afterEach(() => {
    jest.clearAllTimers();
  });

  describe("Component Rendering", () => {
    it("renders notification icon button correctly", () => {
      renderAlertNotifications();

      const notificationButton = screen.getByRole("button", {
        name: /notifications/i,
      });
      expect(notificationButton).toBeInTheDocument();
    });

    it("renders with default maxNotifications prop", () => {
      renderAlertNotifications();

      expect(mockUseWebSocket).toHaveBeenCalledWith(
        "ws://localhost:8000/ws/notifications/1?token=mock-jwt-token",
        expect.objectContaining({
          onMessage: expect.any(Function),
          onConnect: expect.any(Function),
          onDisconnect: expect.any(Function),
          onError: expect.any(Function),
        })
      );
    });

    it("renders with custom maxNotifications prop", () => {
      renderAlertNotifications({ maxNotifications: 25 });

      // Component should render normally with custom prop
      const notificationButton = screen.getByRole("button", {
        name: /notifications/i,
      });
      expect(notificationButton).toBeInTheDocument();
    });

    it("does not render when user is not authenticated", () => {
      const unauthenticatedContext = {
        ...mockAuthContextValue,
        user: null,
        isAuthenticated: false,
      };

      renderWithTheme(
        <AuthContext.Provider value={unauthenticatedContext}>
          <AlertNotifications />
        </AuthContext.Provider>
      );

      const notificationButton = screen.queryByRole("button", {
        name: /notifications/i,
      });
      expect(notificationButton).not.toBeInTheDocument();
    });

    it("shows unread count badge when notifications exist", async () => {
      renderAlertNotifications();

      // Simulate receiving a notification
      const onMessage = mockUseWebSocket.mock.calls[0][1].onMessage;

      await act(async () => {
        onMessage({
          data: JSON.stringify(mockAlertNotification),
        } as MessageEvent);
      });

      await waitFor(
        () => {
          const badge = screen.getByText("1");
          expect(badge).toBeInTheDocument();
        },
        { timeout: 20000 }
      );
    });
  });

  describe("Menu Interaction", () => {
    it("opens notification menu when button is clicked", async () => {
      renderAlertNotifications();

      const notificationButton = screen.getByRole("button", {
        name: /notifications/i,
      });

      await act(async () => {
        fireEvent.click(notificationButton);
      });

      await waitFor(
        () => {
          expect(screen.getByText("Notifications")).toBeInTheDocument();
        },
        { timeout: 20000 }
      );
    });

    it("shows offline indicator when WebSocket is disconnected", async () => {
      mockUseWebSocket.mockReturnValue({
        ...mockWebSocketReturn,
        isConnected: false,
      });

      renderAlertNotifications();

      const notificationButton = screen.getByRole("button", {
        name: /notifications/i,
      });

      await act(async () => {
        fireEvent.click(notificationButton);
      });

      await waitFor(
        () => {
          expect(screen.getByText("Offline")).toBeInTheDocument();
        },
        { timeout: 20000 }
      );
    });

    it("shows 'No notifications' message when list is empty", async () => {
      renderAlertNotifications();

      const notificationButton = screen.getByRole("button", {
        name: /notifications/i,
      });

      await act(async () => {
        fireEvent.click(notificationButton);
      });

      await waitFor(
        () => {
          expect(screen.getByText("No notifications")).toBeInTheDocument();
        },
        { timeout: 20000 }
      );
    });

    it("closes menu when clicking outside", async () => {
      renderAlertNotifications();

      const notificationButton = screen.getByRole("button", {
        name: /notifications/i,
      });

      await act(async () => {
        fireEvent.click(notificationButton);
      });

      await waitFor(
        () => {
          expect(screen.getByText("Notifications")).toBeInTheDocument();
        },
        { timeout: 20000 }
      );

      await act(async () => {
        fireEvent.keyDown(document, { key: "Escape" });
      });

      await waitFor(
        () => {
          expect(screen.queryByText("Notifications")).not.toBeInTheDocument();
        },
        { timeout: 20000 }
      );
    }, 30000);

    it("resets unread count when menu is opened", async () => {
      renderAlertNotifications();

      // Add a notification first
      const onMessage = mockUseWebSocket.mock.calls[0][1].onMessage;

      await act(async () => {
        onMessage({
          data: JSON.stringify(mockAlertNotification),
        } as MessageEvent);
      });

      // Verify badge shows count
      await waitFor(
        () => {
          expect(screen.getByText("1")).toBeInTheDocument();
        },
        { timeout: 20000 }
      );

      // Open menu
      const notificationButton = screen.getByRole("button", {
        name: /notifications/i,
      });

      await act(async () => {
        fireEvent.click(notificationButton);
      });

      // Close menu
      await act(async () => {
        fireEvent.keyDown(document, { key: "Escape" });
      });

      // Badge should be gone (count reset to 0)
      await waitFor(
        () => {
          expect(screen.queryByText("1")).not.toBeInTheDocument();
        },
        { timeout: 20000 }
      );
    }, 30000);
  });

  describe("WebSocket Integration", () => {
    it("establishes WebSocket connection on mount with authenticated user", () => {
      renderAlertNotifications();

      expect(mockUseWebSocket).toHaveBeenCalledWith(
        "ws://localhost:8000/ws/notifications/1?token=mock-jwt-token",
        expect.objectContaining({
          onMessage: expect.any(Function),
          onConnect: expect.any(Function),
          onDisconnect: expect.any(Function),
          onError: expect.any(Function),
        })
      );
    });

    it("does not establish WebSocket connection when user is null", () => {
      const unauthenticatedContext = {
        ...mockAuthContextValue,
        user: null,
      };

      renderWithTheme(
        <AuthContext.Provider value={unauthenticatedContext}>
          <AlertNotifications />
        </AuthContext.Provider>
      );

      expect(mockUseWebSocket).toHaveBeenCalledWith(null, expect.any(Object));
    });

    it("does not establish WebSocket connection when token is null", () => {
      const noTokenContext = {
        ...mockAuthContextValue,
        token: null,
      };

      renderWithTheme(
        <AuthContext.Provider value={noTokenContext}>
          <AlertNotifications />
        </AuthContext.Provider>
      );

      expect(mockUseWebSocket).toHaveBeenCalledWith(null, expect.any(Object));
    });

    it("handles WebSocket connection established", async () => {
      const consoleSpy = jest.spyOn(console, "log").mockImplementation();

      renderAlertNotifications();

      const onConnect = mockUseWebSocket.mock.calls[0][1].onConnect;

      await act(async () => {
        onConnect();
      });

      expect(consoleSpy).toHaveBeenCalledWith(
        "Connected to notification service"
      );
      expect(mockWebSocketReturn.sendMessage).toHaveBeenCalledWith({
        type: "get_notification_history",
        limit: 50,
      });

      consoleSpy.mockRestore();
    });

    it("handles WebSocket disconnection", async () => {
      const consoleSpy = jest.spyOn(console, "log").mockImplementation();

      renderAlertNotifications();

      const onDisconnect = mockUseWebSocket.mock.calls[0][1].onDisconnect;

      await act(async () => {
        onDisconnect();
      });

      expect(consoleSpy).toHaveBeenCalledWith(
        "Disconnected from notification service"
      );
      consoleSpy.mockRestore();
    });

    it("handles WebSocket error", async () => {
      const consoleSpy = jest.spyOn(console, "error").mockImplementation();

      renderAlertNotifications();

      const onError = mockUseWebSocket.mock.calls[0][1].onError;
      const mockError = new Event("error");

      await act(async () => {
        onError(mockError);
      });

      expect(consoleSpy).toHaveBeenCalledWith("WebSocket error:", mockError);

      // Should show snackbar error message
      await waitFor(
        () => {
          expect(
            screen.getByText("Connection error. Notifications may be delayed.")
          ).toBeInTheDocument();
        },
        { timeout: 20000 }
      );

      consoleSpy.mockRestore();
    });

    it("requests notification history with custom maxNotifications", async () => {
      renderAlertNotifications({ maxNotifications: 25 });

      const onConnect = mockUseWebSocket.mock.calls[0][1].onConnect;

      await act(async () => {
        onConnect();
      });

      expect(mockWebSocketReturn.sendMessage).toHaveBeenCalledWith({
        type: "get_notification_history",
        limit: 25,
      });
    });
  });

  describe("WebSocket Message Handling", () => {
    it("handles connection_established message", async () => {
      const consoleSpy = jest.spyOn(console, "log").mockImplementation();

      renderAlertNotifications();

      const onMessage = mockUseWebSocket.mock.calls[0][1].onMessage;

      await act(async () => {
        onMessage({
          data: JSON.stringify({
            type: "connection_established",
          }),
        } as MessageEvent);
      });

      expect(consoleSpy).toHaveBeenCalledWith(
        "Notification connection established"
      );
      consoleSpy.mockRestore();
    });

    it("handles alert_triggered message", async () => {
      renderAlertNotifications();

      const onMessage = mockUseWebSocket.mock.calls[0][1].onMessage;

      await act(async () => {
        onMessage({
          data: JSON.stringify(mockAlertNotification),
        } as MessageEvent);
      });

      // Should show snackbar
      await waitFor(
        () => {
          expect(
            screen.getByText("Alert triggered: CPU Alert")
          ).toBeInTheDocument();
        },
        { timeout: 20000 }
      );

      // Should create browser notification
      expect(mockNotification).toHaveBeenCalledWith(
        "DockerDeployer Alert: CPU Alert",
        expect.objectContaining({
          body: "High CPU usage detected",
          icon: "/favicon.ico",
          tag: "alert-1",
        })
      );
    });

    it("handles alert_triggered message without browser notification permission", async () => {
      Object.defineProperty(mockNotification, "permission", {
        value: "denied",
        configurable: true,
      });

      renderAlertNotifications();

      const onMessage = mockUseWebSocket.mock.calls[0][1].onMessage;

      await act(async () => {
        onMessage({
          data: JSON.stringify(mockAlertNotification),
        } as MessageEvent);
      });

      // Should show snackbar but not browser notification
      await waitFor(
        () => {
          expect(
            screen.getByText("Alert triggered: CPU Alert")
          ).toBeInTheDocument();
        },
        { timeout: 20000 }
      );

      expect(mockNotification).not.toHaveBeenCalled();
    });

    it("handles alert_acknowledged message", async () => {
      renderAlertNotifications();

      const onMessage = mockUseWebSocket.mock.calls[0][1].onMessage;

      // First add an alert
      await act(async () => {
        onMessage({
          data: JSON.stringify(mockAlertNotification),
        } as MessageEvent);
      });

      // Then acknowledge it
      await act(async () => {
        onMessage({
          data: JSON.stringify({
            type: "alert_acknowledged",
            alert_id: 1,
          }),
        } as MessageEvent);
      });

      await waitFor(
        () => {
          expect(screen.getByText("Alert acknowledged")).toBeInTheDocument();
        },
        { timeout: 20000 }
      );
    });

    it("handles notification_history message", async () => {
      renderAlertNotifications();

      const onMessage = mockUseWebSocket.mock.calls[0][1].onMessage;
      const historyNotifications = [
        mockAlertNotification,
        mockSystemNotification,
      ];

      await act(async () => {
        onMessage({
          data: JSON.stringify({
            type: "notification_history",
            notifications: historyNotifications,
          }),
        } as MessageEvent);
      });

      // Open menu to see notifications
      const notificationButton = screen.getByRole("button", {
        name: /notifications/i,
      });

      await act(async () => {
        fireEvent.click(notificationButton);
      });

      await waitFor(
        () => {
          expect(screen.getByText("CPU Alert")).toBeInTheDocument();
          expect(screen.getByText("System Notification")).toBeInTheDocument();
        },
        { timeout: 20000 }
      );
    });

    it("handles pending_notification message", async () => {
      renderAlertNotifications();

      const onMessage = mockUseWebSocket.mock.calls[0][1].onMessage;

      await act(async () => {
        onMessage({
          data: JSON.stringify({
            type: "pending_notification",
            ...mockSystemNotification,
          }),
        } as MessageEvent);
      });

      // Should increment unread count
      await waitFor(
        () => {
          expect(screen.getByText("1")).toBeInTheDocument();
        },
        { timeout: 20000 }
      );
    });

    it("handles system_notification message", async () => {
      renderAlertNotifications();

      const onMessage = mockUseWebSocket.mock.calls[0][1].onMessage;

      await act(async () => {
        onMessage({
          data: JSON.stringify({
            type: "system_notification",
            ...mockSystemNotification,
          }),
        } as MessageEvent);
      });

      await waitFor(
        () => {
          expect(
            screen.getByText("System maintenance scheduled")
          ).toBeInTheDocument();
        },
        { timeout: 20000 }
      );
    });

    it("handles user_notification message", async () => {
      renderAlertNotifications();

      const onMessage = mockUseWebSocket.mock.calls[0][1].onMessage;

      await act(async () => {
        onMessage({
          data: JSON.stringify({
            type: "user_notification",
            message: "User-specific notification",
            notification_type: "warning",
          }),
        } as MessageEvent);
      });

      await waitFor(
        () => {
          expect(
            screen.getByText("User-specific notification")
          ).toBeInTheDocument();
        },
        { timeout: 20000 }
      );
    });

    it("handles error message", async () => {
      const consoleSpy = jest.spyOn(console, "error").mockImplementation();

      renderAlertNotifications();

      const onMessage = mockUseWebSocket.mock.calls[0][1].onMessage;

      await act(async () => {
        onMessage({
          data: JSON.stringify({
            type: "error",
            message: "WebSocket error occurred",
          }),
        } as MessageEvent);
      });

      expect(consoleSpy).toHaveBeenCalledWith(
        "WebSocket error:",
        "WebSocket error occurred"
      );

      await waitFor(
        () => {
          expect(
            screen.getByText("WebSocket error occurred")
          ).toBeInTheDocument();
        },
        { timeout: 20000 }
      );

      consoleSpy.mockRestore();
    });

    it("handles unknown message type", async () => {
      const consoleSpy = jest.spyOn(console, "log").mockImplementation();

      renderAlertNotifications();

      const onMessage = mockUseWebSocket.mock.calls[0][1].onMessage;

      await act(async () => {
        onMessage({
          data: JSON.stringify({
            type: "unknown_type",
            data: "some data",
          }),
        } as MessageEvent);
      });

      expect(consoleSpy).toHaveBeenCalledWith(
        "Unknown notification type:",
        "unknown_type"
      );
      consoleSpy.mockRestore();
    });

    it("handles invalid JSON message", async () => {
      const consoleSpy = jest.spyOn(console, "error").mockImplementation();

      renderAlertNotifications();

      const onMessage = mockUseWebSocket.mock.calls[0][1].onMessage;

      await act(async () => {
        onMessage({
          data: "invalid json {",
        } as MessageEvent);
      });

      expect(consoleSpy).toHaveBeenCalledWith(
        "Error parsing WebSocket message:",
        expect.any(Error)
      );
      consoleSpy.mockRestore();
    });
  });

  describe("Notification Management", () => {
    it("displays notification list correctly", async () => {
      renderAlertNotifications();

      const onMessage = mockUseWebSocket.mock.calls[0][1].onMessage;

      // Add notifications
      await act(async () => {
        onMessage({
          data: JSON.stringify({
            type: "notification_history",
            notifications: [mockAlertNotification, mockSystemNotification],
          }),
        } as MessageEvent);
      });

      // Open menu
      const notificationButton = screen.getByRole("button", {
        name: /notifications/i,
      });

      await act(async () => {
        fireEvent.click(notificationButton);
      });

      await waitFor(
        () => {
          expect(screen.getByText("CPU Alert")).toBeInTheDocument();
          expect(screen.getByText("System Notification")).toBeInTheDocument();
          expect(screen.getByText("critical")).toBeInTheDocument();
          expect(screen.getByText("info")).toBeInTheDocument();
          expect(screen.getByText("Dec 11, 14:30")).toBeInTheDocument();
        },
        { timeout: 20000 }
      );
    }, 30000);

    it("shows acknowledge button for unacknowledged alerts", async () => {
      renderAlertNotifications();

      const onMessage = mockUseWebSocket.mock.calls[0][1].onMessage;

      await act(async () => {
        onMessage({
          data: JSON.stringify(mockAlertNotification),
        } as MessageEvent);
      });

      // Open menu
      const notificationButton = screen.getByRole("button", {
        name: /notifications/i,
      });

      await act(async () => {
        fireEvent.click(notificationButton);
      });

      await waitFor(
        () => {
          const acknowledgeButton = screen.getByRole("button", {
            name: /acknowledge/i,
          });
          expect(acknowledgeButton).toBeInTheDocument();
        },
        { timeout: 20000 }
      );
    });

    it("handles acknowledge button click", async () => {
      renderAlertNotifications();

      const onMessage = mockUseWebSocket.mock.calls[0][1].onMessage;

      await act(async () => {
        onMessage({
          data: JSON.stringify(mockAlertNotification),
        } as MessageEvent);
      });

      // Open menu
      const notificationButton = screen.getByRole("button", {
        name: /notifications/i,
      });

      await act(async () => {
        fireEvent.click(notificationButton);
      });

      await waitFor(
        () => {
          const acknowledgeButton = screen.getByRole("button", {
            name: /acknowledge/i,
          });
          expect(acknowledgeButton).toBeInTheDocument();
        },
        { timeout: 20000 }
      );

      const acknowledgeButton = screen.getByRole("button", {
        name: /acknowledge/i,
      });

      await act(async () => {
        fireEvent.click(acknowledgeButton);
      });

      expect(mockWebSocketReturn.sendMessage).toHaveBeenCalledWith({
        type: "acknowledge_alert",
        alert_id: 1,
      });
    });

    it("handles acknowledge error", async () => {
      const consoleSpy = jest.spyOn(console, "error").mockImplementation();

      // Mock sendMessage to throw error
      const mockSendMessageError = jest.fn().mockImplementation(() => {
        throw new Error("Network error");
      });

      mockUseWebSocket.mockReturnValue({
        ...mockWebSocketReturn,
        sendMessage: mockSendMessageError,
      });

      renderAlertNotifications();

      const onMessage = mockUseWebSocket.mock.calls[0][1].onMessage;

      await act(async () => {
        onMessage({
          data: JSON.stringify(mockAlertNotification),
        } as MessageEvent);
      });

      // Open menu
      const notificationButton = screen.getByRole("button", {
        name: /notifications/i,
      });

      await act(async () => {
        fireEvent.click(notificationButton);
      });

      await waitFor(
        () => {
          const acknowledgeButton = screen.getByRole("button", {
            name: /acknowledge/i,
          });
          expect(acknowledgeButton).toBeInTheDocument();
        },
        { timeout: 20000 }
      );

      const acknowledgeButton = screen.getByRole("button", {
        name: /acknowledge/i,
      });

      await act(async () => {
        fireEvent.click(acknowledgeButton);
      });

      expect(consoleSpy).toHaveBeenCalledWith(
        "Error acknowledging alert:",
        expect.any(Error)
      );

      await waitFor(
        () => {
          expect(
            screen.getByText("Failed to acknowledge alert")
          ).toBeInTheDocument();
        },
        { timeout: 20000 }
      );

      consoleSpy.mockRestore();
    });

    it("clears all notifications", async () => {
      renderAlertNotifications();

      const onMessage = mockUseWebSocket.mock.calls[0][1].onMessage;

      // Add notifications
      await act(async () => {
        onMessage({
          data: JSON.stringify({
            type: "notification_history",
            notifications: [mockAlertNotification, mockSystemNotification],
          }),
        } as MessageEvent);
      });

      // Open menu
      const notificationButton = screen.getByRole("button", {
        name: /notifications/i,
      });

      await act(async () => {
        fireEvent.click(notificationButton);
      });

      await waitFor(
        () => {
          expect(screen.getByText("CPU Alert")).toBeInTheDocument();
        },
        { timeout: 20000 }
      );

      // Click clear all
      const clearButton = screen.getByText("Clear All");

      await act(async () => {
        fireEvent.click(clearButton);
      });

      // Menu should close and notifications should be cleared
      await waitFor(
        () => {
          expect(screen.queryByText("Notifications")).not.toBeInTheDocument();
        },
        { timeout: 20000 }
      );

      // Reopen menu to verify notifications are cleared
      await act(async () => {
        fireEvent.click(notificationButton);
      });

      await waitFor(
        () => {
          expect(screen.getByText("No notifications")).toBeInTheDocument();
        },
        { timeout: 20000 }
      );
    });

    it("limits notifications to maxNotifications", async () => {
      renderAlertNotifications({ maxNotifications: 2 });

      const onMessage = mockUseWebSocket.mock.calls[0][1].onMessage;

      // Add 3 notifications
      const notifications = [
        {
          ...mockAlertNotification,
          alert: { ...mockAlertNotification.alert, id: 1, name: "Alert 1" },
        },
        {
          ...mockAlertNotification,
          alert: { ...mockAlertNotification.alert, id: 2, name: "Alert 2" },
        },
        {
          ...mockAlertNotification,
          alert: { ...mockAlertNotification.alert, id: 3, name: "Alert 3" },
        },
      ];

      for (const notification of notifications) {
        await act(async () => {
          onMessage({
            data: JSON.stringify(notification),
          } as MessageEvent);
        });
      }

      // Open menu
      const notificationButton = screen.getByRole("button", {
        name: /notifications/i,
      });

      await act(async () => {
        fireEvent.click(notificationButton);
      });

      // Should only show 2 notifications (most recent)
      await waitFor(
        () => {
          expect(screen.getByText("Alert 3")).toBeInTheDocument();
          expect(screen.getByText("Alert 2")).toBeInTheDocument();
          expect(screen.queryByText("Alert 1")).not.toBeInTheDocument();
        },
        { timeout: 20000 }
      );
    });
  });

  describe("Severity Icons and Colors", () => {
    it("displays correct severity icons", async () => {
      renderAlertNotifications();

      const onMessage = mockUseWebSocket.mock.calls[0][1].onMessage;

      const notifications = [
        { ...mockAlertNotification, severity: "critical" },
        { ...mockAlertNotification, severity: "warning" },
        { ...mockAlertNotification, severity: "info" },
        { ...mockAlertNotification, severity: undefined },
      ];

      await act(async () => {
        onMessage({
          data: JSON.stringify({
            type: "notification_history",
            notifications,
          }),
        } as MessageEvent);
      });

      // Open menu
      const notificationButton = screen.getByRole("button", {
        name: /notifications/i,
      });

      await act(async () => {
        fireEvent.click(notificationButton);
      });

      await waitFor(
        () => {
          // Check that severity chips are displayed
          const criticalChips = screen.getAllByText("critical");
          const warningChips = screen.getAllByText("warning");
          const infoChips = screen.getAllByText("info");

          expect(criticalChips.length).toBeGreaterThan(0);
          expect(warningChips.length).toBeGreaterThan(0);
          expect(infoChips.length).toBeGreaterThan(0);
        },
        { timeout: 20000 }
      );
    });

    it("handles alert without severity", async () => {
      renderAlertNotifications();

      const onMessage = mockUseWebSocket.mock.calls[0][1].onMessage;
      const alertWithoutSeverity = {
        ...mockAlertNotification,
        severity: undefined,
      };

      await act(async () => {
        onMessage({
          data: JSON.stringify(alertWithoutSeverity),
        } as MessageEvent);
      });

      // Should show snackbar with default severity
      await waitFor(
        () => {
          expect(
            screen.getByText("Alert triggered: CPU Alert")
          ).toBeInTheDocument();
        },
        { timeout: 20000 }
      );
    });
  });

  describe("Snackbar Functionality", () => {
    it("shows and hides snackbar messages", async () => {
      renderAlertNotifications();

      const onMessage = mockUseWebSocket.mock.calls[0][1].onMessage;

      await act(async () => {
        onMessage({
          data: JSON.stringify(mockAlertNotification),
        } as MessageEvent);
      });

      // Should show snackbar
      await waitFor(
        () => {
          expect(
            screen.getByText("Alert triggered: CPU Alert")
          ).toBeInTheDocument();
        },
        { timeout: 20000 }
      );

      // Close snackbar
      const closeButton = screen.getByRole("button", { name: /close/i });

      await act(async () => {
        fireEvent.click(closeButton);
      });

      await waitFor(
        () => {
          expect(
            screen.queryByText("Alert triggered: CPU Alert")
          ).not.toBeInTheDocument();
        },
        { timeout: 20000 }
      );
    });

    it("shows different severity snackbars", async () => {
      renderAlertNotifications();

      const onMessage = mockUseWebSocket.mock.calls[0][1].onMessage;

      // Test critical severity
      await act(async () => {
        onMessage({
          data: JSON.stringify({
            ...mockAlertNotification,
            severity: "critical",
          }),
        } as MessageEvent);
      });

      await waitFor(
        () => {
          expect(
            screen.getByText("Alert triggered: CPU Alert")
          ).toBeInTheDocument();
        },
        { timeout: 20000 }
      );

      // Close snackbar
      const closeButton = screen.getByRole("button", { name: /close/i });
      await act(async () => {
        fireEvent.click(closeButton);
      });

      // Test warning severity
      await act(async () => {
        onMessage({
          data: JSON.stringify({
            ...mockAlertNotification,
            severity: "warning",
          }),
        } as MessageEvent);
      });

      await waitFor(
        () => {
          expect(
            screen.getByText("Alert triggered: CPU Alert")
          ).toBeInTheDocument();
        },
        { timeout: 20000 }
      );
    });

    it("auto-hides snackbar after timeout", async () => {
      jest.useFakeTimers();

      renderAlertNotifications();

      const onMessage = mockUseWebSocket.mock.calls[0][1].onMessage;

      await act(async () => {
        onMessage({
          data: JSON.stringify(mockAlertNotification),
        } as MessageEvent);
      });

      // Should show snackbar
      await waitFor(
        () => {
          expect(
            screen.getByText("Alert triggered: CPU Alert")
          ).toBeInTheDocument();
        },
        { timeout: 20000 }
      );

      // Fast-forward time
      act(() => {
        jest.advanceTimersByTime(6000);
      });

      await waitFor(
        () => {
          expect(
            screen.queryByText("Alert triggered: CPU Alert")
          ).not.toBeInTheDocument();
        },
        { timeout: 20000 }
      );

      jest.useRealTimers();
    });
  });

  describe("Browser Notification Permission", () => {
    it("requests notification permission on mount", async () => {
      Object.defineProperty(mockNotification, "permission", {
        value: "default",
        configurable: true,
      });

      renderAlertNotifications();

      expect(mockNotification.requestPermission).toHaveBeenCalled();
    });

    it("does not request permission when already granted", async () => {
      Object.defineProperty(mockNotification, "permission", {
        value: "granted",
        configurable: true,
      });

      mockNotification.requestPermission.mockClear();

      renderAlertNotifications();

      expect(mockNotification.requestPermission).not.toHaveBeenCalled();
    });

    it("does not request permission when denied", async () => {
      Object.defineProperty(mockNotification, "permission", {
        value: "denied",
        configurable: true,
      });

      mockNotification.requestPermission.mockClear();

      renderAlertNotifications();

      expect(mockNotification.requestPermission).not.toHaveBeenCalled();
    });

    it("creates browser notification with fallback message", async () => {
      renderAlertNotifications();

      const onMessage = mockUseWebSocket.mock.calls[0][1].onMessage;
      const alertWithoutMessage = {
        ...mockAlertNotification,
        message: undefined,
      };

      await act(async () => {
        onMessage({
          data: JSON.stringify(alertWithoutMessage),
        } as MessageEvent);
      });

      expect(mockNotification).toHaveBeenCalledWith(
        "DockerDeployer Alert: CPU Alert",
        expect.objectContaining({
          body: "cpu_percent is 95.5 (threshold: > 80)",
          icon: "/favicon.ico",
          tag: "alert-1",
        })
      );
    });

    it("handles alert without alert object", async () => {
      renderAlertNotifications();

      const onMessage = mockUseWebSocket.mock.calls[0][1].onMessage;
      const alertWithoutAlertObject = {
        type: "alert_triggered",
        timestamp: new Date().toISOString(),
        severity: "warning",
        message: "Generic alert message",
      };

      await act(async () => {
        onMessage({
          data: JSON.stringify(alertWithoutAlertObject),
        } as MessageEvent);
      });

      await waitFor(
        () => {
          expect(
            screen.getByText("Alert triggered: Unknown alert")
          ).toBeInTheDocument();
        },
        { timeout: 20000 }
      );

      // Should not create browser notification without alert object
      expect(mockNotification).not.toHaveBeenCalled();
    });
  });

  describe("Edge Cases", () => {
    it("handles empty notification history", async () => {
      renderAlertNotifications();

      const onMessage = mockUseWebSocket.mock.calls[0][1].onMessage;

      await act(async () => {
        onMessage({
          data: JSON.stringify({
            type: "notification_history",
            notifications: [],
          }),
        } as MessageEvent);
      });

      // Open menu
      const notificationButton = screen.getByRole("button", {
        name: /notifications/i,
      });

      await act(async () => {
        fireEvent.click(notificationButton);
      });

      await waitFor(
        () => {
          expect(screen.getByText("No notifications")).toBeInTheDocument();
        },
        { timeout: 20000 }
      );
    });

    it("handles notification history without notifications field", async () => {
      renderAlertNotifications();

      const onMessage = mockUseWebSocket.mock.calls[0][1].onMessage;

      await act(async () => {
        onMessage({
          data: JSON.stringify({
            type: "notification_history",
          }),
        } as MessageEvent);
      });

      // Should not crash and should show empty state
      const notificationButton = screen.getByRole("button", {
        name: /notifications/i,
      });

      await act(async () => {
        fireEvent.click(notificationButton);
      });

      await waitFor(
        () => {
          expect(screen.getByText("No notifications")).toBeInTheDocument();
        },
        { timeout: 20000 }
      );
    });

    it("handles notification without timestamp", async () => {
      renderAlertNotifications();

      const onMessage = mockUseWebSocket.mock.calls[0][1].onMessage;
      const notificationWithoutTimestamp = {
        ...mockAlertNotification,
        timestamp: undefined,
      };

      await act(async () => {
        onMessage({
          data: JSON.stringify(notificationWithoutTimestamp),
        } as MessageEvent);
      });

      // Should not crash
      const notificationButton = screen.getByRole("button", {
        name: /notifications/i,
      });

      await act(async () => {
        fireEvent.click(notificationButton);
      });

      await waitFor(
        () => {
          expect(screen.getByText("CPU Alert")).toBeInTheDocument();
        },
        { timeout: 20000 }
      );
    });

    it("handles system notification without message", async () => {
      renderAlertNotifications();

      const onMessage = mockUseWebSocket.mock.calls[0][1].onMessage;

      await act(async () => {
        onMessage({
          data: JSON.stringify({
            type: "system_notification",
            timestamp: new Date().toISOString(),
            notification_type: "info",
          }),
        } as MessageEvent);
      });

      await waitFor(
        () => {
          expect(screen.getByText("System notification")).toBeInTheDocument();
        },
        { timeout: 20000 }
      );
    });

    it("handles notification without notification_type", async () => {
      renderAlertNotifications();

      const onMessage = mockUseWebSocket.mock.calls[0][1].onMessage;

      await act(async () => {
        onMessage({
          data: JSON.stringify({
            type: "user_notification",
            message: "Test message",
            timestamp: new Date().toISOString(),
          }),
        } as MessageEvent);
      });

      await waitFor(
        () => {
          expect(screen.getByText("Test message")).toBeInTheDocument();
        },
        { timeout: 20000 }
      );
    });

    it("handles acknowledged notification display", async () => {
      renderAlertNotifications();

      const onMessage = mockUseWebSocket.mock.calls[0][1].onMessage;
      const acknowledgedNotification = {
        ...mockAlertNotification,
        acknowledged: true,
      };

      await act(async () => {
        onMessage({
          data: JSON.stringify({
            type: "notification_history",
            notifications: [acknowledgedNotification],
          }),
        } as MessageEvent);
      });

      // Open menu
      const notificationButton = screen.getByRole("button", {
        name: /notifications/i,
      });

      await act(async () => {
        fireEvent.click(notificationButton);
      });

      await waitFor(
        () => {
          expect(screen.getByText("CPU Alert")).toBeInTheDocument();
          // Should not show acknowledge button for acknowledged alerts
          expect(
            screen.queryByRole("button", { name: /acknowledge/i })
          ).not.toBeInTheDocument();
        },
        { timeout: 20000 }
      );
    });

    it("handles keyboard navigation", async () => {
      renderAlertNotifications();

      const notificationButton = screen.getByRole("button", {
        name: /notifications/i,
      });

      // Focus the button
      notificationButton.focus();

      // Press Enter to open menu
      await act(async () => {
        fireEvent.keyDown(notificationButton, { key: "Enter" });
      });

      await waitFor(
        () => {
          expect(screen.getByText("Notifications")).toBeInTheDocument();
        },
        { timeout: 20000 }
      );

      // Press Escape to close menu
      await act(async () => {
        fireEvent.keyDown(document, { key: "Escape" });
      });

      await waitFor(
        () => {
          expect(screen.queryByText("Notifications")).not.toBeInTheDocument();
        },
        { timeout: 20000 }
      );
    }, 30000);
  });
});
