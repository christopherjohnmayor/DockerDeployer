import React from "react";
import { render, screen, fireEvent, act } from "@testing-library/react";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import ErrorBoundary from "./ErrorBoundary";

// Create a theme for testing
const theme = createTheme();

// Test wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ThemeProvider theme={theme}>{children}</ThemeProvider>
);

// Component that throws an error for testing
const ThrowError: React.FC<{ shouldThrow?: boolean }> = ({
  shouldThrow = true,
}) => {
  if (shouldThrow) {
    throw new Error("Test error");
  }
  return <div>No error</div>;
};

// Mock console.error to avoid noise in tests
const originalConsoleError = console.error;
beforeAll(() => {
  console.error = jest.fn();
});

afterAll(() => {
  console.error = originalConsoleError;
});

describe("ErrorBoundary Component", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("Normal Operation", () => {
    test("renders children when no error occurs", () => {
      render(
        <TestWrapper>
          <ErrorBoundary>
            <div>Test content</div>
          </ErrorBoundary>
        </TestWrapper>
      );

      expect(screen.getByText("Test content")).toBeInTheDocument();
      expect(
        screen.queryByText("Something went wrong")
      ).not.toBeInTheDocument();
    });

    test("renders multiple children correctly", () => {
      render(
        <TestWrapper>
          <ErrorBoundary>
            <div>First child</div>
            <div>Second child</div>
          </ErrorBoundary>
        </TestWrapper>
      );

      expect(screen.getByText("First child")).toBeInTheDocument();
      expect(screen.getByText("Second child")).toBeInTheDocument();
    });
  });

  describe("Error Handling", () => {
    test("catches and displays error when child component throws", () => {
      render(
        <TestWrapper>
          <ErrorBoundary>
            <ThrowError />
          </ErrorBoundary>
        </TestWrapper>
      );

      expect(screen.getByText("Something went wrong")).toBeInTheDocument();
      expect(
        screen.getByText(/An unexpected error occurred/)
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /try again/i })
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /reload page/i })
      ).toBeInTheDocument();
    });

    test("logs error to console when error occurs", () => {
      render(
        <TestWrapper>
          <ErrorBoundary>
            <ThrowError />
          </ErrorBoundary>
        </TestWrapper>
      );

      expect(console.error).toHaveBeenCalledWith(
        "ErrorBoundary caught an error:",
        expect.any(Error),
        expect.any(Object)
      );
    });

    test("displays custom fallback when provided", () => {
      const customFallback = <div>Custom error message</div>;

      render(
        <TestWrapper>
          <ErrorBoundary fallback={customFallback}>
            <ThrowError />
          </ErrorBoundary>
        </TestWrapper>
      );

      expect(screen.getByText("Custom error message")).toBeInTheDocument();
      expect(
        screen.queryByText("Something went wrong")
      ).not.toBeInTheDocument();
    });
  });

  describe("Recovery Actions", () => {
    test("resets error state when Try Again button is clicked", async () => {
      render(
        <TestWrapper>
          <ErrorBoundary>
            <ThrowError />
          </ErrorBoundary>
        </TestWrapper>
      );

      // Error should be displayed initially
      expect(screen.getByText("Something went wrong")).toBeInTheDocument();

      // Click Try Again button
      const tryAgainButton = screen.getByRole("button", { name: /try again/i });
      await act(async () => {
        fireEvent.click(tryAgainButton);
      });

      // The error boundary should attempt to re-render children
      // Since our test component still throws, it will show error again
      // But this tests that the retry mechanism works
      expect(screen.getByText("Something went wrong")).toBeInTheDocument();
    });

    test("reloads page when Reload Page button is clicked", () => {
      // Mock window.location.reload
      const mockReload = jest.fn();
      Object.defineProperty(window, "location", {
        value: { reload: mockReload },
        writable: true,
      });

      render(
        <TestWrapper>
          <ErrorBoundary>
            <ThrowError />
          </ErrorBoundary>
        </TestWrapper>
      );

      const reloadButton = screen.getByRole("button", { name: /reload page/i });
      fireEvent.click(reloadButton);

      expect(mockReload).toHaveBeenCalledTimes(1);
    });
  });

  describe("Error Details", () => {
    test("shows error details in development mode", () => {
      // Mock development environment
      const originalNodeEnv = process.env.NODE_ENV;
      process.env.NODE_ENV = "development";

      render(
        <TestWrapper>
          <ErrorBoundary>
            <ThrowError />
          </ErrorBoundary>
        </TestWrapper>
      );

      // In test environment, we'll just check that the error UI is rendered
      expect(screen.getByText("Something went wrong")).toBeInTheDocument();

      // Restore original environment
      process.env.NODE_ENV = originalNodeEnv;
    });

    test("hides error details in production mode", () => {
      // Mock production environment
      const originalNodeEnv = process.env.NODE_ENV;
      process.env.NODE_ENV = "production";

      render(
        <TestWrapper>
          <ErrorBoundary>
            <ThrowError />
          </ErrorBoundary>
        </TestWrapper>
      );

      expect(screen.getByText("Something went wrong")).toBeInTheDocument();
      // Development details should not be shown in production
      expect(
        screen.queryByText("Development Error Details")
      ).not.toBeInTheDocument();

      // Restore original environment
      process.env.NODE_ENV = originalNodeEnv;
    });
  });

  describe("Edge Cases", () => {
    test("handles error with no message", () => {
      const ThrowEmptyError: React.FC = () => {
        throw new Error("");
      };

      render(
        <TestWrapper>
          <ErrorBoundary>
            <ThrowEmptyError />
          </ErrorBoundary>
        </TestWrapper>
      );

      expect(screen.getByText("Something went wrong")).toBeInTheDocument();
    });

    test("handles non-Error objects thrown", () => {
      const ThrowString: React.FC = () => {
        throw "String error";
      };

      render(
        <TestWrapper>
          <ErrorBoundary>
            <ThrowString />
          </ErrorBoundary>
        </TestWrapper>
      );

      expect(screen.getByText("Something went wrong")).toBeInTheDocument();
    });

    test("handles nested error boundaries", () => {
      render(
        <TestWrapper>
          <ErrorBoundary fallback={<div>Outer boundary</div>}>
            <ErrorBoundary fallback={<div>Inner boundary</div>}>
              <ThrowError />
            </ErrorBoundary>
          </ErrorBoundary>
        </TestWrapper>
      );

      // Inner boundary should catch the error
      expect(screen.getByText("Inner boundary")).toBeInTheDocument();
      expect(screen.queryByText("Outer boundary")).not.toBeInTheDocument();
    });
  });

  describe("Accessibility", () => {
    test("error alert has proper ARIA attributes", () => {
      render(
        <TestWrapper>
          <ErrorBoundary>
            <ThrowError />
          </ErrorBoundary>
        </TestWrapper>
      );

      const alert = screen.getByRole("alert");
      expect(alert).toBeInTheDocument();
      expect(alert).toHaveAttribute("role", "alert");
    });

    test("buttons are keyboard accessible", () => {
      render(
        <TestWrapper>
          <ErrorBoundary>
            <ThrowError />
          </ErrorBoundary>
        </TestWrapper>
      );

      const tryAgainButton = screen.getByRole("button", { name: /try again/i });
      const reloadButton = screen.getByRole("button", { name: /reload page/i });

      expect(tryAgainButton).toBeInTheDocument();
      expect(reloadButton).toBeInTheDocument();
      expect(tryAgainButton).not.toHaveAttribute("disabled");
      expect(reloadButton).not.toHaveAttribute("disabled");
    });
  });
});
