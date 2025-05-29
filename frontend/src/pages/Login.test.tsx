import React from "react";
import {
  render,
  screen,
  fireEvent,
  waitFor,
  act,
} from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import axios from "axios";
import Login from "./Login";

// Mock axios
jest.mock("axios");
const mockedAxios = axios as jest.Mocked<typeof axios>;

// Mock useAuth hook
const mockLogin = jest.fn();
const mockUseAuth = jest.fn();
jest.mock("../hooks/useAuth", () => ({
  useAuth: () => mockUseAuth(),
}));

// Mock useToast hook
const mockShowSuccess = jest.fn();
const mockShowError = jest.fn();
const mockUseToast = jest.fn();
jest.mock("../components/Toast", () => ({
  useToast: () => mockUseToast(),
}));

// Mock useNavigate
const mockNavigate = jest.fn();
jest.mock("react-router-dom", () => ({
  ...jest.requireActual("react-router-dom"),
  useNavigate: () => mockNavigate,
}));

// Mock ErrorDisplay component
jest.mock("../components/ErrorDisplay", () => {
  return function MockErrorDisplay({
    error,
    onDismiss,
  }: {
    error: string;
    onDismiss: () => void;
  }) {
    return (
      <div data-testid="error-display">
        {error}
        <button onClick={onDismiss}>Dismiss</button>
      </div>
    );
  };
});

// Mock error handling utilities
jest.mock("../utils/errorHandling", () => ({
  parseError: jest.fn((err: any) => ({
    message: err.response?.data?.detail || "An error occurred",
  })),
  getValidationErrors: jest.fn(() => ({})),
}));

import { parseError, getValidationErrors } from "../utils/errorHandling";
const mockedParseError = parseError as jest.MockedFunction<typeof parseError>;
const mockedGetValidationErrors = getValidationErrors as jest.MockedFunction<
  typeof getValidationErrors
>;

// Wrapper component for tests
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <MemoryRouter>{children}</MemoryRouter>
);

// Suppress Material-UI warnings in tests
const originalError = console.error;
beforeAll(() => {
  console.error = (...args: any[]) => {
    if (
      typeof args[0] === "string" &&
      (args[0].includes("Warning: An update to") ||
        args[0].includes("Warning: validateDOMNesting") ||
        args[0].includes("Warning: React does not recognize"))
    ) {
      return;
    }
    originalError.call(console, ...args);
  };
});

afterAll(() => {
  console.error = originalError;
});

describe("Login Component", () => {
  // Helper function to get form inputs
  const getFormInputs = () => {
    // Use more reliable selectors for Material-UI components
    const usernameInput = screen.getByRole("textbox", {
      name: /username or email/i,
    });
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole("button", { name: "Sign In" });
    return { usernameInput, passwordInput, submitButton };
  };

  beforeEach(() => {
    jest.clearAllMocks();

    // Set up default mocks
    mockUseAuth.mockReturnValue({
      login: mockLogin,
    });

    mockUseToast.mockReturnValue({
      showSuccess: mockShowSuccess,
      showError: mockShowError,
    });

    mockedParseError.mockImplementation((err: any) => ({
      message: err.response?.data?.detail || "An error occurred",
    }));

    mockedGetValidationErrors.mockReturnValue({});
  });

  test("renders login form correctly", async () => {
    await act(async () => {
      render(
        <TestWrapper>
          <Login />
        </TestWrapper>
      );
    });

    expect(screen.getByText("DockerDeployer")).toBeInTheDocument();
    expect(screen.getByText("Login")).toBeInTheDocument();

    // Check form inputs using our helper function
    const { usernameInput, passwordInput, submitButton } = getFormInputs();
    expect(usernameInput).toBeInTheDocument();
    expect(passwordInput).toBeInTheDocument();
    expect(submitButton).toBeInTheDocument();

    // Check navigation links
    expect(screen.getByText("Forgot your password?")).toBeInTheDocument();
    expect(screen.getByText("Don't have an account?")).toBeInTheDocument();
    expect(screen.getByText("Register")).toBeInTheDocument();
  });

  test("disables submit button when fields are empty", async () => {
    await act(async () => {
      render(
        <TestWrapper>
          <Login />
        </TestWrapper>
      );
    });

    const submitButton = screen.getByRole("button", { name: "Sign In" });
    expect(submitButton).toBeDisabled();
  });

  test("enables submit button when both fields are filled", async () => {
    await act(async () => {
      render(
        <TestWrapper>
          <Login />
        </TestWrapper>
      );
    });

    const { usernameInput, passwordInput, submitButton } = getFormInputs();

    await act(async () => {
      fireEvent.change(usernameInput, { target: { value: "testuser" } });
      fireEvent.change(passwordInput, { target: { value: "password123" } });
    });

    expect(submitButton).not.toBeDisabled();
  });

  test("handles successful login", async () => {
    const mockResponse = {
      data: {
        access_token: "mock-access-token",
        refresh_token: "mock-refresh-token",
      },
    };

    mockedAxios.post.mockResolvedValue(mockResponse);

    await act(async () => {
      render(
        <TestWrapper>
          <Login />
        </TestWrapper>
      );
    });

    const { usernameInput, passwordInput, submitButton } = getFormInputs();

    await act(async () => {
      fireEvent.change(usernameInput, { target: { value: "testuser" } });
      fireEvent.change(passwordInput, { target: { value: "password123" } });
    });

    await act(async () => {
      fireEvent.click(submitButton);
    });

    await waitFor(() => {
      expect(mockedAxios.post).toHaveBeenCalledWith("/auth/login", {
        username: "testuser",
        password: "password123",
      });
    });

    expect(mockLogin).toHaveBeenCalledWith(
      "mock-access-token",
      "mock-refresh-token"
    );
    expect(mockShowSuccess).toHaveBeenCalledWith(
      "Login successful! Welcome back."
    );
    expect(mockNavigate).toHaveBeenCalledWith("/");
  });

  test("handles login error", async () => {
    const mockError = {
      response: {
        data: {
          detail: "Invalid credentials",
        },
      },
    };

    mockedAxios.post.mockRejectedValue(mockError);
    mockedParseError.mockReturnValue({ message: "Invalid credentials" });

    await act(async () => {
      render(
        <TestWrapper>
          <Login />
        </TestWrapper>
      );
    });

    const { usernameInput, passwordInput, submitButton } = getFormInputs();

    await act(async () => {
      fireEvent.change(usernameInput, { target: { value: "testuser" } });
      fireEvent.change(passwordInput, { target: { value: "wrongpassword" } });
    });

    await act(async () => {
      fireEvent.click(submitButton);
    });

    await waitFor(() => {
      expect(screen.getByTestId("error-display")).toBeInTheDocument();
      expect(screen.getByText("Invalid credentials")).toBeInTheDocument();
    });

    expect(mockLogin).not.toHaveBeenCalled();
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  test("handles validation errors", async () => {
    const mockError = {
      response: {
        data: {
          detail: "Validation failed",
        },
      },
    };

    const mockValidationErrors = {
      username: "Username is required",
      password: "Password must be at least 8 characters",
    };

    mockedAxios.post.mockRejectedValue(mockError);
    mockedGetValidationErrors.mockReturnValue(mockValidationErrors);

    await act(async () => {
      render(
        <TestWrapper>
          <Login />
        </TestWrapper>
      );
    });

    const { usernameInput, passwordInput, submitButton } = getFormInputs();

    await act(async () => {
      fireEvent.change(usernameInput, { target: { value: "test" } });
      fireEvent.change(passwordInput, { target: { value: "123" } });
    });

    await act(async () => {
      fireEvent.click(submitButton);
    });

    await waitFor(() => {
      expect(screen.getByText("Username is required")).toBeInTheDocument();
      expect(
        screen.getByText("Password must be at least 8 characters")
      ).toBeInTheDocument();
    });

    expect(mockLogin).not.toHaveBeenCalled();
  });

  test("shows loading state during submission", async () => {
    // Create a promise that we can control
    let resolvePromise: (value: any) => void;
    const mockPromise = new Promise((resolve) => {
      resolvePromise = resolve;
    });

    mockedAxios.post.mockReturnValue(mockPromise);

    await act(async () => {
      render(
        <TestWrapper>
          <Login />
        </TestWrapper>
      );
    });

    const { usernameInput, passwordInput, submitButton } = getFormInputs();

    await act(async () => {
      fireEvent.change(usernameInput, { target: { value: "testuser" } });
      fireEvent.change(passwordInput, { target: { value: "password123" } });
    });

    await act(async () => {
      fireEvent.click(submitButton);
    });

    // Check loading state
    expect(screen.getByRole("progressbar")).toBeInTheDocument();
    expect(usernameInput).toBeDisabled();
    expect(passwordInput).toBeDisabled();
    expect(submitButton).toBeDisabled();

    // Resolve the promise to finish the test
    await act(async () => {
      resolvePromise!({
        data: {
          access_token: "token",
          refresh_token: "refresh",
        },
      });
    });
  });

  test("dismisses error message when dismiss button is clicked", async () => {
    const mockError = {
      response: {
        data: {
          detail: "Invalid credentials",
        },
      },
    };

    mockedAxios.post.mockRejectedValue(mockError);
    mockedParseError.mockReturnValue({ message: "Invalid credentials" });

    await act(async () => {
      render(
        <TestWrapper>
          <Login />
        </TestWrapper>
      );
    });

    const { usernameInput, passwordInput, submitButton } = getFormInputs();

    await act(async () => {
      fireEvent.change(usernameInput, { target: { value: "testuser" } });
      fireEvent.change(passwordInput, { target: { value: "wrongpassword" } });
    });

    await act(async () => {
      fireEvent.click(submitButton);
    });

    await waitFor(() => {
      expect(screen.getByTestId("error-display")).toBeInTheDocument();
    });

    // Dismiss the error
    const dismissButton = screen.getByText("Dismiss");
    await act(async () => {
      fireEvent.click(dismissButton);
    });

    expect(screen.queryByTestId("error-display")).not.toBeInTheDocument();
  });

  test("renders navigation links correctly", async () => {
    await act(async () => {
      render(
        <TestWrapper>
          <Login />
        </TestWrapper>
      );
    });

    const forgotPasswordLink = screen.getByText("Forgot your password?");
    const registerLink = screen.getByText("Register");

    expect(forgotPasswordLink.closest("a")).toHaveAttribute(
      "href",
      "/forgot-password"
    );
    expect(registerLink.closest("a")).toHaveAttribute("href", "/register");
  });

  test("shows helper text for username field", async () => {
    await act(async () => {
      render(
        <TestWrapper>
          <Login />
        </TestWrapper>
      );
    });

    expect(
      screen.getByText("Enter your username or email address")
    ).toBeInTheDocument();
  });

  test("clears errors when form is resubmitted", async () => {
    const mockError = {
      response: {
        data: {
          detail: "Invalid credentials",
        },
      },
    };

    mockedAxios.post.mockRejectedValueOnce(mockError).mockResolvedValueOnce({
      data: {
        access_token: "token",
        refresh_token: "refresh",
      },
    });

    mockedParseError.mockReturnValue({ message: "Invalid credentials" });

    await act(async () => {
      render(
        <TestWrapper>
          <Login />
        </TestWrapper>
      );
    });

    const { usernameInput, passwordInput, submitButton } = getFormInputs();

    // First submission with error
    await act(async () => {
      fireEvent.change(usernameInput, { target: { value: "testuser" } });
      fireEvent.change(passwordInput, { target: { value: "wrongpassword" } });
    });

    await act(async () => {
      fireEvent.click(submitButton);
    });

    await waitFor(() => {
      expect(screen.getByTestId("error-display")).toBeInTheDocument();
    });

    // Second submission should clear the error
    await act(async () => {
      fireEvent.change(passwordInput, { target: { value: "correctpassword" } });
    });

    await act(async () => {
      fireEvent.click(submitButton);
    });

    // Error should be cleared during submission
    expect(screen.queryByTestId("error-display")).not.toBeInTheDocument();
  });

  test("handles form submission with Enter key", async () => {
    const mockResponse = {
      data: {
        access_token: "mock-access-token",
        refresh_token: "mock-refresh-token",
      },
    };

    mockedAxios.post.mockResolvedValue(mockResponse);

    await act(async () => {
      render(
        <TestWrapper>
          <Login />
        </TestWrapper>
      );
    });

    const { usernameInput, passwordInput } = getFormInputs();

    await act(async () => {
      fireEvent.change(usernameInput, { target: { value: "testuser" } });
      fireEvent.change(passwordInput, { target: { value: "password123" } });
    });

    // Submit form with Enter key on the form element
    const form = passwordInput.closest("form");
    await act(async () => {
      fireEvent.submit(form!);
    });

    await waitFor(() => {
      expect(mockedAxios.post).toHaveBeenCalledWith("/auth/login", {
        username: "testuser",
        password: "password123",
      });
    });
  });
});
