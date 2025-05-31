import React from "react";
import {
  render,
  screen,
  fireEvent,
  waitFor,
  act,
} from "@testing-library/react";
import { ThemeProvider } from "@mui/material/styles";
import { createTheme } from "@mui/material/styles";
import AlertsManager from "./AlertsManager";
import * as useApiCallModule from "../hooks/useApiCall";

const theme = createTheme();

const mockAlerts = [
  {
    id: 1,
    name: "High CPU Alert",
    description: "Alert when CPU usage exceeds 80%",
    container_id: "test-container",
    container_name: "test-container-name",
    metric_type: "cpu_percent",
    threshold_value: 80,
    comparison_operator: ">",
    is_active: true,
    is_triggered: false,
    last_triggered_at: null,
    trigger_count: 0,
    created_at: "2024-01-01T12:00:00Z",
    updated_at: "2024-01-01T12:00:00Z",
  },
  {
    id: 2,
    name: "Memory Alert",
    description: "Alert when memory usage exceeds 90%",
    container_id: "test-container",
    container_name: "test-container-name",
    metric_type: "memory_percent",
    threshold_value: 90,
    comparison_operator: ">",
    is_active: false,
    is_triggered: true,
    last_triggered_at: "2024-01-01T11:30:00Z",
    trigger_count: 3,
    created_at: "2024-01-01T10:00:00Z",
    updated_at: "2024-01-01T11:30:00Z",
  },
];

const mockUseApiCall = {
  execute: jest.fn(),
  loading: false,
  error: null,
};

const renderWithTheme = (component: React.ReactElement) => {
  return render(<ThemeProvider theme={theme}>{component}</ThemeProvider>);
};

// Mock the useApiCall hook
jest.mock("../hooks/useApiCall");
const mockedUseApiCall = useApiCallModule.useApiCall as jest.MockedFunction<
  typeof useApiCallModule.useApiCall
>;

describe("AlertsManager", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Set up default mock that returns empty array for alerts
    mockUseApiCall.execute.mockResolvedValue([]);
    mockedUseApiCall.mockReturnValue(mockUseApiCall);
  });

  it("renders alerts manager title", () => {
    renderWithTheme(<AlertsManager />);

    expect(screen.getByText("Metrics Alerts")).toBeInTheDocument();
  });

  it("renders create alert button", () => {
    renderWithTheme(<AlertsManager />);

    expect(
      screen.getByRole("button", { name: /create alert/i })
    ).toBeInTheDocument();
  });

  it("fetches alerts on mount", async () => {
    mockUseApiCall.execute.mockResolvedValue(mockAlerts);

    renderWithTheme(<AlertsManager />);

    await waitFor(() => {
      expect(mockUseApiCall.execute).toHaveBeenCalledWith("/api/alerts");
    });
  });

  it("displays alerts in table", async () => {
    mockUseApiCall.execute.mockResolvedValue(mockAlerts);

    renderWithTheme(<AlertsManager />);

    await waitFor(() => {
      expect(screen.getByText("High CPU Alert")).toBeInTheDocument();
      expect(screen.getByText("Memory Alert")).toBeInTheDocument();
      expect(
        screen.getByText("Alert when CPU usage exceeds 80%")
      ).toBeInTheDocument();
    });
  });

  it("shows container-specific title when containerId is provided", () => {
    renderWithTheme(<AlertsManager containerId="test-container" />);

    expect(
      screen.getByText("Metrics Alerts for Container test-container")
    ).toBeInTheDocument();
  });

  it("filters alerts by container when containerId is provided", async () => {
    const allAlerts = [
      ...mockAlerts,
      {
        ...mockAlerts[0],
        id: 3,
        container_id: "other-container",
        container_name: "other-container-name",
      },
    ];

    mockUseApiCall.execute.mockResolvedValue(allAlerts);

    renderWithTheme(<AlertsManager containerId="test-container" />);

    await waitFor(() => {
      expect(screen.getByText("High CPU Alert")).toBeInTheDocument();
      expect(screen.getByText("Memory Alert")).toBeInTheDocument();
      // Should not show the alert for other-container
      expect(
        screen.queryByText("other-container-name")
      ).not.toBeInTheDocument();
    });
  });

  it("opens create alert dialog when create button is clicked", async () => {
    renderWithTheme(<AlertsManager />);

    const createButton = screen.getByRole("button", { name: /create alert/i });

    await act(async () => {
      fireEvent.click(createButton);
    });

    await waitFor(() => {
      expect(screen.getByText("Create New Alert")).toBeInTheDocument();
    });

    // Use Material-UI testing patterns to find form fields
    await waitFor(() => {
      // Find the first text input (Alert Name field)
      const textInputs = screen.getAllByRole("textbox");
      expect(textInputs.length).toBeGreaterThan(0);
      expect(textInputs[0]).toBeInTheDocument();

      // Verify the threshold input field exists
      const thresholdInput = screen.getByDisplayValue("80");
      expect(thresholdInput).toBeInTheDocument();
    });
  });

  it("opens edit alert dialog when edit button is clicked", async () => {
    mockUseApiCall.execute.mockResolvedValue(mockAlerts);

    renderWithTheme(<AlertsManager />);

    await waitFor(() => {
      expect(screen.getByText("High CPU Alert")).toBeInTheDocument();
    });

    const editButtons = screen.getAllByRole("button", { name: /edit/i });

    await act(async () => {
      fireEvent.click(editButtons[0]);
    });

    expect(screen.getByText("Edit Alert")).toBeInTheDocument();
    expect(screen.getByDisplayValue("High CPU Alert")).toBeInTheDocument();
  });

  it("handles alert creation", async () => {
    const createResponse = { id: 3, name: "New Alert" };
    mockUseApiCall.execute
      .mockResolvedValueOnce([]) // Initial fetch
      .mockResolvedValueOnce(createResponse) // Create alert
      .mockResolvedValueOnce([...mockAlerts, createResponse]); // Refresh after create

    renderWithTheme(<AlertsManager />);

    // Open create dialog
    const createButton = screen.getByRole("button", { name: /create alert/i });
    await act(async () => {
      fireEvent.click(createButton);
    });

    // Wait for dialog to open and form fields to be available
    await waitFor(() => {
      expect(screen.getByText("Create New Alert")).toBeInTheDocument();
    });

    // Use Material-UI testing patterns to find form fields
    await waitFor(() => {
      const textInputs = screen.getAllByRole("textbox");
      expect(textInputs.length).toBeGreaterThanOrEqual(3); // Name, Description, Container ID
    });

    const textInputs = screen.getAllByRole("textbox");
    const nameInput = textInputs[0]; // First textbox is Alert Name
    const descriptionInput = textInputs[1]; // Second textbox is Description (multiline)
    const containerInput = textInputs[2]; // Third textbox is Container ID
    const thresholdInput = screen.getByDisplayValue("80"); // Threshold field with default value

    await act(async () => {
      fireEvent.change(nameInput, { target: { value: "New Alert" } });
      fireEvent.change(containerInput, { target: { value: "test-container" } });
      fireEvent.change(thresholdInput, { target: { value: "75" } });
    });

    // Wait for form state to update
    await waitFor(() => {
      expect(nameInput).toHaveValue("New Alert");
      expect(containerInput).toHaveValue("test-container");
      expect(thresholdInput).toHaveValue(75);
    });

    // Submit form
    const saveButton = screen.getByRole("button", { name: /create/i });

    // Verify button is enabled before clicking
    await waitFor(() => {
      expect(saveButton).not.toBeDisabled();
    });

    await act(async () => {
      fireEvent.click(saveButton);
    });

    // Check that the create alert API was called with correct parameters
    await waitFor(() => {
      expect(mockUseApiCall.execute).toHaveBeenCalledWith("/api/alerts", {
        method: "POST",
        body: JSON.stringify({
          name: "New Alert",
          description: "",
          container_id: "test-container",
          metric_type: "cpu_percent",
          threshold_value: 75,
          comparison_operator: ">",
        }),
        headers: { "Content-Type": "application/json" },
      });
    });
  });

  it("handles alert deletion with confirmation", async () => {
    // Create a separate mock that returns alerts on first call
    const mockExecuteWithAlerts = jest.fn();
    mockExecuteWithAlerts
      .mockResolvedValueOnce(mockAlerts) // First call (loadAlerts)
      .mockResolvedValueOnce({}) // Delete call
      .mockResolvedValueOnce([]); // Reload after delete

    mockedUseApiCall.mockReturnValue({
      execute: mockExecuteWithAlerts,
      loading: false,
      error: null,
    });

    // Mock window.confirm
    const confirmSpy = jest.spyOn(window, "confirm").mockReturnValue(true);

    await act(async () => {
      renderWithTheme(<AlertsManager />);
    });

    await waitFor(() => {
      expect(screen.getByText("High CPU Alert")).toBeInTheDocument();
    });

    const deleteButtons = screen.getAllByRole("button", { name: /delete/i });

    await act(async () => {
      fireEvent.click(deleteButtons[0]);
    });

    expect(confirmSpy).toHaveBeenCalledWith(
      "Are you sure you want to delete this alert?"
    );
    expect(mockExecuteWithAlerts).toHaveBeenCalledWith("/api/alerts/1", {
      method: "DELETE",
    });

    confirmSpy.mockRestore();
  });

  it("cancels alert deletion when user declines confirmation", async () => {
    // Create a separate mock that returns alerts on first call
    const mockExecuteWithAlerts = jest.fn();
    mockExecuteWithAlerts.mockResolvedValueOnce(mockAlerts); // First call returns alerts

    mockedUseApiCall.mockReturnValue({
      execute: mockExecuteWithAlerts,
      loading: false,
      error: null,
    });

    // Mock window.confirm to return false
    const confirmSpy = jest.spyOn(window, "confirm").mockReturnValue(false);

    await act(async () => {
      renderWithTheme(<AlertsManager />);
    });

    await waitFor(() => {
      expect(screen.getByText("High CPU Alert")).toBeInTheDocument();
    });

    const deleteButtons = screen.getAllByRole("button", { name: /delete/i });

    await act(async () => {
      fireEvent.click(deleteButtons[0]);
    });

    expect(confirmSpy).toHaveBeenCalled();
    // Should not call delete API since user declined
    expect(mockExecuteWithAlerts).toHaveBeenCalledTimes(1); // Only the initial load call
    expect(mockExecuteWithAlerts).not.toHaveBeenCalledWith("/api/alerts/1", {
      method: "DELETE",
    });

    confirmSpy.mockRestore();
  });

  it("toggles alert active state", async () => {
    // Create a separate mock that returns alerts on first call
    const mockExecuteWithAlerts = jest.fn();
    mockExecuteWithAlerts.mockResolvedValueOnce(mockAlerts); // First call returns alerts

    mockedUseApiCall.mockReturnValue({
      execute: mockExecuteWithAlerts,
      loading: false,
      error: null,
    });

    await act(async () => {
      renderWithTheme(<AlertsManager />);
    });

    await waitFor(() => {
      expect(screen.getByText("High CPU Alert")).toBeInTheDocument();
    });

    // Find the toggle button for the first alert (active alert)
    const toggleButtons = screen.getAllByRole("button");
    const activeToggleButton = toggleButtons.find((button) =>
      button.querySelector('[data-testid="NotificationsIcon"]')
    );

    if (activeToggleButton) {
      await act(async () => {
        fireEvent.click(activeToggleButton);
      });

      expect(mockExecuteWithAlerts).toHaveBeenCalledWith("/api/alerts/1", {
        method: "PUT",
        body: JSON.stringify({ ...mockAlerts[0], is_active: false }),
        headers: { "Content-Type": "application/json" },
      });
    }
  });

  it("displays error message when API fails", () => {
    const errorMessage = "Failed to load alerts";
    mockedUseApiCall.mockReturnValue({
      ...mockUseApiCall,
      error: errorMessage,
    });

    renderWithTheme(<AlertsManager />);

    expect(
      screen.getByText(`Failed to load alerts: ${errorMessage}`)
    ).toBeInTheDocument();
  });

  it("shows empty state when no alerts exist", async () => {
    mockUseApiCall.execute.mockResolvedValue([]);

    renderWithTheme(<AlertsManager />);

    await waitFor(() => {
      expect(
        screen.getByText(
          "No alerts configured. Create your first alert to get notified about container metrics."
        )
      ).toBeInTheDocument();
    });
  });

  it("displays alert status correctly", async () => {
    mockUseApiCall.execute.mockResolvedValue(mockAlerts);

    renderWithTheme(<AlertsManager />);

    await waitFor(() => {
      expect(screen.getByText("Active")).toBeInTheDocument(); // First alert is active
      expect(screen.getByText("Disabled")).toBeInTheDocument(); // Second alert is disabled
    });
  });

  it("shows trigger count and last triggered time", async () => {
    mockUseApiCall.execute.mockResolvedValue(mockAlerts);

    renderWithTheme(<AlertsManager />);

    await waitFor(() => {
      expect(screen.getByText("0")).toBeInTheDocument(); // First alert trigger count
      expect(screen.getByText("3")).toBeInTheDocument(); // Second alert trigger count
      expect(screen.getByText(/Last:/)).toBeInTheDocument(); // Last triggered text
    });
  });

  it("validates required fields in create dialog", async () => {
    renderWithTheme(<AlertsManager />);

    // Open create dialog
    const createButton = screen.getByRole("button", { name: /create alert/i });
    await act(async () => {
      fireEvent.click(createButton);
    });

    // Try to submit without filling required fields
    const saveButton = screen.getByRole("button", { name: /create/i });
    expect(saveButton).toBeDisabled();
  });
});
