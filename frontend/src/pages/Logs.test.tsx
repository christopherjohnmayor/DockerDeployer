import React from "react";
import { render, screen } from "@testing-library/react";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import Logs from "./Logs";

// Create a theme for testing
const theme = createTheme();

// Test wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ThemeProvider theme={theme}>
    {children}
  </ThemeProvider>
);

describe("Logs Component", () => {
  describe("Rendering", () => {
    test("renders logs page correctly", () => {
      render(
        <TestWrapper>
          <Logs />
        </TestWrapper>
      );

      expect(screen.getByText("Logs")).toBeInTheDocument();
      expect(
        screen.getByText(
          "This is a placeholder for the Logs page. Here you will be able to view and search logs for your Docker containers."
        )
      ).toBeInTheDocument();
    });

    test("has proper heading structure", () => {
      render(
        <TestWrapper>
          <Logs />
        </TestWrapper>
      );

      const heading = screen.getByRole("heading", { name: "Logs" });
      expect(heading).toBeInTheDocument();
    });

    test("displays placeholder content", () => {
      render(
        <TestWrapper>
          <Logs />
        </TestWrapper>
      );

      const placeholderText = screen.getByText(
        "This is a placeholder for the Logs page. Here you will be able to view and search logs for your Docker containers."
      );
      expect(placeholderText).toBeInTheDocument();
    });
  });

  describe("Layout and Styling", () => {
    test("renders within paper component", () => {
      const { container } = render(
        <TestWrapper>
          <Logs />
        </TestWrapper>
      );

      // Check for Material-UI Paper component class
      const paperElement = container.querySelector(".MuiPaper-root");
      expect(paperElement).toBeInTheDocument();
    });

    test("renders within box container", () => {
      const { container } = render(
        <TestWrapper>
          <Logs />
        </TestWrapper>
      );

      // Check for Material-UI Box component class
      const boxElement = container.querySelector(".MuiBox-root");
      expect(boxElement).toBeInTheDocument();
    });
  });

  describe("Accessibility", () => {
    test("has proper heading hierarchy", () => {
      render(
        <TestWrapper>
          <Logs />
        </TestWrapper>
      );

      const heading = screen.getByRole("heading", { name: "Logs" });
      expect(heading).toBeInTheDocument();
    });

    test("content is readable", () => {
      render(
        <TestWrapper>
          <Logs />
        </TestWrapper>
      );

      // Ensure all text content is present and accessible
      expect(screen.getByText("Logs")).toBeInTheDocument();
      expect(
        screen.getByText(/This is a placeholder for the Logs page/)
      ).toBeInTheDocument();
    });
  });

  describe("Content", () => {
    test("displays correct page title", () => {
      render(
        <TestWrapper>
          <Logs />
        </TestWrapper>
      );

      const title = screen.getByText("Logs");
      expect(title).toBeInTheDocument();
    });

    test("displays informative placeholder message", () => {
      render(
        <TestWrapper>
          <Logs />
        </TestWrapper>
      );

      const message = screen.getByText(
        /Here you will be able to view and search logs for your Docker containers/
      );
      expect(message).toBeInTheDocument();
    });
  });

  describe("Component Structure", () => {
    test("renders without crashing", () => {
      expect(() => {
        render(
          <TestWrapper>
            <Logs />
          </TestWrapper>
        );
      }).not.toThrow();
    });

    test("has expected DOM structure", () => {
      const { container } = render(
        <TestWrapper>
          <Logs />
        </TestWrapper>
      );

      // Should have Box > Paper > Typography elements
      const boxElement = container.querySelector(".MuiBox-root");
      const paperElement = container.querySelector(".MuiPaper-root");
      
      expect(boxElement).toBeInTheDocument();
      expect(paperElement).toBeInTheDocument();
      expect(boxElement).toContainElement(paperElement);
    });
  });
});
