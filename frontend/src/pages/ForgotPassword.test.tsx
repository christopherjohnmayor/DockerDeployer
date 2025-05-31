import React from "react";
import { render, screen, waitFor, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import axios from "axios";
import ForgotPassword from "./ForgotPassword";
import { ToastProvider } from "../components/Toast";

// Mock axios
jest.mock("axios");
const mockedAxios = axios as jest.Mocked<typeof axios>;

// Create a theme for testing
const theme = createTheme();

// Test wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <BrowserRouter>
    <ThemeProvider theme={theme}>
      <ToastProvider>{children}</ToastProvider>
    </ThemeProvider>
  </BrowserRouter>
);

describe("ForgotPassword Component", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("Rendering", () => {
    test("renders forgot password form correctly", () => {
      render(
        <TestWrapper>
          <ForgotPassword />
        </TestWrapper>
      );

      expect(screen.getByText("DockerDeployer")).toBeInTheDocument();
      expect(screen.getByText("Reset Password")).toBeInTheDocument();
      expect(
        screen.getByText(/Enter your email address and we'll send you a link/)
      ).toBeInTheDocument();
      expect(
        screen.getByRole("textbox", { name: /email address/i })
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /send reset link/i })
      ).toBeInTheDocument();
      expect(screen.getByText("Remember your password?")).toBeInTheDocument();
      expect(
        screen.getByRole("link", { name: /back to login/i })
      ).toBeInTheDocument();
    });

    test("submit button is disabled when email is empty", () => {
      render(
        <TestWrapper>
          <ForgotPassword />
        </TestWrapper>
      );

      const submitButton = screen.getByRole("button", {
        name: /send reset link/i,
      });
      expect(submitButton).toBeDisabled();
    });

    test("submit button is enabled when email is provided", async () => {
      const user = userEvent.setup();
      render(
        <TestWrapper>
          <ForgotPassword />
        </TestWrapper>
      );

      const emailInput = screen.getByRole("textbox", {
        name: /email address/i,
      });
      const submitButton = screen.getByRole("button", {
        name: /send reset link/i,
      });

      await act(async () => {
        await user.type(emailInput, "test@example.com");
      });

      expect(submitButton).not.toBeDisabled();
    });
  });

  describe("Form Validation", () => {
    test("shows error for invalid email format", async () => {
      const user = userEvent.setup();
      render(
        <TestWrapper>
          <ForgotPassword />
        </TestWrapper>
      );

      const emailInput = screen.getByRole("textbox", {
        name: /email address/i,
      });
      const submitButton = screen.getByRole("button", {
        name: /send reset link/i,
      });

      await act(async () => {
        await user.type(emailInput, "invalid-email");
        await user.click(submitButton);
      });

      await waitFor(() => {
        expect(
          screen.getByText("Please enter a valid email address")
        ).toBeInTheDocument();
      });
    });

    test("accepts valid email format", async () => {
      const user = userEvent.setup();
      mockedAxios.post.mockResolvedValue({ data: {} });

      render(
        <TestWrapper>
          <ForgotPassword />
        </TestWrapper>
      );

      const emailInput = screen.getByRole("textbox", {
        name: /email address/i,
      });
      const submitButton = screen.getByRole("button", {
        name: /send reset link/i,
      });

      await act(async () => {
        await user.type(emailInput, "test@example.com");
        await user.click(submitButton);
      });

      await waitFor(() => {
        expect(mockedAxios.post).toHaveBeenCalledWith(
          "/auth/password-reset-request",
          {
            email: "test@example.com",
          }
        );
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
          <ForgotPassword />
        </TestWrapper>
      );

      const emailInput = screen.getByRole("textbox", {
        name: /email address/i,
      });
      const submitButton = screen.getByRole("button", {
        name: /send reset link/i,
      });

      await act(async () => {
        await user.type(emailInput, "test@example.com");
        await user.click(submitButton);
      });

      // Should show loading spinner
      expect(screen.getByRole("progressbar")).toBeInTheDocument();
      expect(emailInput).toBeDisabled();

      // Wait for completion
      await waitFor(() => {
        expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
      });
    });

    test("shows success message on successful submission", async () => {
      const user = userEvent.setup();
      mockedAxios.post.mockResolvedValue({ data: {} });

      render(
        <TestWrapper>
          <ForgotPassword />
        </TestWrapper>
      );

      const emailInput = screen.getByRole("textbox", {
        name: /email address/i,
      });
      const submitButton = screen.getByRole("button", {
        name: /send reset link/i,
      });

      await act(async () => {
        await user.type(emailInput, "test@example.com");
        await user.click(submitButton);
      });

      await waitFor(() => {
        expect(
          screen.getByText(
            /If an account with that email exists, a password reset link has been sent/
          )
        ).toBeInTheDocument();
      });

      expect(mockedAxios.post).toHaveBeenCalledWith(
        "/auth/password-reset-request",
        {
          email: "test@example.com",
        }
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
          <ForgotPassword />
        </TestWrapper>
      );

      const emailInput = screen.getByRole("textbox", {
        name: /email address/i,
      });
      const submitButton = screen.getByRole("button", {
        name: /send reset link/i,
      });

      await act(async () => {
        await user.type(emailInput, "test@example.com");
        await user.click(submitButton);
      });

      await waitFor(() => {
        expect(screen.getByText("Server error")).toBeInTheDocument();
      });
    });

    test("handles validation errors from server", async () => {
      const user = userEvent.setup();
      const mockError = {
        isAxiosError: true,
        response: {
          status: 422,
          data: {
            detail: [
              {
                loc: ["body", "email"],
                msg: "Invalid email format",
                type: "value_error",
              },
            ],
          },
        },
      };
      mockedAxios.post.mockRejectedValue(mockError);

      render(
        <TestWrapper>
          <ForgotPassword />
        </TestWrapper>
      );

      const emailInput = screen.getByRole("textbox", {
        name: /email address/i,
      });
      const submitButton = screen.getByRole("button", {
        name: /send reset link/i,
      });

      await act(async () => {
        await user.type(emailInput, "test@example.com");
        await user.click(submitButton);
      });

      // Verify the API call was made and component handles the error gracefully
      await waitFor(() => {
        expect(mockedAxios.post).toHaveBeenCalledWith(
          "/auth/password-reset-request",
          {
            email: "test@example.com",
          }
        );
      });

      // Component should not crash and form should still be present
      expect(
        screen.getByRole("button", { name: /send reset link/i })
      ).toBeInTheDocument();
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
          <ForgotPassword />
        </TestWrapper>
      );

      const emailInput = screen.getByRole("textbox", {
        name: /email address/i,
      });
      const submitButton = screen.getByRole("button", {
        name: /send reset link/i,
      });

      await act(async () => {
        await user.type(emailInput, "test@example.com");
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
          <ForgotPassword />
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
          <ForgotPassword />
        </TestWrapper>
      );

      const emailInput = screen.getByRole("textbox", {
        name: /email address/i,
      });
      expect(emailInput).toHaveAttribute("type", "text"); // Material-UI uses text type for email inputs
      expect(emailInput).toHaveAttribute("required");
      expect(emailInput).toHaveAttribute("autoComplete", "email");

      // Check that the form element exists (even without role="form")
      const formElement = document.querySelector("form");
      expect(formElement).toBeInTheDocument();

      const submitButton = screen.getByRole("button", {
        name: /send reset link/i,
      });
      expect(submitButton).toHaveAttribute("type", "submit");
    });

    test("input field has proper accessibility attributes", async () => {
      render(
        <TestWrapper>
          <ForgotPassword />
        </TestWrapper>
      );

      const emailInput = screen.getByRole("textbox", {
        name: /email address/i,
      });

      // Check basic accessibility attributes
      expect(emailInput).toHaveAttribute("required");
      expect(emailInput).toHaveAttribute("autoComplete", "email");
      expect(emailInput).toHaveAttribute("id", "email");

      // Check that the input is properly labeled
      const label = document.querySelector('label[for="email"]');
      expect(label).toBeInTheDocument();
      expect(label).toHaveTextContent("Email Address");
    });
  });
});
