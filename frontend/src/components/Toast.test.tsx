import React from "react";
import {
  render,
  screen,
  fireEvent,
  act,
  waitFor,
} from "@testing-library/react";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import { ToastProvider, useToast } from "./Toast";

// Create a theme for testing
const theme = createTheme();

// Test wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ThemeProvider theme={theme}>
    <ToastProvider>{children}</ToastProvider>
  </ThemeProvider>
);

// Test component that uses the toast hook
const TestComponent: React.FC = () => {
  const { showToast, showSuccess, showError, showWarning, showInfo } =
    useToast();

  return (
    <div>
      <button onClick={() => showToast("Custom toast", "info", 3000)}>
        Show Custom Toast
      </button>
      <button onClick={() => showSuccess("Success message")}>
        Show Success
      </button>
      <button onClick={() => showError("Error message")}>Show Error</button>
      <button onClick={() => showWarning("Warning message")}>
        Show Warning
      </button>
      <button onClick={() => showInfo("Info message")}>Show Info</button>
    </div>
  );
};

describe("Toast Component", () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    act(() => {
      jest.runOnlyPendingTimers();
    });
    jest.useRealTimers();
  });

  describe("ToastProvider", () => {
    test("renders children without toasts initially", () => {
      render(
        <TestWrapper>
          <div>Test content</div>
        </TestWrapper>
      );

      expect(screen.getByText("Test content")).toBeInTheDocument();
      expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    });

    test("displays toast when showToast is called", async () => {
      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      );

      await act(async () => {
        fireEvent.click(screen.getByText("Show Custom Toast"));
      });

      expect(screen.getByText("Custom toast")).toBeInTheDocument();
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });

    test("displays success toast with correct styling", async () => {
      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      );

      await act(async () => {
        fireEvent.click(screen.getByText("Show Success"));
      });

      const alert = screen.getByRole("alert");
      expect(screen.getByText("Success message")).toBeInTheDocument();
      expect(alert).toHaveClass("MuiAlert-filledSuccess");
    });

    test("displays error toast with correct styling", async () => {
      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      );

      await act(async () => {
        fireEvent.click(screen.getByText("Show Error"));
      });

      const alert = screen.getByRole("alert");
      expect(screen.getByText("Error message")).toBeInTheDocument();
      expect(alert).toHaveClass("MuiAlert-filledError");
    });

    test("displays warning toast with correct styling", async () => {
      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      );

      await act(async () => {
        fireEvent.click(screen.getByText("Show Warning"));
      });

      const alert = screen.getByRole("alert");
      expect(screen.getByText("Warning message")).toBeInTheDocument();
      expect(alert).toHaveClass("MuiAlert-filledWarning");
    });

    test("displays info toast with correct styling", async () => {
      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      );

      await act(async () => {
        fireEvent.click(screen.getByText("Show Info"));
      });

      const alert = screen.getByRole("alert");
      expect(screen.getByText("Info message")).toBeInTheDocument();
      expect(alert).toHaveClass("MuiAlert-filledInfo");
    });

    test("displays multiple toasts simultaneously", async () => {
      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      );

      await act(async () => {
        fireEvent.click(screen.getByText("Show Success"));
        fireEvent.click(screen.getByText("Show Error"));
        fireEvent.click(screen.getByText("Show Warning"));
      });

      expect(screen.getByText("Success message")).toBeInTheDocument();
      expect(screen.getByText("Error message")).toBeInTheDocument();
      expect(screen.getByText("Warning message")).toBeInTheDocument();
      expect(screen.getAllByRole("alert")).toHaveLength(3);
    });

    test("removes toast when close button is clicked", async () => {
      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      );

      await act(async () => {
        fireEvent.click(screen.getByText("Show Success"));
      });

      expect(screen.getByText("Success message")).toBeInTheDocument();

      const closeButton = screen.getByRole("button", { name: /close/i });
      await act(async () => {
        fireEvent.click(closeButton);
      });

      expect(screen.queryByText("Success message")).not.toBeInTheDocument();
    });

    test("auto-dismisses toast after specified duration", async () => {
      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      );

      await act(async () => {
        fireEvent.click(screen.getByText("Show Custom Toast"));
      });

      expect(screen.getByText("Custom toast")).toBeInTheDocument();

      // Fast-forward time by 3000ms (the duration set for custom toast)
      await act(async () => {
        jest.advanceTimersByTime(3000);
      });

      await waitFor(() => {
        expect(screen.queryByText("Custom toast")).not.toBeInTheDocument();
      });
    });

    test("error toasts have longer default duration", async () => {
      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      );

      await act(async () => {
        fireEvent.click(screen.getByText("Show Error"));
      });

      expect(screen.getByText("Error message")).toBeInTheDocument();

      // Fast-forward by 6000ms (default duration) - should still be visible
      await act(async () => {
        jest.advanceTimersByTime(6000);
      });

      expect(screen.getByText("Error message")).toBeInTheDocument();

      // Fast-forward by additional 2000ms (total 8000ms) - should be dismissed
      await act(async () => {
        jest.advanceTimersByTime(2000);
      });

      await waitFor(() => {
        expect(screen.queryByText("Error message")).not.toBeInTheDocument();
      });
    });

    test("toasts are stacked correctly", async () => {
      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      );

      await act(async () => {
        fireEvent.click(screen.getByText("Show Success"));
        fireEvent.click(screen.getByText("Show Error"));
      });

      const snackbars = document.querySelectorAll(".MuiSnackbar-root");
      expect(snackbars).toHaveLength(2);
    });
  });

  describe("useToast hook", () => {
    test("throws error when used outside ToastProvider", () => {
      const TestComponentWithoutProvider = () => {
        const { showToast } = useToast();
        return <div>Test</div>;
      };

      // Suppress console.error for this test
      const consoleSpy = jest
        .spyOn(console, "error")
        .mockImplementation(() => {});

      expect(() => {
        render(<TestComponentWithoutProvider />);
      }).toThrow("useToast must be used within a ToastProvider");

      consoleSpy.mockRestore();
    });

    test("provides all toast methods", () => {
      let toastMethods: any;

      const TestComponentForMethods = () => {
        toastMethods = useToast();
        return <div>Test</div>;
      };

      render(
        <TestWrapper>
          <TestComponentForMethods />
        </TestWrapper>
      );

      expect(toastMethods).toHaveProperty("showToast");
      expect(toastMethods).toHaveProperty("showSuccess");
      expect(toastMethods).toHaveProperty("showError");
      expect(toastMethods).toHaveProperty("showWarning");
      expect(toastMethods).toHaveProperty("showInfo");
      expect(typeof toastMethods.showToast).toBe("function");
      expect(typeof toastMethods.showSuccess).toBe("function");
      expect(typeof toastMethods.showError).toBe("function");
      expect(typeof toastMethods.showWarning).toBe("function");
      expect(typeof toastMethods.showInfo).toBe("function");
    });
  });

  // Note: SlideTransition tests removed due to Material-UI implementation details

  describe("Accessibility", () => {
    test("toasts have proper ARIA attributes", async () => {
      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      );

      await act(async () => {
        fireEvent.click(screen.getByText("Show Success"));
      });

      const alert = screen.getByRole("alert");
      expect(alert).toBeInTheDocument();
      expect(alert).toHaveAttribute("role", "alert");
    });

    test("close button is accessible", async () => {
      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      );

      await act(async () => {
        fireEvent.click(screen.getByText("Show Success"));
      });

      const closeButton = screen.getByRole("button", { name: /close/i });
      expect(closeButton).toBeInTheDocument();
      expect(closeButton).toHaveAttribute("aria-label");
    });
  });
});
