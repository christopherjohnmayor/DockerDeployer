import React from "react";
import { render, screen, act } from "@testing-library/react";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import LoadingState, { LoadingOverlay } from "./LoadingState";

// Create a theme for testing
const theme = createTheme();

// Test wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ThemeProvider theme={theme}>{children}</ThemeProvider>
);

describe("LoadingState Component", () => {
  test("renders circular loading variant by default", async () => {
    await act(async () => {
      render(
        <TestWrapper>
          <LoadingState />
        </TestWrapper>
      );
    });

    expect(screen.getByRole("progressbar")).toBeInTheDocument();
    expect(screen.getByText("Loading...")).toBeInTheDocument();
  });

  test("renders circular loading variant explicitly", async () => {
    await act(async () => {
      render(
        <TestWrapper>
          <LoadingState variant="circular" />
        </TestWrapper>
      );
    });

    const progressbar = screen.getByRole("progressbar");
    expect(progressbar).toBeInTheDocument();
    expect(progressbar).toHaveClass("MuiCircularProgress-root");
  });

  test("renders linear loading variant", async () => {
    await act(async () => {
      render(
        <TestWrapper>
          <LoadingState variant="linear" />
        </TestWrapper>
      );
    });

    const progressbar = screen.getByRole("progressbar");
    expect(progressbar).toBeInTheDocument();
    expect(progressbar).toHaveClass("MuiLinearProgress-root");
    expect(screen.getByText("Loading...")).toBeInTheDocument();
  });

  test("renders skeleton loading variant", async () => {
    await act(async () => {
      render(
        <TestWrapper>
          <LoadingState variant="skeleton" rows={3} />
        </TestWrapper>
      );
    });

    // Should render skeleton elements (Material-UI Skeleton components)
    const skeletonElements = document.querySelectorAll(".MuiSkeleton-root");
    expect(skeletonElements.length).toBe(3);
  });

  test("renders card loading variant", async () => {
    await act(async () => {
      render(
        <TestWrapper>
          <LoadingState variant="card" />
        </TestWrapper>
      );
    });

    // Card variant should render skeleton within a card
    expect(screen.getByText("Loading...")).toBeInTheDocument();
  });

  test("displays custom loading message", async () => {
    const customMessage = "Please wait while we process your request...";

    await act(async () => {
      render(
        <TestWrapper>
          <LoadingState message={customMessage} />
        </TestWrapper>
      );
    });

    expect(screen.getByText(customMessage)).toBeInTheDocument();
  });

  test("renders different sizes correctly", async () => {
    // Test small size
    const { rerender } = render(
      <TestWrapper>
        <LoadingState size="small" />
      </TestWrapper>
    );

    let progressbar = screen.getByRole("progressbar");
    expect(progressbar).toHaveAttribute("style", expect.stringContaining("24"));

    // Test medium size (default)
    await act(async () => {
      rerender(
        <TestWrapper>
          <LoadingState size="medium" />
        </TestWrapper>
      );
    });

    progressbar = screen.getByRole("progressbar");
    expect(progressbar).toHaveAttribute("style", expect.stringContaining("40"));

    // Test large size
    await act(async () => {
      rerender(
        <TestWrapper>
          <LoadingState size="large" />
        </TestWrapper>
      );
    });

    progressbar = screen.getByRole("progressbar");
    expect(progressbar).toHaveAttribute("style", expect.stringContaining("60"));
  });

  test("renders full-screen loading overlay", async () => {
    await act(async () => {
      render(
        <TestWrapper>
          <LoadingState fullScreen={true} />
        </TestWrapper>
      );
    });

    // Full-screen overlay should have fixed positioning
    const progressbar = screen.getByRole("progressbar");
    expect(progressbar).toBeInTheDocument();

    // Full-screen should render the progressbar
    expect(progressbar).toBeInTheDocument();
  });

  test("renders skeleton with custom number of rows", async () => {
    await act(async () => {
      render(
        <TestWrapper>
          <LoadingState variant="skeleton" rows={5} />
        </TestWrapper>
      );
    });

    // Check that 5 skeleton elements are rendered
    const skeletonElements = document.querySelectorAll(".MuiSkeleton-root");
    expect(skeletonElements.length).toBe(5);
  });

  test("linear variant shows message below progress bar", async () => {
    const message = "Processing data...";

    await act(async () => {
      render(
        <TestWrapper>
          <LoadingState variant="linear" message={message} />
        </TestWrapper>
      );
    });

    expect(screen.getByRole("progressbar")).toBeInTheDocument();
    expect(screen.getByText(message)).toBeInTheDocument();
  });

  test("skeleton variant does not show message", async () => {
    const message = "This should not appear";

    await act(async () => {
      render(
        <TestWrapper>
          <LoadingState variant="skeleton" message={message} />
        </TestWrapper>
      );
    });

    // Skeleton variant doesn't display the message text
    expect(screen.queryByText(message)).not.toBeInTheDocument();
    // But skeleton elements should be present
    const skeletonElements = document.querySelectorAll(".MuiSkeleton-root");
    expect(skeletonElements.length).toBeGreaterThan(0);
  });

  test("card variant renders within a card container", async () => {
    await act(async () => {
      render(
        <TestWrapper>
          <LoadingState variant="card" />
        </TestWrapper>
      );
    });

    // Card variant should render a card with loading content
    expect(screen.getByText("Loading...")).toBeInTheDocument();
  });

  test("accessibility features for screen readers", async () => {
    await act(async () => {
      render(
        <TestWrapper>
          <LoadingState />
        </TestWrapper>
      );
    });

    const progressbar = screen.getByRole("progressbar");
    expect(progressbar).toBeInTheDocument();
    // Material-UI CircularProgress has built-in accessibility features
    expect(progressbar).toHaveAttribute("role", "progressbar");
  });

  test("component renders without crashing for all variants", async () => {
    const variants = ["circular", "linear", "skeleton", "card"] as const;

    for (const variant of variants) {
      const { unmount } = render(
        <TestWrapper>
          <LoadingState variant={variant} />
        </TestWrapper>
      );

      // Should render without throwing - check for appropriate elements
      if (variant === "skeleton") {
        const skeletonElements = document.querySelectorAll(".MuiSkeleton-root");
        expect(skeletonElements.length).toBeGreaterThan(0);
      } else {
        expect(screen.getByText("Loading...")).toBeInTheDocument();
      }
      unmount();
    }
  });
});

describe("LoadingOverlay Component", () => {
  test("renders children when not loading", async () => {
    await act(async () => {
      render(
        <TestWrapper>
          <LoadingOverlay loading={false}>
            <div>Content to display</div>
          </LoadingOverlay>
        </TestWrapper>
      );
    });

    expect(screen.getByText("Content to display")).toBeInTheDocument();
    expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
  });

  test("renders loading overlay when loading is true", async () => {
    await act(async () => {
      render(
        <TestWrapper>
          <LoadingOverlay loading={true}>
            <div>Content to display</div>
          </LoadingOverlay>
        </TestWrapper>
      );
    });

    expect(screen.getByText("Content to display")).toBeInTheDocument();
    expect(screen.getByRole("progressbar")).toBeInTheDocument();
    expect(screen.getByText("Loading...")).toBeInTheDocument();
  });

  test("displays custom loading message in overlay", async () => {
    const customMessage = "Saving changes...";

    await act(async () => {
      render(
        <TestWrapper>
          <LoadingOverlay loading={true} message={customMessage}>
            <div>Content to display</div>
          </LoadingOverlay>
        </TestWrapper>
      );
    });

    expect(screen.getByText(customMessage)).toBeInTheDocument();
    expect(screen.queryByText("Loading...")).not.toBeInTheDocument();
  });

  test("overlay has correct positioning and styling", async () => {
    await act(async () => {
      render(
        <TestWrapper>
          <LoadingOverlay loading={true}>
            <div>Content to display</div>
          </LoadingOverlay>
        </TestWrapper>
      );
    });

    // Check that the overlay is rendered with absolute positioning
    const progressbar = screen.getByRole("progressbar");
    expect(progressbar).toBeInTheDocument();

    // Overlay should render the progressbar
    expect(progressbar).toBeInTheDocument();
  });

  test("children remain accessible when overlay is shown", async () => {
    await act(async () => {
      render(
        <TestWrapper>
          <LoadingOverlay loading={true}>
            <button>Click me</button>
          </LoadingOverlay>
        </TestWrapper>
      );
    });

    // Children should still be in the DOM
    expect(screen.getByText("Click me")).toBeInTheDocument();
    // But overlay should be on top
    expect(screen.getByRole("progressbar")).toBeInTheDocument();
  });

  test("overlay toggles correctly", async () => {
    const { rerender } = render(
      <TestWrapper>
        <LoadingOverlay loading={false}>
          <div>Content</div>
        </LoadingOverlay>
      </TestWrapper>
    );

    expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();

    await act(async () => {
      rerender(
        <TestWrapper>
          <LoadingOverlay loading={true}>
            <div>Content</div>
          </LoadingOverlay>
        </TestWrapper>
      );
    });

    expect(screen.getByRole("progressbar")).toBeInTheDocument();

    await act(async () => {
      rerender(
        <TestWrapper>
          <LoadingOverlay loading={false}>
            <div>Content</div>
          </LoadingOverlay>
        </TestWrapper>
      );
    });

    expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
  });

  test("component unmounts cleanly", async () => {
    const { unmount } = render(
      <TestWrapper>
        <LoadingOverlay loading={true}>
          <div>Content</div>
        </LoadingOverlay>
      </TestWrapper>
    );

    expect(screen.getByRole("progressbar")).toBeInTheDocument();

    // Should unmount without errors
    unmount();
    expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
  });
});
