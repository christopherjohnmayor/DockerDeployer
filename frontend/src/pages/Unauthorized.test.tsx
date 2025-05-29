import React from "react";
import {
  render,
  screen,
  fireEvent,
  act,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import Unauthorized from "./Unauthorized";

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
      {children}
    </ThemeProvider>
  </BrowserRouter>
);

describe("Unauthorized Component", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("Rendering", () => {
    test("renders unauthorized page correctly", () => {
      render(
        <TestWrapper>
          <Unauthorized />
        </TestWrapper>
      );

      expect(screen.getByText("Access Denied")).toBeInTheDocument();
      expect(
        screen.getByText(
          "You don't have permission to access this page. This area requires higher privileges than your current account has."
        )
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /go to dashboard/i })
      ).toBeInTheDocument();
    });

    test("displays error icon", () => {
      render(
        <TestWrapper>
          <Unauthorized />
        </TestWrapper>
      );

      // Check for error icon by looking for the SVG element
      const errorIcon = document.querySelector('[data-testid="ErrorOutlineIcon"]');
      expect(errorIcon || screen.getByTestId("ErrorOutlineIcon")).toBeInTheDocument();
    });

    test("has proper heading structure", () => {
      render(
        <TestWrapper>
          <Unauthorized />
        </TestWrapper>
      );

      const heading = screen.getByRole("heading", { name: "Access Denied" });
      expect(heading).toBeInTheDocument();
      expect(heading.tagName).toBe("H1");
    });
  });

  describe("Navigation", () => {
    test("navigates to dashboard when button is clicked", async () => {
      const user = userEvent.setup();
      render(
        <TestWrapper>
          <Unauthorized />
        </TestWrapper>
      );

      const dashboardButton = screen.getByRole("button", {
        name: /go to dashboard/i,
      });

      await act(async () => {
        await user.click(dashboardButton);
      });

      expect(mockNavigate).toHaveBeenCalledWith("/");
    });

    test("button has correct attributes", () => {
      render(
        <TestWrapper>
          <Unauthorized />
        </TestWrapper>
      );

      const dashboardButton = screen.getByRole("button", {
        name: /go to dashboard/i,
      });

      expect(dashboardButton).toHaveAttribute("type", "button");
    });
  });

  describe("Accessibility", () => {
    test("has proper ARIA structure", () => {
      render(
        <TestWrapper>
          <Unauthorized />
        </TestWrapper>
      );

      const heading = screen.getByRole("heading", { name: "Access Denied" });
      const button = screen.getByRole("button", { name: /go to dashboard/i });

      expect(heading).toBeInTheDocument();
      expect(button).toBeInTheDocument();
    });

    test("button is keyboard accessible", () => {
      render(
        <TestWrapper>
          <Unauthorized />
        </TestWrapper>
      );

      const dashboardButton = screen.getByRole("button", {
        name: /go to dashboard/i,
      });

      // Simulate keyboard interaction
      fireEvent.keyDown(dashboardButton, { key: "Enter", code: "Enter" });
      fireEvent.keyUp(dashboardButton, { key: "Enter", code: "Enter" });

      // Button should be focusable
      expect(dashboardButton).not.toHaveAttribute("disabled");
    });
  });

  describe("Layout and Styling", () => {
    test("renders within container", () => {
      render(
        <TestWrapper>
          <Unauthorized />
        </TestWrapper>
      );

      // Check that content is properly structured
      expect(screen.getByText("Access Denied")).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /go to dashboard/i })
      ).toBeInTheDocument();
    });

    test("displays content in paper component", () => {
      const { container } = render(
        <TestWrapper>
          <Unauthorized />
        </TestWrapper>
      );

      // Check for Material-UI Paper component class
      const paperElement = container.querySelector(".MuiPaper-root");
      expect(paperElement).toBeInTheDocument();
    });
  });

  describe("Content", () => {
    test("displays correct error message", () => {
      render(
        <TestWrapper>
          <Unauthorized />
        </TestWrapper>
      );

      const errorMessage = screen.getByText(
        "You don't have permission to access this page. This area requires higher privileges than your current account has."
      );
      expect(errorMessage).toBeInTheDocument();
    });

    test("displays correct page title", () => {
      render(
        <TestWrapper>
          <Unauthorized />
        </TestWrapper>
      );

      const title = screen.getByText("Access Denied");
      expect(title).toBeInTheDocument();
    });
  });
});
