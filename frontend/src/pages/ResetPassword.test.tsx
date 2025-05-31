import React from "react";
import { render, screen, waitFor, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import axios from "axios";
import ResetPassword from "./ResetPassword";
import { ToastProvider } from "../components/Toast";

// Mock axios
jest.mock("axios");
const mockedAxios = axios as jest.Mocked<typeof axios>;

// Mock useNavigate
const mockNavigate = jest.fn();
jest.mock("react-router-dom", () => ({
  ...jest.requireActual("react-router-dom"),
  useNavigate: () => mockNavigate,
}));

// Create a theme for testing
const theme = createTheme();

// Test wrapper component
const TestWrapper: React.FC<{
  children: React.ReactNode;
  initialEntries?: string[];
}> = ({ children, initialEntries = ["/reset-password?token=valid-token"] }) => (
  <MemoryRouter initialEntries={initialEntries}>
    <ThemeProvider theme={theme}>
      <ToastProvider>{children}</ToastProvider>
    </ThemeProvider>
  </MemoryRouter>
);

describe("ResetPassword Component", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.clearAllTimers();
    jest.useRealTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  describe("Rendering with Valid Token", () => {
    test("renders reset password form correctly", () => {
      render(
        <TestWrapper>
          <ResetPassword />
        </TestWrapper>
      );

      expect(screen.getByText("DockerDeployer")).toBeInTheDocument();
      expect(
        screen.getByRole("heading", { name: "Reset Password" })
      ).toBeInTheDocument();
      expect(
        screen.getByText("Enter your new password below.")
      ).toBeInTheDocument();
      expect(
        document.querySelector('input[name="password"]')
      ).toBeInTheDocument();
      expect(
        document.querySelector('input[name="confirmPassword"]')
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /reset password/i })
      ).toBeInTheDocument();
    });

    test("submit button is disabled when fields are empty", () => {
      render(
        <TestWrapper>
          <ResetPassword />
        </TestWrapper>
      );

      const submitButton = screen.getByRole("button", {
        name: /reset password/i,
      });
      expect(submitButton).toBeDisabled();
    });

    test("displays password helper text", () => {
      render(
        <TestWrapper>
          <ResetPassword />
        </TestWrapper>
      );

      expect(
        screen.getByText(
          "Password must be at least 8 characters long and contain uppercase, lowercase, and numbers"
        )
      ).toBeInTheDocument();
    });
  });

  describe("Rendering without Token", () => {
    test("renders invalid reset link page when no token", () => {
      render(
        <TestWrapper initialEntries={["/reset-password"]}>
          <ResetPassword />
        </TestWrapper>
      );

      expect(screen.getByText("Invalid Reset Link")).toBeInTheDocument();
      expect(
        screen.getByText("This password reset link is invalid or has expired.")
      ).toBeInTheDocument();
      expect(
        screen.getByRole("link", { name: /request a new reset link/i })
      ).toBeInTheDocument();
    });

    test("invalid token link has correct href", () => {
      render(
        <TestWrapper initialEntries={["/reset-password"]}>
          <ResetPassword />
        </TestWrapper>
      );

      const resetLink = screen.getByRole("link", {
        name: /request a new reset link/i,
      });
      expect(resetLink).toHaveAttribute("href", "/forgot-password");
    });
  });

  describe("Form Validation", () => {
    test("shows error when passwords do not match", async () => {
      const user = userEvent.setup();
      render(
        <TestWrapper>
          <ResetPassword />
        </TestWrapper>
      );

      const passwordInput = document.querySelector(
        'input[name="password"]'
      ) as HTMLInputElement;
      const confirmPasswordInput = document.querySelector(
        'input[name="confirmPassword"]'
      ) as HTMLInputElement;
      const submitButton = screen.getByRole("button", {
        name: /reset password/i,
      });

      await act(async () => {
        await user.type(passwordInput, "Password123");
        await user.type(confirmPasswordInput, "DifferentPassword");
        await user.click(submitButton);
      });

      await waitFor(() => {
        expect(screen.getByText("Passwords do not match")).toBeInTheDocument();
      });
    });

    test("shows error for weak password (too short)", async () => {
      const user = userEvent.setup();
      render(
        <TestWrapper>
          <ResetPassword />
        </TestWrapper>
      );

      const passwordInput = document.querySelector(
        'input[name="password"]'
      ) as HTMLInputElement;
      const confirmPasswordInput = document.querySelector(
        'input[name="confirmPassword"]'
      ) as HTMLInputElement;
      const submitButton = screen.getByRole("button", {
        name: /reset password/i,
      });

      await act(async () => {
        await user.type(passwordInput, "Pass1");
        await user.type(confirmPasswordInput, "Pass1");
        await user.click(submitButton);
      });

      await waitFor(() => {
        expect(
          screen.getByText("Password must be at least 8 characters long")
        ).toBeInTheDocument();
      });
    });

    test("shows error for password without uppercase letter", async () => {
      const user = userEvent.setup();
      render(
        <TestWrapper>
          <ResetPassword />
        </TestWrapper>
      );

      const passwordInput = document.querySelector(
        'input[name="password"]'
      ) as HTMLInputElement;
      const confirmPasswordInput = document.querySelector(
        'input[name="confirmPassword"]'
      ) as HTMLInputElement;
      const submitButton = screen.getByRole("button", {
        name: /reset password/i,
      });

      await act(async () => {
        await user.type(passwordInput, "password123");
        await user.type(confirmPasswordInput, "password123");
        await user.click(submitButton);
      });

      await waitFor(() => {
        expect(
          screen.getByText(
            "Password must contain at least one uppercase letter"
          )
        ).toBeInTheDocument();
      });
    });

    test("shows error for password without lowercase letter", async () => {
      const user = userEvent.setup();
      render(
        <TestWrapper>
          <ResetPassword />
        </TestWrapper>
      );

      const passwordInput = document.querySelector(
        'input[name="password"]'
      ) as HTMLInputElement;
      const confirmPasswordInput = document.querySelector(
        'input[name="confirmPassword"]'
      ) as HTMLInputElement;
      const submitButton = screen.getByRole("button", {
        name: /reset password/i,
      });

      await act(async () => {
        await user.type(passwordInput, "PASSWORD123");
        await user.type(confirmPasswordInput, "PASSWORD123");
        await user.click(submitButton);
      });

      await waitFor(() => {
        expect(
          screen.getByText(
            "Password must contain at least one lowercase letter"
          )
        ).toBeInTheDocument();
      });
    });

    test("shows error for password without number", async () => {
      const user = userEvent.setup();
      render(
        <TestWrapper>
          <ResetPassword />
        </TestWrapper>
      );

      const passwordInput = document.querySelector(
        'input[name="password"]'
      ) as HTMLInputElement;
      const confirmPasswordInput = document.querySelector(
        'input[name="confirmPassword"]'
      ) as HTMLInputElement;
      const submitButton = screen.getByRole("button", {
        name: /reset password/i,
      });

      await act(async () => {
        await user.type(passwordInput, "Password");
        await user.type(confirmPasswordInput, "Password");
        await user.click(submitButton);
      });

      await waitFor(() => {
        expect(
          screen.getByText("Password must contain at least one number")
        ).toBeInTheDocument();
      });
    });
  });

  describe("Form Submission", () => {
    test("shows loading state during submission", async () => {
      const user = userEvent.setup();
      // Mock a delayed response
      mockedAxios.post.mockImplementation(
        () =>
          new Promise((resolve) => setTimeout(() => resolve({ data: {} }), 100))
      );

      render(
        <TestWrapper>
          <ResetPassword />
        </TestWrapper>
      );

      const passwordInput = document.querySelector(
        'input[name="password"]'
      ) as HTMLInputElement;
      const confirmPasswordInput = document.querySelector(
        'input[name="confirmPassword"]'
      ) as HTMLInputElement;
      const submitButton = screen.getByRole("button", {
        name: /reset password/i,
      });

      await act(async () => {
        await user.type(passwordInput, "Password123");
        await user.type(confirmPasswordInput, "Password123");
        await user.click(submitButton);
      });

      // Should show loading spinner
      expect(screen.getByRole("progressbar")).toBeInTheDocument();
      expect(passwordInput).toBeDisabled();
      expect(confirmPasswordInput).toBeDisabled();

      // Wait for completion
      await waitFor(() => {
        expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
      });
    });

    test("shows success message and redirects on successful reset", async () => {
      const user = userEvent.setup();
      mockedAxios.post.mockResolvedValue({ data: {} });

      render(
        <TestWrapper>
          <ResetPassword />
        </TestWrapper>
      );

      const passwordInput = document.querySelector(
        'input[name="password"]'
      ) as HTMLInputElement;
      const confirmPasswordInput = document.querySelector(
        'input[name="confirmPassword"]'
      ) as HTMLInputElement;
      const submitButton = screen.getByRole("button", {
        name: /reset password/i,
      });

      await act(async () => {
        await user.type(passwordInput, "Password123");
        await user.type(confirmPasswordInput, "Password123");
        await user.click(submitButton);
      });

      await waitFor(() => {
        expect(
          screen.getByText("Password has been reset successfully!")
        ).toBeInTheDocument();
      });

      expect(mockedAxios.post).toHaveBeenCalledWith(
        "/auth/password-reset-confirm",
        {
          token: "valid-token",
          new_password: "Password123",
        }
      );

      // Wait for navigation to be called (after 2 second timeout)
      await waitFor(
        () => {
          expect(mockNavigate).toHaveBeenCalledWith("/login");
        },
        { timeout: 3000 }
      );
    });
  });

  describe("Error Handling", () => {
    test("displays general error message", async () => {
      const user = userEvent.setup();
      const mockError = {
        isAxiosError: true,
        response: { status: 500, data: { detail: "Server error" } },
      };
      mockedAxios.post.mockRejectedValue(mockError);

      render(
        <TestWrapper>
          <ResetPassword />
        </TestWrapper>
      );

      const passwordInput = document.querySelector(
        'input[name="password"]'
      ) as HTMLInputElement;
      const confirmPasswordInput = document.querySelector(
        'input[name="confirmPassword"]'
      ) as HTMLInputElement;
      const submitButton = screen.getByRole("button", {
        name: /reset password/i,
      });

      await act(async () => {
        await user.type(passwordInput, "Password123");
        await user.type(confirmPasswordInput, "Password123");
        await user.click(submitButton);
      });

      await waitFor(() => {
        expect(screen.getByText("Server error")).toBeInTheDocument();
      });
    });

    test("can dismiss error messages", async () => {
      const user = userEvent.setup();
      const mockError = {
        isAxiosError: true,
        response: { status: 500, data: { detail: "Server error" } },
      };
      mockedAxios.post.mockRejectedValue(mockError);

      render(
        <TestWrapper>
          <ResetPassword />
        </TestWrapper>
      );

      const passwordInput = document.querySelector(
        'input[name="password"]'
      ) as HTMLInputElement;
      const confirmPasswordInput = document.querySelector(
        'input[name="confirmPassword"]'
      ) as HTMLInputElement;
      const submitButton = screen.getByRole("button", {
        name: /reset password/i,
      });

      await act(async () => {
        await user.type(passwordInput, "Password123");
        await user.type(confirmPasswordInput, "Password123");
        await user.click(submitButton);
      });

      await waitFor(() => {
        expect(screen.getByText("Server error")).toBeInTheDocument();
      });

      // Dismiss the error
      const closeButton = screen.getByLabelText("Close");
      await act(async () => {
        await user.click(closeButton);
      });

      await waitFor(() => {
        expect(screen.queryByText("Server error")).not.toBeInTheDocument();
      });
    });
  });

  describe("Navigation", () => {
    test("back to login link has correct href", () => {
      render(
        <TestWrapper>
          <ResetPassword />
        </TestWrapper>
      );

      const loginLink = screen.getByRole("link", { name: /back to login/i });
      expect(loginLink).toHaveAttribute("href", "/login");
    });
  });

  describe("Accessibility", () => {
    test("form has proper labels and structure", () => {
      render(
        <TestWrapper>
          <ResetPassword />
        </TestWrapper>
      );

      const passwordInput = document.querySelector(
        'input[name="password"]'
      ) as HTMLInputElement;
      const confirmPasswordInput = document.querySelector(
        'input[name="confirmPassword"]'
      ) as HTMLInputElement;

      expect(passwordInput).toHaveAttribute("required");
      expect(passwordInput).toHaveAttribute("type", "password");
      expect(passwordInput).toHaveAttribute("autoComplete", "new-password");
      expect(confirmPasswordInput).toHaveAttribute("required");
      expect(confirmPasswordInput).toHaveAttribute("type", "password");
      expect(confirmPasswordInput).toHaveAttribute(
        "autoComplete",
        "new-password"
      );

      const submitButton = screen.getByRole("button", {
        name: /reset password/i,
      });
      expect(submitButton).toHaveAttribute("type", "submit");
    });
  });
});
