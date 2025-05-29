import React from "react";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import ProtectedRoute from "./ProtectedRoute";
import { useAuth } from "../hooks/useAuth";

// Mock the useAuth hook
jest.mock("../hooks/useAuth");
const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;

// Mock Navigate component
jest.mock("react-router-dom", () => ({
  ...jest.requireActual("react-router-dom"),
  Navigate: ({
    to,
    state,
    replace,
  }: {
    to: string;
    state?: any;
    replace?: boolean;
  }) => (
    <div
      data-testid="navigate"
      data-to={to}
      data-state={JSON.stringify(state)}
      data-replace={replace}
    >
      Navigate to {to}
    </div>
  ),
}));

// Test wrapper component
const TestWrapper: React.FC<{
  children: React.ReactNode;
  initialEntries?: string[];
}> = ({ children, initialEntries = ["/"] }) => (
  <MemoryRouter initialEntries={initialEntries}>{children}</MemoryRouter>
);

describe("ProtectedRoute Component", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("Authentication checks", () => {
    test("renders children when user is authenticated", () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: true,
        user: { id: "1", username: "testuser", role: "user" },
        login: jest.fn(),
        logout: jest.fn(),
        refreshAuth: jest.fn(),
      });

      render(
        <TestWrapper>
          <ProtectedRoute>
            <div>Protected content</div>
          </ProtectedRoute>
        </TestWrapper>
      );

      expect(screen.getByText("Protected content")).toBeInTheDocument();
      expect(screen.queryByTestId("navigate")).not.toBeInTheDocument();
    });

    test("redirects to login when user is not authenticated", () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        user: null,
        login: jest.fn(),
        logout: jest.fn(),
        refreshAuth: jest.fn(),
      });

      render(
        <TestWrapper initialEntries={["/dashboard"]}>
          <ProtectedRoute>
            <div>Protected content</div>
          </ProtectedRoute>
        </TestWrapper>
      );

      expect(screen.queryByText("Protected content")).not.toBeInTheDocument();
      expect(screen.getByTestId("navigate")).toBeInTheDocument();
      expect(screen.getByTestId("navigate")).toHaveAttribute(
        "data-to",
        "/login"
      );
      expect(screen.getByTestId("navigate")).toHaveAttribute(
        "data-replace",
        "true"
      );
    });

    test("preserves location state when redirecting to login", () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        user: null,
        login: jest.fn(),
        logout: jest.fn(),
        refreshAuth: jest.fn(),
      });

      render(
        <TestWrapper initialEntries={["/protected-page"]}>
          <ProtectedRoute>
            <div>Protected content</div>
          </ProtectedRoute>
        </TestWrapper>
      );

      const navigateElement = screen.getByTestId("navigate");
      expect(navigateElement).toHaveAttribute("data-to", "/login");

      const stateData = JSON.parse(
        navigateElement.getAttribute("data-state") || "{}"
      );
      expect(stateData.from).toEqual(
        expect.objectContaining({
          pathname: "/protected-page",
        })
      );
    });
  });

  describe("Role-based access control", () => {
    test("renders children when user has required role", () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: true,
        user: { id: "1", username: "admin", role: "admin" },
        login: jest.fn(),
        logout: jest.fn(),
        refreshAuth: jest.fn(),
      });

      render(
        <TestWrapper>
          <ProtectedRoute requiredRole="admin">
            <div>Admin content</div>
          </ProtectedRoute>
        </TestWrapper>
      );

      expect(screen.getByText("Admin content")).toBeInTheDocument();
      expect(screen.queryByTestId("navigate")).not.toBeInTheDocument();
    });

    test("redirects to unauthorized when user lacks required role", () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: true,
        user: { id: "1", username: "user", role: "user" },
        login: jest.fn(),
        logout: jest.fn(),
        refreshAuth: jest.fn(),
      });

      render(
        <TestWrapper>
          <ProtectedRoute requiredRole="admin">
            <div>Admin content</div>
          </ProtectedRoute>
        </TestWrapper>
      );

      expect(screen.queryByText("Admin content")).not.toBeInTheDocument();
      expect(screen.getByTestId("navigate")).toBeInTheDocument();
      expect(screen.getByTestId("navigate")).toHaveAttribute(
        "data-to",
        "/unauthorized"
      );
      expect(screen.getByTestId("navigate")).toHaveAttribute(
        "data-replace",
        "true"
      );
    });

    test("handles null user when checking role", () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: true,
        user: null,
        login: jest.fn(),
        logout: jest.fn(),
        refreshAuth: jest.fn(),
      });

      render(
        <TestWrapper>
          <ProtectedRoute requiredRole="admin">
            <div>Admin content</div>
          </ProtectedRoute>
        </TestWrapper>
      );

      expect(screen.queryByText("Admin content")).not.toBeInTheDocument();
      expect(screen.getByTestId("navigate")).toBeInTheDocument();
      expect(screen.getByTestId("navigate")).toHaveAttribute(
        "data-to",
        "/unauthorized"
      );
    });

    test("allows access when no specific role is required", () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: true,
        user: { id: "1", username: "user", role: "user" },
        login: jest.fn(),
        logout: jest.fn(),
        refreshAuth: jest.fn(),
      });

      render(
        <TestWrapper>
          <ProtectedRoute>
            <div>General protected content</div>
          </ProtectedRoute>
        </TestWrapper>
      );

      expect(screen.getByText("General protected content")).toBeInTheDocument();
      expect(screen.queryByTestId("navigate")).not.toBeInTheDocument();
    });
  });

  describe("Edge cases", () => {
    test("handles undefined user role", () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: true,
        user: { id: "1", username: "user", role: undefined as any },
        login: jest.fn(),
        logout: jest.fn(),
        refreshAuth: jest.fn(),
      });

      render(
        <TestWrapper>
          <ProtectedRoute requiredRole="admin">
            <div>Admin content</div>
          </ProtectedRoute>
        </TestWrapper>
      );

      expect(screen.queryByText("Admin content")).not.toBeInTheDocument();
      expect(screen.getByTestId("navigate")).toHaveAttribute(
        "data-to",
        "/unauthorized"
      );
    });

    test("handles empty string role requirement", () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: true,
        user: { id: "1", username: "user", role: "user" },
        login: jest.fn(),
        logout: jest.fn(),
        refreshAuth: jest.fn(),
      });

      render(
        <TestWrapper>
          <ProtectedRoute requiredRole="">
            <div>Content with empty role</div>
          </ProtectedRoute>
        </TestWrapper>
      );

      // Empty string role should allow access (no specific role required)
      expect(screen.getByText("Content with empty role")).toBeInTheDocument();
      expect(screen.queryByTestId("navigate")).not.toBeInTheDocument();
    });

    test("renders multiple children correctly", () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: true,
        user: { id: "1", username: "user", role: "user" },
        login: jest.fn(),
        logout: jest.fn(),
        refreshAuth: jest.fn(),
      });

      render(
        <TestWrapper>
          <ProtectedRoute>
            <div>First child</div>
            <div>Second child</div>
            <span>Third child</span>
          </ProtectedRoute>
        </TestWrapper>
      );

      expect(screen.getByText("First child")).toBeInTheDocument();
      expect(screen.getByText("Second child")).toBeInTheDocument();
      expect(screen.getByText("Third child")).toBeInTheDocument();
    });
  });
});
