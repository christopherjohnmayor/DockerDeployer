import React from "react";
import { render, screen, waitFor, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import axios from "axios";
import Register from "./Register";
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
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <BrowserRouter>
    <ThemeProvider theme={theme}>
      <ToastProvider>{children}</ToastProvider>
    </ThemeProvider>
  </BrowserRouter>
);

describe("Register Component", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.clearAllTimers();
    jest.useRealTimers();
    // Clear any existing DOM
    document.body.innerHTML = "";
  });

  afterEach(() => {
    jest.useRealTimers();
    // Clean up DOM
    document.body.innerHTML = "";
  });

  describe("Rendering", () => {
    test("renders registration form correctly", () => {
      render(
        <TestWrapper>
          <Register />
        </TestWrapper>
      );

      expect(screen.getByText("DockerDeployer")).toBeInTheDocument();
      expect(
        screen.getByRole("heading", { name: "Register" })
      ).toBeInTheDocument();
      expect(
        screen.getByRole("textbox", { name: /username/i })
      ).toBeInTheDocument();
      expect(
        screen.getByRole("textbox", { name: /email address/i })
      ).toBeInTheDocument();
      expect(
        screen.getByRole("textbox", { name: /full name/i })
      ).toBeInTheDocument();
      expect(
        document.querySelector('input[name="password"]')
      ).toBeInTheDocument();
      expect(
        document.querySelector('input[name="confirmPassword"]')
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /register/i })
      ).toBeInTheDocument();
      expect(screen.getByText("Already have an account?")).toBeInTheDocument();
      expect(
        screen.getByRole("link", { name: /sign in/i })
      ).toBeInTheDocument();
    });

    test("submit button is disabled when required fields are empty", () => {
      render(
        <TestWrapper>
          <Register />
        </TestWrapper>
      );

      const submitButton = screen.getByRole("button", { name: /register/i });
      expect(submitButton).toBeDisabled();
    });

    test("submit button is enabled when all required fields are filled", async () => {
      const user = userEvent.setup();
      render(
        <TestWrapper>
          <Register />
        </TestWrapper>
      );

      const usernameInput = screen.getByRole("textbox", { name: /username/i });
      const emailInput = screen.getByRole("textbox", {
        name: /email address/i,
      });
      const passwordInput = document.querySelector(
        'input[name="password"]'
      ) as HTMLInputElement;
      const confirmPasswordInput = document.querySelector(
        'input[name="confirmPassword"]'
      ) as HTMLInputElement;
      const submitButton = screen.getByRole("button", { name: /register/i });

      await act(async () => {
        await user.type(usernameInput, "testuser");
        await user.type(emailInput, "test@example.com");
        await user.type(passwordInput, "Password123");
        await user.type(confirmPasswordInput, "Password123");
      });

      expect(submitButton).not.toBeDisabled();
    });
  });

  describe("Form Validation", () => {
    test("shows error when passwords do not match", async () => {
      const user = userEvent.setup();
      render(
        <TestWrapper>
          <Register />
        </TestWrapper>
      );

      const usernameInput = screen.getByRole("textbox", { name: /username/i });
      const emailInput = screen.getByRole("textbox", {
        name: /email address/i,
      });
      const passwordInput = document.querySelector(
        'input[name="password"]'
      ) as HTMLInputElement;
      const confirmPasswordInput = document.querySelector(
        'input[name="confirmPassword"]'
      ) as HTMLInputElement;
      const submitButton = screen.getByRole("button", { name: /register/i });

      await act(async () => {
        await user.type(usernameInput, "testuser");
        await user.type(emailInput, "test@example.com");
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
          <Register />
        </TestWrapper>
      );

      const usernameInput = screen.getByRole("textbox", { name: /username/i });
      const emailInput = screen.getByRole("textbox", {
        name: /email address/i,
      });
      const passwordInput = document.querySelector(
        'input[name="password"]'
      ) as HTMLInputElement;
      const confirmPasswordInput = document.querySelector(
        'input[name="confirmPassword"]'
      ) as HTMLInputElement;
      const submitButton = screen.getByRole("button", { name: /register/i });

      await act(async () => {
        await user.type(usernameInput, "testuser");
        await user.type(emailInput, "test@example.com");
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
          <Register />
        </TestWrapper>
      );

      const usernameInput = screen.getByRole("textbox", { name: /username/i });
      const emailInput = screen.getByRole("textbox", {
        name: /email address/i,
      });
      const passwordInput = document.querySelector(
        'input[name="password"]'
      ) as HTMLInputElement;
      const confirmPasswordInput = document.querySelector(
        'input[name="confirmPassword"]'
      ) as HTMLInputElement;
      const submitButton = screen.getByRole("button", { name: /register/i });

      await act(async () => {
        await user.type(usernameInput, "testuser");
        await user.type(emailInput, "test@example.com");
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
          <Register />
        </TestWrapper>
      );

      const usernameInput = screen.getByRole("textbox", { name: /username/i });
      const emailInput = screen.getByRole("textbox", {
        name: /email address/i,
      });
      const passwordInput = document.querySelector(
        'input[name="password"]'
      ) as HTMLInputElement;
      const confirmPasswordInput = document.querySelector(
        'input[name="confirmPassword"]'
      ) as HTMLInputElement;
      const submitButton = screen.getByRole("button", { name: /register/i });

      await act(async () => {
        await user.type(usernameInput, "testuser");
        await user.type(emailInput, "test@example.com");
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
          <Register />
        </TestWrapper>
      );

      const usernameInput = screen.getByRole("textbox", { name: /username/i });
      const emailInput = screen.getByRole("textbox", {
        name: /email address/i,
      });
      const passwordInput = document.querySelector(
        'input[name="password"]'
      ) as HTMLInputElement;
      const confirmPasswordInput = document.querySelector(
        'input[name="confirmPassword"]'
      ) as HTMLInputElement;
      const submitButton = screen.getByRole("button", { name: /register/i });

      await act(async () => {
        await user.type(usernameInput, "testuser");
        await user.type(emailInput, "test@example.com");
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

    test("shows error for invalid email format", async () => {
      const user = userEvent.setup();
      render(
        <TestWrapper>
          <Register />
        </TestWrapper>
      );

      const usernameInput = screen.getByRole("textbox", { name: /username/i });
      const emailInput = screen.getByRole("textbox", {
        name: /email address/i,
      });
      const passwordInput = document.querySelector(
        'input[name="password"]'
      ) as HTMLInputElement;
      const confirmPasswordInput = document.querySelector(
        'input[name="confirmPassword"]'
      ) as HTMLInputElement;
      const submitButton = screen.getByRole("button", { name: /register/i });

      await act(async () => {
        await user.type(usernameInput, "testuser");
        await user.type(emailInput, "invalid-email");
        await user.type(passwordInput, "Password123");
        await user.type(confirmPasswordInput, "Password123");
        await user.click(submitButton);
      });

      await waitFor(() => {
        expect(
          screen.getByText("Please enter a valid email address")
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
          <Register />
        </TestWrapper>
      );

      const usernameInput = screen.getByRole("textbox", { name: /username/i });
      const emailInput = screen.getByRole("textbox", {
        name: /email address/i,
      });
      const passwordInput = document.querySelector(
        'input[name="password"]'
      ) as HTMLInputElement;
      const confirmPasswordInput = document.querySelector(
        'input[name="confirmPassword"]'
      ) as HTMLInputElement;
      const submitButton = screen.getByRole("button", { name: /register/i });

      await act(async () => {
        await user.type(usernameInput, "testuser");
        await user.type(emailInput, "test@example.com");
        await user.type(passwordInput, "Password123");
        await user.type(confirmPasswordInput, "Password123");
        await user.click(submitButton);
      });

      // Should show loading spinner
      expect(screen.getByRole("progressbar")).toBeInTheDocument();
      expect(usernameInput).toBeDisabled();
      expect(emailInput).toBeDisabled();

      // Wait for completion
      await waitFor(() => {
        expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
      });
    });

    test("shows success message and calls navigate on successful registration", async () => {
      const user = userEvent.setup();
      mockedAxios.post.mockResolvedValue({ data: {} });

      render(
        <TestWrapper>
          <Register />
        </TestWrapper>
      );

      const usernameInput = screen.getByRole("textbox", {
        name: /username/i,
      });
      const emailInput = screen.getByRole("textbox", {
        name: /email address/i,
      });
      const passwordInput = document.querySelector(
        'input[name="password"]'
      ) as HTMLInputElement;
      const confirmPasswordInput = document.querySelector(
        'input[name="confirmPassword"]'
      ) as HTMLInputElement;
      const submitButton = screen.getByRole("button", { name: /register/i });

      await act(async () => {
        await user.type(usernameInput, "testuser");
        await user.type(emailInput, "test@example.com");
        await user.type(passwordInput, "Password123");
        await user.type(confirmPasswordInput, "Password123");
        await user.click(submitButton);
      });

      await waitFor(() => {
        expect(
          screen.getByText("Registration successful! You can now login.")
        ).toBeInTheDocument();
      });

      expect(mockedAxios.post).toHaveBeenCalledWith("/auth/register", {
        username: "testuser",
        email: "test@example.com",
        password: "Password123",
        full_name: "",
      });

      // Wait for navigation to be called (after 2 second timeout)
      await waitFor(
        () => {
          expect(mockNavigate).toHaveBeenCalledWith("/login");
        },
        { timeout: 3000 }
      );
    });

    test("includes full name when provided", async () => {
      const user = userEvent.setup();
      mockedAxios.post.mockResolvedValue({ data: {} });

      render(
        <TestWrapper>
          <Register />
        </TestWrapper>
      );

      const usernameInput = screen.getByRole("textbox", { name: /username/i });
      const emailInput = screen.getByRole("textbox", {
        name: /email address/i,
      });
      const fullNameInput = screen.getByRole("textbox", { name: /full name/i });
      const passwordInput = document.querySelector(
        'input[name="password"]'
      ) as HTMLInputElement;
      const confirmPasswordInput = document.querySelector(
        'input[name="confirmPassword"]'
      ) as HTMLInputElement;
      const submitButton = screen.getByRole("button", { name: /register/i });

      await act(async () => {
        await user.type(usernameInput, "testuser");
        await user.type(emailInput, "test@example.com");
        await user.type(fullNameInput, "Test User");
        await user.type(passwordInput, "Password123");
        await user.type(confirmPasswordInput, "Password123");
        await user.click(submitButton);
      });

      await waitFor(() => {
        expect(mockedAxios.post).toHaveBeenCalledWith("/auth/register", {
          username: "testuser",
          email: "test@example.com",
          password: "Password123",
          full_name: "Test User",
        });
      });
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
          <Register />
        </TestWrapper>
      );

      const usernameInput = screen.getByRole("textbox", { name: /username/i });
      const emailInput = screen.getByRole("textbox", {
        name: /email address/i,
      });
      const passwordInput = document.querySelector(
        'input[name="password"]'
      ) as HTMLInputElement;
      const confirmPasswordInput = document.querySelector(
        'input[name="confirmPassword"]'
      ) as HTMLInputElement;
      const submitButton = screen.getByRole("button", { name: /register/i });

      await act(async () => {
        await user.type(usernameInput, "testuser");
        await user.type(emailInput, "test@example.com");
        await user.type(passwordInput, "Password123");
        await user.type(confirmPasswordInput, "Password123");
        await user.click(submitButton);
      });

      await waitFor(() => {
        expect(screen.getByText("Server error")).toBeInTheDocument();
      });
    });

    test("displays field validation errors from server", async () => {
      const user = userEvent.setup();
      const mockError = {
        isAxiosError: true,
        response: {
          status: 422,
          data: {
            detail: [
              {
                loc: ["username"],
                msg: "Username already exists",
                type: "value_error",
              },
              {
                loc: ["email"],
                msg: "Email already registered",
                type: "value_error",
              },
            ],
          },
        },
      };
      mockedAxios.post.mockRejectedValue(mockError);

      render(
        <TestWrapper>
          <Register />
        </TestWrapper>
      );

      const usernameInput = screen.getByRole("textbox", { name: /username/i });
      const emailInput = screen.getByRole("textbox", {
        name: /email address/i,
      });
      const passwordInput = document.querySelector(
        'input[name="password"]'
      ) as HTMLInputElement;
      const confirmPasswordInput = document.querySelector(
        'input[name="confirmPassword"]'
      ) as HTMLInputElement;
      const submitButton = screen.getByRole("button", { name: /register/i });

      await act(async () => {
        await user.type(usernameInput, "testuser");
        await user.type(emailInput, "test@example.com");
        await user.type(passwordInput, "Password123");
        await user.type(confirmPasswordInput, "Password123");
        await user.click(submitButton);
      });

      await waitFor(() => {
        // Check for field validation errors in helper text
        expect(screen.getByText("Username already exists")).toBeInTheDocument();
        expect(
          screen.getByText("Email already registered")
        ).toBeInTheDocument();
      });

      // Fields should show error state
      expect(usernameInput).toHaveAttribute("aria-invalid", "true");
      expect(emailInput).toHaveAttribute("aria-invalid", "true");
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
          <Register />
        </TestWrapper>
      );

      const usernameInput = screen.getByRole("textbox", { name: /username/i });
      const emailInput = screen.getByRole("textbox", {
        name: /email address/i,
      });
      const passwordInput = document.querySelector(
        'input[name="password"]'
      ) as HTMLInputElement;
      const confirmPasswordInput = document.querySelector(
        'input[name="confirmPassword"]'
      ) as HTMLInputElement;
      const submitButton = screen.getByRole("button", { name: /register/i });

      await act(async () => {
        await user.type(usernameInput, "testuser");
        await user.type(emailInput, "test@example.com");
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
    test("sign in link has correct href", () => {
      render(
        <TestWrapper>
          <Register />
        </TestWrapper>
      );

      const signInLink = screen.getByRole("link", { name: /sign in/i });
      expect(signInLink).toHaveAttribute("href", "/login");
    });
  });

  describe("Accessibility", () => {
    test("form has proper labels and structure", () => {
      render(
        <TestWrapper>
          <Register />
        </TestWrapper>
      );

      const usernameInput = screen.getByRole("textbox", { name: /username/i });
      const emailInput = screen.getByRole("textbox", {
        name: /email address/i,
      });
      const fullNameInput = screen.getByRole("textbox", { name: /full name/i });
      const passwordInput = document.querySelector(
        'input[name="password"]'
      ) as HTMLInputElement;
      const confirmPasswordInput = document.querySelector(
        'input[name="confirmPassword"]'
      ) as HTMLInputElement;

      expect(usernameInput).toHaveAttribute("required");
      expect(usernameInput).toHaveAttribute("autoComplete", "username");
      expect(emailInput).toHaveAttribute("required");
      expect(emailInput).toHaveAttribute("autoComplete", "email");
      expect(fullNameInput).toHaveAttribute("autoComplete", "name");
      expect(passwordInput).toHaveAttribute("required");
      expect(passwordInput).toHaveAttribute("type", "password");
      expect(passwordInput).toHaveAttribute("autoComplete", "new-password");
      expect(confirmPasswordInput).toHaveAttribute("required");
      expect(confirmPasswordInput).toHaveAttribute("type", "password");
      expect(confirmPasswordInput).toHaveAttribute(
        "autoComplete",
        "new-password"
      );

      const submitButton = screen.getByRole("button", { name: /register/i });
      expect(submitButton).toHaveAttribute("type", "submit");
    });

    test("password helper text is displayed", () => {
      render(
        <TestWrapper>
          <Register />
        </TestWrapper>
      );

      expect(
        screen.getByText(
          "Password must be at least 8 characters long and contain uppercase, lowercase, and numbers"
        )
      ).toBeInTheDocument();
    });
  });
});
