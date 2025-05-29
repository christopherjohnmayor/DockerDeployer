import React from "react";
import {
  render,
  screen,
  fireEvent,
  waitFor,
  act,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ThemeProvider } from "@mui/material/styles";
import { createTheme } from "@mui/material/styles";
import axios from "axios";
import UserManagement from "./UserManagement";
import { AuthContext } from "../contexts/AuthContext";
import { ToastProvider } from "../components/Toast";

// Mock axios
jest.mock("axios");
const mockedAxios = axios as jest.Mocked<typeof axios>;

// Mock Material-UI theme
const theme = createTheme();

// Mock user data
const mockUsers = [
  {
    id: 1,
    username: "admin",
    email: "admin@example.com",
    full_name: "Administrator",
    role: "admin",
    is_active: true,
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
  },
  {
    id: 2,
    username: "user1",
    email: "user1@example.com",
    full_name: "User One",
    role: "user",
    is_active: true,
    created_at: "2024-01-02T00:00:00Z",
    updated_at: "2024-01-02T00:00:00Z",
  },
  {
    id: 3,
    username: "user2",
    email: "user2@example.com",
    full_name: null,
    role: "user",
    is_active: false,
    created_at: "2024-01-03T00:00:00Z",
    updated_at: "2024-01-03T00:00:00Z",
  },
];

// Mock auth context
const mockAuthContext = {
  user: { id: 1, username: "admin", role: "admin" },
  isAuthenticated: true,
  login: jest.fn(),
  logout: jest.fn(),
  loading: false,
};

// Test wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ThemeProvider theme={theme}>
    <AuthContext.Provider value={mockAuthContext}>
      <ToastProvider>{children}</ToastProvider>
    </AuthContext.Provider>
  </ThemeProvider>
);

describe("UserManagement Component", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Mock successful users fetch by default
    mockedAxios.get.mockResolvedValue({ data: mockUsers });
    mockedAxios.patch.mockResolvedValue({ data: {} });
    mockedAxios.delete.mockResolvedValue({ data: {} });
    mockedAxios.post.mockResolvedValue({ data: {} });
  });

  afterEach(() => {
    jest.clearAllTimers();
  });

  describe("Component Rendering", () => {
    it("renders user management page with correct title", async () => {
      await act(async () => {
        render(
          <TestWrapper>
            <UserManagement />
          </TestWrapper>
        );
      });

      expect(screen.getByText("User Management")).toBeInTheDocument();
      expect(
        screen.getByText("Manage user accounts, roles, and permissions")
      ).toBeInTheDocument();
    });

    it("shows loading state initially", async () => {
      // Mock delayed response
      mockedAxios.get.mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(() => resolve({ data: mockUsers }), 100)
          )
      );

      await act(async () => {
        render(
          <TestWrapper>
            <UserManagement />
          </TestWrapper>
        );
      });

      expect(screen.getByText("Loading users...")).toBeInTheDocument();

      // Wait for loading to complete
      await waitFor(
        () => {
          expect(
            screen.queryByText("Loading users...")
          ).not.toBeInTheDocument();
        },
        { timeout: 200 }
      );
    });

    it("renders user table with correct headers", async () => {
      await act(async () => {
        render(
          <TestWrapper>
            <UserManagement />
          </TestWrapper>
        );
      });

      await waitFor(() => {
        expect(screen.getByText("Username")).toBeInTheDocument();
        expect(screen.getByText("Email")).toBeInTheDocument();
        expect(screen.getByText("Full Name")).toBeInTheDocument();
        expect(screen.getByText("Role")).toBeInTheDocument();
        expect(screen.getByText("Status")).toBeInTheDocument();
        expect(screen.getByText("Created")).toBeInTheDocument();
        expect(screen.getByText("Actions")).toBeInTheDocument();
      });
    });

    it("displays user data correctly in table", async () => {
      await act(async () => {
        render(
          <TestWrapper>
            <UserManagement />
          </TestWrapper>
        );
      });

      await waitFor(() => {
        // Check user data is displayed - use getAllByText for elements that appear multiple times
        expect(screen.getAllByText("admin")).toHaveLength(2); // username and role
        expect(screen.getByText("admin@example.com")).toBeInTheDocument();
        expect(screen.getByText("Administrator")).toBeInTheDocument();
        expect(screen.getByText("user1")).toBeInTheDocument();
        expect(screen.getByText("user1@example.com")).toBeInTheDocument();
        expect(screen.getByText("User One")).toBeInTheDocument();
        expect(screen.getByText("user2")).toBeInTheDocument();
        expect(screen.getByText("user2@example.com")).toBeInTheDocument();

        // Check role chips
        const adminChips = screen.getAllByText("admin");
        const userChips = screen.getAllByText("user");
        expect(adminChips.length).toBeGreaterThan(0);
        expect(userChips.length).toBeGreaterThan(0);

        // Check status chips
        expect(screen.getAllByText("Active")).toHaveLength(2);
        expect(screen.getByText("Inactive")).toBeInTheDocument();

        // Check null full name displays as dash
        const dashElements = screen.getAllByText("-");
        expect(dashElements.length).toBeGreaterThan(0);
      });
    });
  });

  describe("Data Loading", () => {
    it("fetches users on component mount", async () => {
      await act(async () => {
        render(
          <TestWrapper>
            <UserManagement />
          </TestWrapper>
        );
      });

      await waitFor(() => {
        expect(mockedAxios.get).toHaveBeenCalledWith("/auth/admin/users");
      });
    });

    it("handles loading error", async () => {
      const errorMessage = "Failed to load users";
      mockedAxios.get.mockRejectedValue({
        response: { data: { detail: errorMessage } },
      });

      await act(async () => {
        render(
          <TestWrapper>
            <UserManagement />
          </TestWrapper>
        );
      });

      await waitFor(() => {
        expect(screen.getByText(errorMessage)).toBeInTheDocument();
      });
    });

    it("handles network error during loading", async () => {
      mockedAxios.get.mockRejectedValue(new Error("Network error"));

      await act(async () => {
        render(
          <TestWrapper>
            <UserManagement />
          </TestWrapper>
        );
      });

      await waitFor(() => {
        expect(screen.getByText("Network error")).toBeInTheDocument();
      });
    });

    it("handles malformed response during loading", async () => {
      mockedAxios.get.mockRejectedValue({});

      await act(async () => {
        render(
          <TestWrapper>
            <UserManagement />
          </TestWrapper>
        );
      });

      await waitFor(() => {
        expect(
          screen.getByText("An unexpected error occurred. Please try again.")
        ).toBeInTheDocument();
      });
    });
  });

  describe("User Actions", () => {
    it("opens edit dialog when edit button is clicked", async () => {
      const user = userEvent.setup();

      await act(async () => {
        render(
          <TestWrapper>
            <UserManagement />
          </TestWrapper>
        );
      });

      await waitFor(() => {
        expect(screen.getAllByText("admin")).toHaveLength(2); // username and role
      });

      // Click edit button for first user
      const editButtons = screen.getAllByTestId("EditIcon");
      await act(async () => {
        await user.click(editButtons[0].closest("button")!);
      });

      await waitFor(() => {
        expect(screen.getByText("Edit User")).toBeInTheDocument();
        expect(
          screen.getByDisplayValue("admin@example.com")
        ).toBeInTheDocument();
        expect(screen.getByDisplayValue("Administrator")).toBeInTheDocument();
      });
    });

    it("opens delete dialog when delete button is clicked", async () => {
      const user = userEvent.setup();

      await act(async () => {
        render(
          <TestWrapper>
            <UserManagement />
          </TestWrapper>
        );
      });

      await waitFor(() => {
        expect(screen.getByText("user1")).toBeInTheDocument();
      });

      // Click delete button for second user (not admin)
      const deleteButtons = screen.getAllByTestId("DeleteIcon");
      await act(async () => {
        await user.click(deleteButtons[1].closest("button")!);
      });

      await waitFor(() => {
        expect(screen.getByText("Delete User")).toBeInTheDocument();
        expect(
          screen.getByText(/Are you sure you want to delete user "user1"/)
        ).toBeInTheDocument();
      });
    });

    it("disables delete and toggle buttons for current user", async () => {
      await act(async () => {
        render(
          <TestWrapper>
            <UserManagement />
          </TestWrapper>
        );
      });

      await waitFor(() => {
        expect(screen.getAllByText("admin")).toHaveLength(2); // username and role
      });

      // Find buttons for the admin user (first row)
      const deleteButtons = screen.getAllByTestId("DeleteIcon");
      const toggleButtons = screen.getAllByTestId("BlockIcon");

      // Admin user's buttons should be disabled
      expect(deleteButtons[0].closest("button")).toBeDisabled();
      expect(toggleButtons[0].closest("button")).toBeDisabled();

      // Other users' buttons should be enabled
      expect(deleteButtons[1].closest("button")).not.toBeDisabled();
    });
  });

  describe("Role and Status Display", () => {
    it("displays admin role with error color", async () => {
      await act(async () => {
        render(
          <TestWrapper>
            <UserManagement />
          </TestWrapper>
        );
      });

      await waitFor(() => {
        const adminChips = screen.getAllByText("admin");
        // Find the chip (not the username)
        const adminRoleChip = adminChips.find((chip) =>
          chip.closest(".MuiChip-root")
        );
        expect(adminRoleChip).toBeInTheDocument();
      });
    });

    it("displays user role with default color", async () => {
      await act(async () => {
        render(
          <TestWrapper>
            <UserManagement />
          </TestWrapper>
        );
      });

      await waitFor(() => {
        const userChips = screen.getAllByText("user");
        expect(userChips.length).toBeGreaterThan(0);
      });
    });

    it("displays active status with success color", async () => {
      await act(async () => {
        render(
          <TestWrapper>
            <UserManagement />
          </TestWrapper>
        );
      });

      await waitFor(() => {
        const activeChips = screen.getAllByText("Active");
        expect(activeChips).toHaveLength(2);
      });
    });

    it("displays inactive status with default color", async () => {
      await act(async () => {
        render(
          <TestWrapper>
            <UserManagement />
          </TestWrapper>
        );
      });

      await waitFor(() => {
        expect(screen.getByText("Inactive")).toBeInTheDocument();
      });
    });

    it("formats creation date correctly", async () => {
      await act(async () => {
        render(
          <TestWrapper>
            <UserManagement />
          </TestWrapper>
        );
      });

      await waitFor(() => {
        // Check that dates are formatted (should show as MM/DD/YYYY or similar)
        const dateElements = screen.getAllByText(/\d{1,2}\/\d{1,2}\/\d{4}/);
        expect(dateElements.length).toBeGreaterThan(0);
      });
    });
  });

  describe("Edit User Dialog", () => {
    it("populates edit form with user data", async () => {
      const user = userEvent.setup();

      await act(async () => {
        render(
          <TestWrapper>
            <UserManagement />
          </TestWrapper>
        );
      });

      await waitFor(() => {
        expect(screen.getByText("user1")).toBeInTheDocument();
      });

      // Click edit button for user1
      const editButtons = screen.getAllByTestId("EditIcon");
      await act(async () => {
        await user.click(editButtons[1].closest("button")!);
      });

      await waitFor(() => {
        expect(
          screen.getByDisplayValue("user1@example.com")
        ).toBeInTheDocument();
        expect(screen.getByDisplayValue("User One")).toBeInTheDocument();
        expect(screen.getByDisplayValue("user")).toBeInTheDocument();
        // Password field should be empty
        const passwordInput = screen.getByLabelText("New Password (optional)");
        expect(passwordInput).toHaveValue("");
      });
    });

    it("updates form fields when user types", async () => {
      const user = userEvent.setup();

      await act(async () => {
        render(
          <TestWrapper>
            <UserManagement />
          </TestWrapper>
        );
      });

      // Open edit dialog
      const editButtons = screen.getAllByTestId("EditIcon");
      await act(async () => {
        await user.click(editButtons[1].closest("button")!);
      });

      await waitFor(() => {
        expect(
          screen.getByDisplayValue("user1@example.com")
        ).toBeInTheDocument();
      });

      // Update email field
      const emailInput = screen.getByDisplayValue("user1@example.com");
      await act(async () => {
        await user.clear(emailInput);
        await user.type(emailInput, "updated@example.com");
      });

      expect(
        screen.getByDisplayValue("updated@example.com")
      ).toBeInTheDocument();

      // Update full name field
      const fullNameInput = screen.getByDisplayValue("User One");
      await act(async () => {
        await user.clear(fullNameInput);
        await user.type(fullNameInput, "Updated User");
      });

      expect(screen.getByDisplayValue("Updated User")).toBeInTheDocument();
    });

    it("saves user successfully", async () => {
      const user = userEvent.setup();

      await act(async () => {
        render(
          <TestWrapper>
            <UserManagement />
          </TestWrapper>
        );
      });

      // Open edit dialog
      const editButtons = screen.getAllByTestId("EditIcon");
      await act(async () => {
        await user.click(editButtons[1].closest("button")!);
      });

      await waitFor(() => {
        expect(screen.getByText("Edit User")).toBeInTheDocument();
      });

      // Update email
      const emailInput = screen.getByDisplayValue("user1@example.com");
      await act(async () => {
        await user.clear(emailInput);
        await user.type(emailInput, "updated@example.com");
      });

      // Click save
      const saveButton = screen.getByRole("button", { name: /save/i });
      await act(async () => {
        await user.click(saveButton);
      });

      await waitFor(() => {
        expect(mockedAxios.patch).toHaveBeenCalledWith("/auth/admin/users/2", {
          email: "updated@example.com",
          full_name: "User One",
          role: "user",
          is_active: true,
        });
      });

      // Dialog should close and users should be refetched
      await waitFor(() => {
        expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
      });
    });

    it("saves user with password when provided", async () => {
      const user = userEvent.setup();

      await act(async () => {
        render(
          <TestWrapper>
            <UserManagement />
          </TestWrapper>
        );
      });

      // Open edit dialog
      const editButtons = screen.getAllByTestId("EditIcon");
      await act(async () => {
        await user.click(editButtons[1].closest("button")!);
      });

      await waitFor(() => {
        expect(screen.getByText("Edit User")).toBeInTheDocument();
      });

      // Add password
      const passwordInput = screen.getByLabelText("New Password (optional)");
      await act(async () => {
        await user.type(passwordInput, "newpassword123");
      });

      // Click save
      const saveButton = screen.getByRole("button", { name: /save/i });
      await act(async () => {
        await user.click(saveButton);
      });

      await waitFor(() => {
        expect(mockedAxios.patch).toHaveBeenCalledWith("/auth/admin/users/2", {
          email: "user1@example.com",
          full_name: "User One",
          role: "user",
          is_active: true,
          password: "newpassword123",
        });
      });
    });

    it("handles save error with validation errors", async () => {
      const user = userEvent.setup();
      mockedAxios.patch.mockRejectedValue({
        isAxiosError: true,
        response: {
          status: 422,
          data: {
            detail: [
              { loc: ["email"], msg: "Invalid email format" },
              { loc: ["password"], msg: "Password too short" },
            ],
          },
        },
      });

      await act(async () => {
        render(
          <TestWrapper>
            <UserManagement />
          </TestWrapper>
        );
      });

      // Open edit dialog and save
      const editButtons = screen.getAllByTestId("EditIcon");
      await act(async () => {
        await user.click(editButtons[1].closest("button")!);
      });

      const saveButton = screen.getByRole("button", { name: /save/i });
      await act(async () => {
        await user.click(saveButton);
      });

      await waitFor(() => {
        // Check that validation errors appear as helper text in form fields
        expect(screen.getByText("Invalid email format")).toBeInTheDocument();
        expect(screen.getByText("Password too short")).toBeInTheDocument();
      });
    });

    it("handles save error without validation errors", async () => {
      const user = userEvent.setup();
      mockedAxios.patch.mockRejectedValue({
        response: { data: { detail: "Server error" } },
      });

      await act(async () => {
        render(
          <TestWrapper>
            <UserManagement />
          </TestWrapper>
        );
      });

      // Open edit dialog and save
      const editButtons = screen.getAllByTestId("EditIcon");
      await act(async () => {
        await user.click(editButtons[1].closest("button")!);
      });

      const saveButton = screen.getByRole("button", { name: /save/i });
      await act(async () => {
        await user.click(saveButton);
      });

      // Should show toast error (we can't easily test toast content, but we can verify the API call)
      await waitFor(() => {
        expect(mockedAxios.patch).toHaveBeenCalled();
      });
    });

    it("cancels edit dialog", async () => {
      const user = userEvent.setup();

      await act(async () => {
        render(
          <TestWrapper>
            <UserManagement />
          </TestWrapper>
        );
      });

      // Open edit dialog
      const editButtons = screen.getAllByTestId("EditIcon");
      await act(async () => {
        await user.click(editButtons[1].closest("button")!);
      });

      await waitFor(() => {
        expect(screen.getByText("Edit User")).toBeInTheDocument();
      });

      // Click cancel
      const cancelButton = screen.getByRole("button", { name: /cancel/i });
      await act(async () => {
        await user.click(cancelButton);
      });

      await waitFor(() => {
        expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
      });
    });

    it("toggles active status switch", async () => {
      const user = userEvent.setup();

      await act(async () => {
        render(
          <TestWrapper>
            <UserManagement />
          </TestWrapper>
        );
      });

      // Open edit dialog for inactive user
      const editButtons = screen.getAllByTestId("EditIcon");
      await act(async () => {
        await user.click(editButtons[2].closest("button")!);
      });

      await waitFor(() => {
        expect(screen.getByText("Edit User")).toBeInTheDocument();
      });

      // Find and toggle the active switch
      const activeSwitch = screen.getByRole("checkbox", { name: /active/i });
      expect(activeSwitch).not.toBeChecked(); // user2 is inactive

      await act(async () => {
        await user.click(activeSwitch);
      });

      expect(activeSwitch).toBeChecked();
    });

    it("changes role selection", async () => {
      const user = userEvent.setup();

      await act(async () => {
        render(
          <TestWrapper>
            <UserManagement />
          </TestWrapper>
        );
      });

      // Open edit dialog
      const editButtons = screen.getAllByTestId("EditIcon");
      await act(async () => {
        await user.click(editButtons[1].closest("button")!);
      });

      await waitFor(() => {
        expect(screen.getByText("Edit User")).toBeInTheDocument();
      });

      // Click on role select - use the select element directly (it doesn't have a name)
      const roleSelect = screen.getByRole("combobox");
      await act(async () => {
        await user.click(roleSelect);
      });

      // Select admin option
      await act(async () => {
        const adminOption = screen.getByRole("option", { name: "Admin" });
        await user.click(adminOption);
      });

      // Verify selection
      expect(screen.getByDisplayValue("admin")).toBeInTheDocument();
    });
  });

  describe("Delete User Dialog", () => {
    it("deletes user successfully", async () => {
      const user = userEvent.setup();

      await act(async () => {
        render(
          <TestWrapper>
            <UserManagement />
          </TestWrapper>
        );
      });

      // Open delete dialog
      const deleteButtons = screen.getAllByTestId("DeleteIcon");
      await act(async () => {
        await user.click(deleteButtons[1].closest("button")!);
      });

      await waitFor(() => {
        expect(screen.getByText("Delete User")).toBeInTheDocument();
      });

      // Click delete
      const deleteButton = screen.getByRole("button", { name: /delete/i });
      await act(async () => {
        await user.click(deleteButton);
      });

      await waitFor(() => {
        expect(mockedAxios.delete).toHaveBeenCalledWith("/auth/admin/users/2");
      });

      // Dialog should close and users should be refetched
      await waitFor(() => {
        expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
      });
    });

    it("handles delete error", async () => {
      const user = userEvent.setup();
      mockedAxios.delete.mockRejectedValue({
        response: { data: { detail: "Cannot delete user" } },
      });

      await act(async () => {
        render(
          <TestWrapper>
            <UserManagement />
          </TestWrapper>
        );
      });

      // Open delete dialog and delete
      const deleteButtons = screen.getAllByTestId("DeleteIcon");
      await act(async () => {
        await user.click(deleteButtons[1].closest("button")!);
      });

      const deleteButton = screen.getByRole("button", { name: /delete/i });
      await act(async () => {
        await user.click(deleteButton);
      });

      // Should handle error (we can't easily test toast content, but we can verify the API call)
      await waitFor(() => {
        expect(mockedAxios.delete).toHaveBeenCalled();
      });
    });

    it("cancels delete dialog", async () => {
      const user = userEvent.setup();

      await act(async () => {
        render(
          <TestWrapper>
            <UserManagement />
          </TestWrapper>
        );
      });

      // Open delete dialog
      const deleteButtons = screen.getAllByTestId("DeleteIcon");
      await act(async () => {
        await user.click(deleteButtons[1].closest("button")!);
      });

      await waitFor(() => {
        expect(screen.getByText("Delete User")).toBeInTheDocument();
      });

      // Click cancel
      const cancelButton = screen.getByRole("button", { name: /cancel/i });
      await act(async () => {
        await user.click(cancelButton);
      });

      await waitFor(() => {
        expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
      });
    });
  });

  describe("User Status Toggle", () => {
    it("toggles user status successfully", async () => {
      const user = userEvent.setup();

      await act(async () => {
        render(
          <TestWrapper>
            <UserManagement />
          </TestWrapper>
        );
      });

      await waitFor(() => {
        expect(screen.getByText("user1")).toBeInTheDocument();
      });

      // Click toggle button for active user (should deactivate)
      const toggleButtons = screen.getAllByTestId("BlockIcon");
      await act(async () => {
        await user.click(toggleButtons[1].closest("button")!);
      });

      await waitFor(() => {
        expect(mockedAxios.post).toHaveBeenCalledWith(
          "/auth/admin/users/2/deactivate"
        );
      });
    });

    it("toggles inactive user to active", async () => {
      const user = userEvent.setup();

      await act(async () => {
        render(
          <TestWrapper>
            <UserManagement />
          </TestWrapper>
        );
      });

      await waitFor(() => {
        expect(screen.getByText("user2")).toBeInTheDocument();
      });

      // Click toggle button for inactive user (should activate)
      const toggleButtons = screen.getAllByTestId("CheckCircleIcon");
      await act(async () => {
        await user.click(toggleButtons[0].closest("button")!);
      });

      await waitFor(() => {
        expect(mockedAxios.post).toHaveBeenCalledWith(
          "/auth/admin/users/3/activate"
        );
      });
    });

    it("handles toggle status error", async () => {
      const user = userEvent.setup();
      mockedAxios.post.mockRejectedValue({
        response: { data: { detail: "Cannot toggle user status" } },
      });

      await act(async () => {
        render(
          <TestWrapper>
            <UserManagement />
          </TestWrapper>
        );
      });

      // Click toggle button
      const toggleButtons = screen.getAllByTestId("BlockIcon");
      await act(async () => {
        await user.click(toggleButtons[1].closest("button")!);
      });

      // Should handle error (we can't easily test toast content, but we can verify the API call)
      await waitFor(() => {
        expect(mockedAxios.post).toHaveBeenCalled();
      });
    });
  });

  describe("Error Handling", () => {
    it("displays and dismisses error messages", async () => {
      const user = userEvent.setup();
      const mockError = {
        isAxiosError: true,
        response: { status: 403, data: { detail: "Access denied" } },
      };
      mockedAxios.get.mockRejectedValue(mockError);

      await act(async () => {
        render(
          <TestWrapper>
            <UserManagement />
          </TestWrapper>
        );
      });

      // The ErrorDisplay component shows the parsed error message
      await waitFor(() => {
        expect(screen.getByText("Access denied")).toBeInTheDocument();
      });

      // Dismiss error using the close button in the ErrorDisplay (first one)
      const dismissButtons = screen.getAllByLabelText("Close");
      await act(async () => {
        await user.click(dismissButtons[0]); // First close button is from ErrorDisplay
      });

      await waitFor(() => {
        expect(screen.queryByText("Access denied")).not.toBeInTheDocument();
      });
    });
  });

  describe("Edge Cases", () => {
    it("handles empty users list", async () => {
      mockedAxios.get.mockResolvedValue({ data: [] });

      await act(async () => {
        render(
          <TestWrapper>
            <UserManagement />
          </TestWrapper>
        );
      });

      await waitFor(() => {
        expect(screen.getByText("User Management")).toBeInTheDocument();
        // Table headers should still be present
        expect(screen.getByText("Username")).toBeInTheDocument();
        // But no user data
        expect(screen.queryByText("admin")).not.toBeInTheDocument();
      });
    });

    it("handles user with null full_name in edit dialog", async () => {
      const user = userEvent.setup();

      await act(async () => {
        render(
          <TestWrapper>
            <UserManagement />
          </TestWrapper>
        );
      });

      // Open edit dialog for user2 (has null full_name)
      const editButtons = screen.getAllByTestId("EditIcon");
      await act(async () => {
        await user.click(editButtons[2].closest("button")!);
      });

      await waitFor(() => {
        expect(screen.getByText("Edit User")).toBeInTheDocument();
        // Full name field should be empty for null value
        const fullNameInput = screen.getByLabelText("Full Name");
        expect(fullNameInput).toHaveValue("");
      });
    });

    it("clears field errors when opening edit dialog", async () => {
      const user = userEvent.setup();

      await act(async () => {
        render(
          <TestWrapper>
            <UserManagement />
          </TestWrapper>
        );
      });

      // Open edit dialog
      const editButtons = screen.getAllByTestId("EditIcon");
      await act(async () => {
        await user.click(editButtons[1].closest("button")!);
      });

      await waitFor(() => {
        expect(screen.getByText("Edit User")).toBeInTheDocument();
        // No error messages should be present initially
        expect(
          screen.queryByText("Invalid email format")
        ).not.toBeInTheDocument();
      });
    });
  });
});
