import React from "react";
import { render, screen, act } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import Sidebar from "./Sidebar";

// Mock the useAuth hook
const mockUseAuth = jest.fn();
jest.mock("../hooks/useAuth", () => ({
  useAuth: () => mockUseAuth(),
}));

// Mock Material-UI useMediaQuery
jest.mock("@mui/material", () => ({
  ...jest.requireActual("@mui/material"),
  useMediaQuery: jest.fn(),
}));

import { useMediaQuery } from "@mui/material";
const mockedUseMediaQuery = useMediaQuery as jest.MockedFunction<
  typeof useMediaQuery
>;

// Create a theme for testing
const theme = createTheme();

// Wrapper component for tests
const TestWrapper: React.FC<{
  children: React.ReactNode;
  initialRoute?: string;
}> = ({ children, initialRoute = "/" }) => (
  <MemoryRouter initialEntries={[initialRoute]}>
    <ThemeProvider theme={theme}>{children}</ThemeProvider>
  </MemoryRouter>
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

describe("Sidebar Component", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Default to desktop view
    mockedUseMediaQuery.mockReturnValue(false);
  });

  test("renders basic navigation items for regular user", async () => {
    mockUseAuth.mockReturnValue({
      user: { username: "testuser", role: "user" },
      isAuthenticated: true,
    });

    await act(async () => {
      render(
        <TestWrapper>
          <Sidebar />
        </TestWrapper>
      );
    });

    // Check that basic navigation items are present
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByText("Containers")).toBeInTheDocument();
    expect(screen.getByText("Templates")).toBeInTheDocument();
    expect(screen.getByText("Logs")).toBeInTheDocument();

    // Check that admin-only items are NOT present
    expect(screen.queryByText("Users")).not.toBeInTheDocument();
    expect(screen.queryByText("Settings")).not.toBeInTheDocument();
  });

  test("renders admin navigation items for admin user", async () => {
    mockUseAuth.mockReturnValue({
      user: { username: "admin", role: "admin" },
      isAuthenticated: true,
    });

    await act(async () => {
      render(
        <TestWrapper>
          <Sidebar />
        </TestWrapper>
      );
    });

    // Check that all navigation items are present
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByText("Containers")).toBeInTheDocument();
    expect(screen.getByText("Templates")).toBeInTheDocument();
    expect(screen.getByText("Logs")).toBeInTheDocument();
    expect(screen.getByText("Users")).toBeInTheDocument();
    expect(screen.getByText("Settings")).toBeInTheDocument();
  });

  test("renders navigation items when user is null", async () => {
    mockUseAuth.mockReturnValue({
      user: null,
      isAuthenticated: false,
    });

    await act(async () => {
      render(
        <TestWrapper>
          <Sidebar />
        </TestWrapper>
      );
    });

    // Check that basic navigation items are present
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByText("Containers")).toBeInTheDocument();
    expect(screen.getByText("Templates")).toBeInTheDocument();
    expect(screen.getByText("Logs")).toBeInTheDocument();

    // Check that admin-only items are NOT present
    expect(screen.queryByText("Users")).not.toBeInTheDocument();
    expect(screen.queryByText("Settings")).not.toBeInTheDocument();
  });

  test("shows active state for dashboard route", async () => {
    mockUseAuth.mockReturnValue({
      user: { username: "testuser", role: "user" },
      isAuthenticated: true,
    });

    await act(async () => {
      render(
        <TestWrapper initialRoute="/">
          <Sidebar />
        </TestWrapper>
      );
    });

    const dashboardItem = screen.getByText("Dashboard").closest("a");
    expect(dashboardItem).toHaveClass("Mui-selected");
  });

  test("shows active state for containers route", async () => {
    mockUseAuth.mockReturnValue({
      user: { username: "testuser", role: "user" },
      isAuthenticated: true,
    });

    await act(async () => {
      render(
        <TestWrapper initialRoute="/containers">
          <Sidebar />
        </TestWrapper>
      );
    });

    const containersItem = screen.getByText("Containers").closest("a");
    expect(containersItem).toHaveClass("Mui-selected");
  });

  test("shows active state for templates route", async () => {
    mockUseAuth.mockReturnValue({
      user: { username: "testuser", role: "user" },
      isAuthenticated: true,
    });

    await act(async () => {
      render(
        <TestWrapper initialRoute="/templates">
          <Sidebar />
        </TestWrapper>
      );
    });

    const templatesItem = screen.getByText("Templates").closest("a");
    expect(templatesItem).toHaveClass("Mui-selected");
  });

  test("shows active state for logs route", async () => {
    mockUseAuth.mockReturnValue({
      user: { username: "testuser", role: "user" },
      isAuthenticated: true,
    });

    await act(async () => {
      render(
        <TestWrapper initialRoute="/logs">
          <Sidebar />
        </TestWrapper>
      );
    });

    const logsItem = screen.getByText("Logs").closest("a");
    expect(logsItem).toHaveClass("Mui-selected");
  });

  test("shows active state for admin routes", async () => {
    mockUseAuth.mockReturnValue({
      user: { username: "admin", role: "admin" },
      isAuthenticated: true,
    });

    await act(async () => {
      render(
        <TestWrapper initialRoute="/users">
          <Sidebar />
        </TestWrapper>
      );
    });

    const usersItem = screen.getByText("Users").closest("a");
    expect(usersItem).toHaveClass("Mui-selected");
  });

  test("handles nested routes correctly", async () => {
    mockUseAuth.mockReturnValue({
      user: { username: "testuser", role: "user" },
      isAuthenticated: true,
    });

    await act(async () => {
      render(
        <TestWrapper initialRoute="/containers/some-container-id">
          <Sidebar />
        </TestWrapper>
      );
    });

    // Should show containers as active for nested route
    const containersItem = screen.getByText("Containers").closest("a");
    expect(containersItem).toHaveClass("Mui-selected");
  });

  test("renders correct links for navigation items", async () => {
    mockUseAuth.mockReturnValue({
      user: { username: "admin", role: "admin" },
      isAuthenticated: true,
    });

    await act(async () => {
      render(
        <TestWrapper>
          <Sidebar />
        </TestWrapper>
      );
    });

    // Check that links have correct href attributes
    expect(screen.getByText("Dashboard").closest("a")).toHaveAttribute(
      "href",
      "/"
    );
    expect(screen.getByText("Containers").closest("a")).toHaveAttribute(
      "href",
      "/containers"
    );
    expect(screen.getByText("Templates").closest("a")).toHaveAttribute(
      "href",
      "/templates"
    );
    expect(screen.getByText("Logs").closest("a")).toHaveAttribute(
      "href",
      "/logs"
    );
    expect(screen.getByText("Users").closest("a")).toHaveAttribute(
      "href",
      "/users"
    );
    expect(screen.getByText("Settings").closest("a")).toHaveAttribute(
      "href",
      "/settings"
    );
  });

  test("renders with mobile layout", async () => {
    mockUseAuth.mockReturnValue({
      user: { username: "testuser", role: "user" },
      isAuthenticated: true,
    });

    // Mock mobile view
    mockedUseMediaQuery.mockReturnValue(true);

    await act(async () => {
      render(
        <TestWrapper>
          <Sidebar />
        </TestWrapper>
      );
    });

    // Should still render navigation items
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByText("Containers")).toBeInTheDocument();
  });

  test("renders icons for navigation items", async () => {
    mockUseAuth.mockReturnValue({
      user: { username: "admin", role: "admin" },
      isAuthenticated: true,
    });

    await act(async () => {
      render(
        <TestWrapper>
          <Sidebar />
        </TestWrapper>
      );
    });

    // Check that icons are rendered (they should be present as SVG elements)
    const listItems = screen.getAllByRole("link");
    expect(listItems).toHaveLength(11); // 8 basic + 3 admin items (added Marketplace, My Templates, Metrics, Alerts, and Production)

    // Each list item should contain an icon
    listItems.forEach((item) => {
      const icon = item.querySelector("svg");
      expect(icon).toBeInTheDocument();
    });
  });

  test("handles different user role values", async () => {
    mockUseAuth.mockReturnValue({
      user: { username: "testuser", role: "moderator" },
      isAuthenticated: true,
    });

    await act(async () => {
      render(
        <TestWrapper>
          <Sidebar />
        </TestWrapper>
      );
    });

    // Non-admin role should not see admin items
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.queryByText("Users")).not.toBeInTheDocument();
    expect(screen.queryByText("Settings")).not.toBeInTheDocument();
  });
});
