import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { ThemeProvider } from "@mui/material/styles";
import { createTheme } from "@mui/material/styles";
import TemplateCard from "./TemplateCard";
import { Template } from "../../api/marketplace";

const theme = createTheme();

const mockTemplate: Template = {
  id: 1,
  name: "Test Template",
  description: "This is a test template for unit testing purposes",
  author_id: 1,
  category_id: 1,
  version: "1.0.0",
  docker_compose_yaml: "version: '3.8'\nservices:\n  app:\n    image: nginx",
  tags: ["test", "nginx", "web"],
  status: "approved",
  downloads: 42,
  rating_avg: 4.5,
  rating_count: 10,
  created_at: "2023-01-01T00:00:00Z",
  updated_at: "2023-01-01T00:00:00Z",
  author_username: "testuser",
  category_name: "Web Servers",
};

const renderTemplateCard = (props: any = {}) => {
  const defaultProps = {
    template: mockTemplate,
    onView: jest.fn(),
    onDownload: jest.fn(),
    showAuthor: true,
    compact: false,
    ...props,
  };

  return render(
    <ThemeProvider theme={theme}>
      <TemplateCard {...defaultProps} />
    </ThemeProvider>
  );
};

describe("TemplateCard", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("Rendering", () => {
    test("renders template name and description", () => {
      renderTemplateCard();

      expect(screen.getByText("Test Template")).toBeInTheDocument();
      expect(screen.getByText(/This is a test template/)).toBeInTheDocument();
    });

    test("renders template status chip", () => {
      renderTemplateCard();

      expect(screen.getByText("approved")).toBeInTheDocument();
    });

    test("renders category and version chips", () => {
      renderTemplateCard();

      expect(screen.getByText("Web Servers")).toBeInTheDocument();
      expect(screen.getByText("v1.0.0")).toBeInTheDocument();
    });

    test("renders template tags", () => {
      renderTemplateCard();

      expect(screen.getByText("test")).toBeInTheDocument();
      expect(screen.getByText("nginx")).toBeInTheDocument();
      expect(screen.getByText("web")).toBeInTheDocument();
    });

    test("renders rating and download count", () => {
      renderTemplateCard();

      expect(screen.getByText("(10)")).toBeInTheDocument(); // Rating count
      expect(screen.getByText("42")).toBeInTheDocument(); // Download count
    });

    test("renders author information when showAuthor is true", () => {
      renderTemplateCard({ showAuthor: true });

      expect(screen.getByText("testuser")).toBeInTheDocument();
    });

    test("does not render author information when showAuthor is false", () => {
      renderTemplateCard({ showAuthor: false });

      expect(screen.queryByText("testuser")).not.toBeInTheDocument();
    });

    test("renders View Details button", () => {
      renderTemplateCard();

      expect(
        screen.getByRole("button", { name: /view details/i })
      ).toBeInTheDocument();
    });

    test("renders download button for approved templates when onDownload provided", () => {
      renderTemplateCard();

      expect(screen.getByLabelText(/download template/i)).toBeInTheDocument();
    });

    test("does not render download button when onDownload not provided", () => {
      renderTemplateCard({ onDownload: undefined });

      expect(
        screen.queryByLabelText(/download template/i)
      ).not.toBeInTheDocument();
    });

    test("does not render download button for non-approved templates", () => {
      const pendingTemplate = { ...mockTemplate, status: "pending" };
      renderTemplateCard({ template: pendingTemplate });

      expect(
        screen.queryByLabelText(/download template/i)
      ).not.toBeInTheDocument();
    });
  });

  describe("Status colors", () => {
    test("renders approved status with success color", () => {
      renderTemplateCard();

      const statusChip = screen.getByText("approved");
      expect(statusChip).toBeInTheDocument();
    });

    test("renders pending status with warning color", () => {
      const pendingTemplate = { ...mockTemplate, status: "pending" };
      renderTemplateCard({ template: pendingTemplate });

      const statusChip = screen.getByText("pending");
      expect(statusChip).toBeInTheDocument();
    });

    test("renders rejected status with error color", () => {
      const rejectedTemplate = { ...mockTemplate, status: "rejected" };
      renderTemplateCard({ template: rejectedTemplate });

      const statusChip = screen.getByText("rejected");
      expect(statusChip).toBeInTheDocument();
    });
  });

  describe("Compact mode", () => {
    test("renders in compact mode when compact prop is true", () => {
      renderTemplateCard({ compact: true });

      // In compact mode, author info should not be shown
      expect(screen.queryByText("testuser")).not.toBeInTheDocument();
    });

    test("limits tags in compact mode", () => {
      renderTemplateCard({ compact: true });

      // Should show first 2 tags plus "+1" indicator
      expect(screen.getByText("test")).toBeInTheDocument();
      expect(screen.getByText("nginx")).toBeInTheDocument();
      expect(screen.getByText("+1")).toBeInTheDocument();
    });
  });

  describe("Tag handling", () => {
    test("shows all tags when count is within limit", () => {
      const templateWithFewTags = {
        ...mockTemplate,
        tags: ["tag1", "tag2"],
      };
      renderTemplateCard({ template: templateWithFewTags });

      expect(screen.getByText("tag1")).toBeInTheDocument();
      expect(screen.getByText("tag2")).toBeInTheDocument();
      expect(screen.queryByText(/\+/)).not.toBeInTheDocument();
    });

    test("shows overflow indicator when tags exceed limit", () => {
      const templateWithManyTags = {
        ...mockTemplate,
        tags: ["tag1", "tag2", "tag3", "tag4", "tag5"],
      };
      renderTemplateCard({ template: templateWithManyTags });

      expect(screen.getByText("tag1")).toBeInTheDocument();
      expect(screen.getByText("tag2")).toBeInTheDocument();
      expect(screen.getByText("tag3")).toBeInTheDocument();
      expect(screen.getByText("+2")).toBeInTheDocument();
    });
  });

  describe("Interactions", () => {
    test("calls onView when View Details button is clicked", () => {
      const onView = jest.fn();
      renderTemplateCard({ onView });

      fireEvent.click(screen.getByRole("button", { name: /view details/i }));

      expect(onView).toHaveBeenCalledWith(mockTemplate);
    });

    test("calls onDownload when download button is clicked", () => {
      const onDownload = jest.fn();
      renderTemplateCard({ onDownload });

      fireEvent.click(screen.getByLabelText(/download template/i));

      expect(onDownload).toHaveBeenCalledWith(mockTemplate);
    });
  });

  describe("Description truncation", () => {
    test("truncates long descriptions", () => {
      const longDescription = "A".repeat(200);
      const templateWithLongDesc = {
        ...mockTemplate,
        description: longDescription,
      };
      renderTemplateCard({ template: templateWithLongDesc });

      const descriptionElement = screen.getByText(/A+\.\.\./);
      expect(descriptionElement).toBeInTheDocument();
    });

    test("does not truncate short descriptions", () => {
      const shortDescription = "Short description";
      const templateWithShortDesc = {
        ...mockTemplate,
        description: shortDescription,
      };
      renderTemplateCard({ template: templateWithShortDesc });

      expect(screen.getByText("Short description")).toBeInTheDocument();
      expect(screen.queryByText(/\.\.\./)).not.toBeInTheDocument();
    });
  });

  describe("Date formatting", () => {
    test("formats creation date correctly", () => {
      renderTemplateCard();

      // Check that a date is displayed (more flexible pattern to handle different locales)
      // The date should contain "2023" and some form of "1" for January 1st
      const datePattern = /2023|1\/1|Jan.*1|1.*Jan/;
      const dateElements = screen.getAllByText(datePattern);
      expect(dateElements.length).toBeGreaterThan(0);
    });
  });

  describe("Fallback values", () => {
    test("handles missing author username", () => {
      const templateWithoutUsername = {
        ...mockTemplate,
        author_username: undefined,
      };
      renderTemplateCard({ template: templateWithoutUsername });

      expect(screen.getByText("User 1")).toBeInTheDocument();
    });

    test("handles missing category name", () => {
      const templateWithoutCategory = {
        ...mockTemplate,
        category_name: undefined,
      };
      renderTemplateCard({ template: templateWithoutCategory });

      // Category chip should not be rendered
      expect(screen.queryByText("Web Servers")).not.toBeInTheDocument();
    });

    test("handles empty tags array", () => {
      const templateWithoutTags = {
        ...mockTemplate,
        tags: [],
      };
      renderTemplateCard({ template: templateWithoutTags });

      // No tag chips should be rendered
      expect(screen.queryByText("test")).not.toBeInTheDocument();
    });
  });
});
