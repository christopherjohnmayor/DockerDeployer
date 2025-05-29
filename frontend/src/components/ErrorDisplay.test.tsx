import React from "react";
import { render, screen, fireEvent, act } from "@testing-library/react";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import ErrorDisplay, { CompactErrorDisplay } from "./ErrorDisplay";
import { AppError, ErrorType } from "../utils/errorHandling";

// Create a theme for testing
const theme = createTheme();

// Test wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ThemeProvider theme={theme}>{children}</ThemeProvider>
);

describe("ErrorDisplay Component", () => {
  const mockOnRetry = jest.fn();
  const mockOnDismiss = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("returns null when no error is provided", () => {
    render(
      <TestWrapper>
        <ErrorDisplay error={null} />
      </TestWrapper>
    );

    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  test("renders string error correctly", async () => {
    await act(async () => {
      render(
        <TestWrapper>
          <ErrorDisplay error="Simple error message" />
        </TestWrapper>
      );
    });

    expect(screen.getByText("Error")).toBeInTheDocument();
    expect(screen.getByText("Simple error message")).toBeInTheDocument();
  });

  test("renders AppError object correctly", async () => {
    const error: AppError = {
      type: ErrorType.NETWORK,
      message: "Network connection failed",
      details: "Connection timeout",
      code: 500,
    };

    await act(async () => {
      render(
        <TestWrapper>
          <ErrorDisplay error={error} />
        </TestWrapper>
      );
    });

    expect(screen.getByText("Connection Error")).toBeInTheDocument();
    expect(screen.getByText("Network connection failed")).toBeInTheDocument();
  });

  test("displays different error variants", async () => {
    const error: AppError = {
      type: ErrorType.VALIDATION,
      message: "Validation error",
    };

    // Test outlined variant
    const { rerender } = render(
      <TestWrapper>
        <ErrorDisplay error={error} variant="outlined" />
      </TestWrapper>
    );

    let alertElement = screen.getByRole("alert");
    expect(alertElement).toHaveClass("MuiAlert-outlined");

    // Test filled variant
    await act(async () => {
      rerender(
        <TestWrapper>
          <ErrorDisplay error={error} variant="filled" />
        </TestWrapper>
      );
    });

    alertElement = screen.getByRole("alert");
    expect(alertElement).toHaveClass("MuiAlert-filled");

    // Test standard variant (default)
    await act(async () => {
      rerender(
        <TestWrapper>
          <ErrorDisplay error={error} variant="standard" />
        </TestWrapper>
      );
    });

    alertElement = screen.getByRole("alert");
    expect(alertElement).toHaveClass("MuiAlert-standard");
  });

  test("displays appropriate severity levels for different error types", async () => {
    const testCases = [
      { type: ErrorType.NETWORK, expectedSeverity: "Error" },
      { type: ErrorType.VALIDATION, expectedSeverity: "Warning" },
      { type: ErrorType.AUTHENTICATION, expectedSeverity: "Info" },
      { type: ErrorType.AUTHORIZATION, expectedSeverity: "Info" },
      { type: ErrorType.SERVER, expectedSeverity: "Error" },
      { type: ErrorType.UNKNOWN, expectedSeverity: "Error" },
    ];

    for (const testCase of testCases) {
      const error: AppError = {
        type: testCase.type,
        message: `${testCase.type} error`,
      };

      const { unmount } = render(
        <TestWrapper>
          <ErrorDisplay error={error} />
        </TestWrapper>
      );

      const alertElement = screen.getByRole("alert");
      expect(alertElement).toHaveClass(
        `MuiAlert-color${testCase.expectedSeverity}`
      );

      unmount();
    }
  });

  test("shows correct titles for different error types", async () => {
    const testCases = [
      { type: ErrorType.NETWORK, expectedTitle: "Connection Error" },
      { type: ErrorType.VALIDATION, expectedTitle: "Validation Error" },
      {
        type: ErrorType.AUTHENTICATION,
        expectedTitle: "Authentication Required",
      },
      { type: ErrorType.AUTHORIZATION, expectedTitle: "Access Denied" },
      { type: ErrorType.NOT_FOUND, expectedTitle: "Not Found" },
      { type: ErrorType.SERVER, expectedTitle: "Server Error" },
      { type: ErrorType.UNKNOWN, expectedTitle: "Error" },
    ];

    for (const testCase of testCases) {
      const error: AppError = {
        type: testCase.type,
        message: "Test message",
      };

      const { unmount } = render(
        <TestWrapper>
          <ErrorDisplay error={error} />
        </TestWrapper>
      );

      expect(screen.getByText(testCase.expectedTitle)).toBeInTheDocument();
      unmount();
    }
  });

  test("dismiss functionality works correctly", async () => {
    const error: AppError = {
      type: ErrorType.NETWORK,
      message: "Network error",
    };

    await act(async () => {
      render(
        <TestWrapper>
          <ErrorDisplay error={error} onDismiss={mockOnDismiss} />
        </TestWrapper>
      );
    });

    const dismissButton = screen.getByRole("button", { name: /close/i });
    await act(async () => {
      fireEvent.click(dismissButton);
    });

    expect(mockOnDismiss).toHaveBeenCalledTimes(1);
  });

  test("retry functionality for retryable errors", async () => {
    const retryableError: AppError = {
      type: ErrorType.NETWORK,
      message: "Network connection failed",
    };

    await act(async () => {
      render(
        <TestWrapper>
          <ErrorDisplay error={retryableError} onRetry={mockOnRetry} />
        </TestWrapper>
      );
    });

    const retryButton = screen.getByText("Try Again");
    await act(async () => {
      fireEvent.click(retryButton);
    });

    expect(mockOnRetry).toHaveBeenCalledTimes(1);
  });

  test("does not show retry button for non-retryable errors", async () => {
    const nonRetryableError: AppError = {
      type: ErrorType.VALIDATION,
      message: "Validation failed",
    };

    await act(async () => {
      render(
        <TestWrapper>
          <ErrorDisplay error={nonRetryableError} onRetry={mockOnRetry} />
        </TestWrapper>
      );
    });

    expect(screen.queryByText("Try Again")).not.toBeInTheDocument();
  });

  test("expandable error details functionality", async () => {
    const errorWithDetails: AppError = {
      type: ErrorType.SERVER,
      message: "Server error occurred",
      details: "Internal server error details",
      code: 500,
    };

    await act(async () => {
      render(
        <TestWrapper>
          <ErrorDisplay error={errorWithDetails} showDetails={true} />
        </TestWrapper>
      );
    });

    // When showDetails=true, the expand button should be available
    const expandButton = screen.getByRole("button", { name: /show details/i });
    expect(expandButton).toBeInTheDocument();

    // Click to expand details
    await act(async () => {
      fireEvent.click(expandButton);
    });

    // Details should now be visible
    expect(
      screen.getByText("Internal server error details")
    ).toBeInTheDocument();
    expect(screen.getByText("500")).toBeInTheDocument();

    // Test that the collapse button is available
    const collapseButton = screen.getByRole("button", {
      name: /hide details/i,
    });
    expect(collapseButton).toBeInTheDocument();
  });

  test("handles different sizes correctly", async () => {
    const error: AppError = {
      type: ErrorType.NETWORK,
      message: "Network error",
    };

    // Test small size
    const { rerender } = render(
      <TestWrapper>
        <ErrorDisplay error={error} size="small" />
      </TestWrapper>
    );

    let messageElement = screen.getByText("Network error");
    expect(messageElement).toHaveClass("MuiTypography-body2");

    // Test medium size (default)
    await act(async () => {
      rerender(
        <TestWrapper>
          <ErrorDisplay error={error} size="medium" />
        </TestWrapper>
      );
    });

    messageElement = screen.getByText("Network error");
    expect(messageElement).toHaveClass("MuiTypography-body1");
  });

  test("displays appropriate icons for error types", async () => {
    const testCases = [
      { type: ErrorType.NETWORK, iconTestId: "error-icon" },
      { type: ErrorType.VALIDATION, iconTestId: "warning-icon" },
      { type: ErrorType.AUTHENTICATION, iconTestId: "info-icon" },
    ];

    for (const testCase of testCases) {
      const error: AppError = {
        type: testCase.type,
        message: "Test message",
      };

      const { unmount } = render(
        <TestWrapper>
          <ErrorDisplay error={error} />
        </TestWrapper>
      );

      const alertElement = screen.getByRole("alert");
      const icon = alertElement.querySelector("svg");
      expect(icon).toBeInTheDocument();

      unmount();
    }
  });
});

describe("CompactErrorDisplay Component", () => {
  const mockOnRetry = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("returns null when no error is provided", () => {
    render(
      <TestWrapper>
        <CompactErrorDisplay error={null} />
      </TestWrapper>
    );

    expect(screen.queryByText(/error/i)).not.toBeInTheDocument();
  });

  test("renders string error correctly", async () => {
    await act(async () => {
      render(
        <TestWrapper>
          <CompactErrorDisplay error="Compact error message" />
        </TestWrapper>
      );
    });

    expect(screen.getByText("Compact error message")).toBeInTheDocument();
  });

  test("renders AppError object correctly", async () => {
    const error: AppError = {
      type: ErrorType.NETWORK,
      message: "Network connection failed",
    };

    await act(async () => {
      render(
        <TestWrapper>
          <CompactErrorDisplay error={error} />
        </TestWrapper>
      );
    });

    expect(screen.getByText("Network connection failed")).toBeInTheDocument();
  });

  test("retry functionality works in compact display", async () => {
    const error: AppError = {
      type: ErrorType.NETWORK,
      message: "Network error",
    };

    await act(async () => {
      render(
        <TestWrapper>
          <CompactErrorDisplay error={error} onRetry={mockOnRetry} />
        </TestWrapper>
      );
    });

    const retryButton = screen.getByRole("button");
    await act(async () => {
      fireEvent.click(retryButton);
    });

    expect(mockOnRetry).toHaveBeenCalledTimes(1);
  });

  test("does not show retry button when onRetry is not provided", async () => {
    const error: AppError = {
      type: ErrorType.NETWORK,
      message: "Network error",
    };

    await act(async () => {
      render(
        <TestWrapper>
          <CompactErrorDisplay error={error} />
        </TestWrapper>
      );
    });

    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });
});
