import React from "react";
import { render, screen, act } from "@testing-library/react";
import Dashboard from "./Dashboard";

// Mock the NaturalLanguageInput component
jest.mock("../components/NaturalLanguageInput", () => {
  return function MockNaturalLanguageInput() {
    return <div data-testid="natural-language-input">Natural Language Input Component</div>;
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
      render(<Dashboard />);
    });

    expect(screen.getByText("Dashboard")).toBeInTheDocument();
  });

  test("renders welcome message", async () => {
    await act(async () => {
      render(<Dashboard />);
    });

    expect(
      screen.getByText(/Welcome to the DockerDeployer dashboard!/)
    ).toBeInTheDocument();
  });

  test("renders placeholder text", async () => {
    await act(async () => {
      render(<Dashboard />);
    });

    expect(
      screen.getByText(/This is a placeholder. More features coming soon./)
    ).toBeInTheDocument();
  });

  test("renders natural language input component", async () => {
    await act(async () => {
      render(<Dashboard />);
    });

    expect(screen.getByTestId("natural-language-input")).toBeInTheDocument();
    expect(
      screen.getByText("Natural Language Input Component")
    ).toBeInTheDocument();
  });

  test("has proper layout structure", async () => {
    await act(async () => {
      render(<Dashboard />);
    });

    // Check that the main container exists
    const dashboardContainer = screen.getByText("Dashboard").closest("div");
    expect(dashboardContainer).toBeInTheDocument();

    // Check that both the paper section and natural language input are present
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByTestId("natural-language-input")).toBeInTheDocument();
  });

  test("displays overview information", async () => {
    await act(async () => {
      render(<Dashboard />);
    });

    expect(
      screen.getByText(/overview of your containers, resource usage/)
    ).toBeInTheDocument();
  });
});
