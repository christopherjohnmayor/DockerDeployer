import React from "react";
import { screen, act } from "@testing-library/react";
import { renderWithProviders } from "../utils/testUtils";
import Dashboard from "./Dashboard";

// Mock the NaturalLanguageInput component
jest.mock("../components/NaturalLanguageInput", () => {
  return function MockNaturalLanguageInput() {
    return (
      <div data-testid="natural-language-input">
        Natural Language Input Component
      </div>
    );
  };
});

// Mock the SystemOverview component
jest.mock("../components/SystemOverview", () => {
  return function MockSystemOverview() {
    return <div data-testid="system-overview">System Overview Component</div>;
  };
});

// Suppress Material-UI warnings in tests
const originalError = console.error;
beforeAll(() => {
  console.error = (...args: any[]) => {
    if (
      typeof args[0] === "string" &&
      (args[0].includes("Warning: An update to") ||
        args[0].includes("Warning: validateDOMNesting"))
    ) {
      return;
    }
    originalError.call(console, ...args);
  };
});

afterAll(() => {
  console.error = originalError;
});

describe("Dashboard Component", () => {
  test("renders dashboard title", async () => {
    await act(async () => {
      renderWithProviders(<Dashboard />);
    });

    expect(screen.getByText("Dashboard")).toBeInTheDocument();
  });

  test("renders welcome message", async () => {
    await act(async () => {
      renderWithProviders(<Dashboard />);
    });

    expect(
      screen.getByText(/Welcome to the DockerDeployer dashboard!/)
    ).toBeInTheDocument();
  });

  test("renders system overview component", async () => {
    await act(async () => {
      renderWithProviders(<Dashboard />);
    });

    expect(screen.getByTestId("system-overview")).toBeInTheDocument();
    expect(screen.getByText("System Overview Component")).toBeInTheDocument();
  });

  test("renders natural language input component", async () => {
    await act(async () => {
      renderWithProviders(<Dashboard />);
    });

    expect(screen.getByTestId("natural-language-input")).toBeInTheDocument();
    expect(
      screen.getByText("Natural Language Input Component")
    ).toBeInTheDocument();
  });

  test("has proper layout structure", async () => {
    await act(async () => {
      renderWithProviders(<Dashboard />);
    });

    // Check that the main container exists
    const dashboardContainer = screen.getByText("Dashboard").closest("div");
    expect(dashboardContainer).toBeInTheDocument();

    // Check that all main components are present
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByTestId("system-overview")).toBeInTheDocument();
    expect(screen.getByTestId("natural-language-input")).toBeInTheDocument();
  });

  test("displays quick actions section", async () => {
    await act(async () => {
      renderWithProviders(<Dashboard />);
    });

    expect(screen.getByText("Quick Actions")).toBeInTheDocument();
    expect(
      screen.getByText(/Use natural language to manage your containers/)
    ).toBeInTheDocument();
  });
});
