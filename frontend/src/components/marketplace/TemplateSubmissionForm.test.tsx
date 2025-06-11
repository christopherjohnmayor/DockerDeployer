import React from "react";
import {
  render,
  screen,
  fireEvent,
  waitFor,
  act,
} from "@testing-library/react";
import { ThemeProvider } from "@mui/material/styles";
import { createTheme } from "@mui/material/styles";
import TemplateSubmissionForm from "./TemplateSubmissionForm";
import { Category } from "../../api/marketplace";
import { useApiCall } from "../../hooks/useApiCall";

// Mock the useApiCall hook
jest.mock("../../hooks/useApiCall", () => ({
  useApiCall: jest.fn(),
}));

// Mock the API functions
jest.mock("../../api/marketplace", () => ({
  createTemplate: jest.fn(),
}));

const theme = createTheme();

const mockCategories: Category[] = [
  {
    id: 1,
    name: "Web Servers",
    description: "Web server templates",
    icon: "web",
    sort_order: 1,
    is_active: true,
    created_at: "2023-01-01T00:00:00Z",
    updated_at: "2023-01-01T00:00:00Z",
    template_count: 5,
  },
  {
    id: 2,
    name: "Databases",
    description: "Database templates",
    icon: "database",
    sort_order: 2,
    is_active: true,
    created_at: "2023-01-01T00:00:00Z",
    updated_at: "2023-01-01T00:00:00Z",
    template_count: 3,
  },
];

const renderTemplateSubmissionForm = (props: any = {}) => {
  const defaultProps = {
    open: true,
    onClose: jest.fn(),
    onSubmitted: jest.fn(),
    categories: mockCategories,
    ...props,
  };

  return render(
    <ThemeProvider theme={theme}>
      <TemplateSubmissionForm {...defaultProps} />
    </ThemeProvider>
  );
};

describe("TemplateSubmissionForm", () => {
  const mockUseApiCall = useApiCall as jest.MockedFunction<typeof useApiCall>;

  beforeEach(() => {
    jest.clearAllMocks();

    // Default mock for useApiCall
    mockUseApiCall.mockReturnValue({
      loading: false,
      error: null,
      execute: jest.fn().mockResolvedValue({ id: 1, name: "Test Template" }),
    });
  });

  describe("Rendering", () => {
    test("renders dialog when open", () => {
      renderTemplateSubmissionForm();

      expect(screen.getByText("Submit New Template")).toBeInTheDocument();
    });

    test("does not render dialog when closed", () => {
      renderTemplateSubmissionForm({ open: false });

      expect(screen.queryByText("Submit New Template")).not.toBeInTheDocument();
    });

    test("renders stepper with correct steps", () => {
      renderTemplateSubmissionForm();

      expect(screen.getByText("Basic Information")).toBeInTheDocument();
      expect(screen.getByText("Docker Compose")).toBeInTheDocument();
      expect(screen.getByText("Review & Submit")).toBeInTheDocument();
    });

    test("renders first step form fields", () => {
      renderTemplateSubmissionForm();

      expect(screen.getByLabelText(/template name/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/description/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/category/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/version/i)).toBeInTheDocument();
    });

    test("renders category options", async () => {
      renderTemplateSubmissionForm();

      const categorySelect = screen.getByLabelText(/category/i);
      fireEvent.mouseDown(categorySelect);

      await waitFor(() => {
        expect(screen.getByText("Web Servers")).toBeInTheDocument();
        expect(screen.getByText("Databases")).toBeInTheDocument();
      });
    });

    test("renders navigation buttons", () => {
      renderTemplateSubmissionForm();

      expect(
        screen.getByRole("button", { name: /cancel/i })
      ).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /next/i })).toBeInTheDocument();
    });
  });

  describe("Form validation", () => {
    test("shows validation error for empty template name", async () => {
      renderTemplateSubmissionForm();

      const nextButton = screen.getByRole("button", { name: /next/i });
      fireEvent.click(nextButton);

      await waitFor(() => {
        expect(
          screen.getByText("Template name is required")
        ).toBeInTheDocument();
      });
    });

    test("shows validation error for short template name", async () => {
      renderTemplateSubmissionForm();

      const nameInput = screen.getByLabelText(/template name/i);
      fireEvent.change(nameInput, { target: { value: "ab" } });

      const nextButton = screen.getByRole("button", { name: /next/i });
      fireEvent.click(nextButton);

      await waitFor(() => {
        expect(
          screen.getByText("Template name must be at least 3 characters")
        ).toBeInTheDocument();
      });
    });

    test("shows validation error for empty description", async () => {
      renderTemplateSubmissionForm();

      const nameInput = screen.getByLabelText(/template name/i);
      fireEvent.change(nameInput, { target: { value: "Test Template" } });

      const nextButton = screen.getByRole("button", { name: /next/i });
      fireEvent.click(nextButton);

      await waitFor(() => {
        expect(screen.getByText("Description is required")).toBeInTheDocument();
      });
    });

    test("shows validation error for short description", async () => {
      renderTemplateSubmissionForm();

      const nameInput = screen.getByLabelText(/template name/i);
      fireEvent.change(nameInput, { target: { value: "Test Template" } });

      const descInput = screen.getByLabelText(/description/i);
      fireEvent.change(descInput, { target: { value: "Short" } });

      const nextButton = screen.getByRole("button", { name: /next/i });
      fireEvent.click(nextButton);

      await waitFor(() => {
        expect(
          screen.getByText("Description must be at least 10 characters")
        ).toBeInTheDocument();
      });
    });

    test("shows validation error for missing category", async () => {
      renderTemplateSubmissionForm();

      const nameInput = screen.getByLabelText(/template name/i);
      fireEvent.change(nameInput, { target: { value: "Test Template" } });

      const descInput = screen.getByLabelText(/description/i);
      fireEvent.change(descInput, {
        target: { value: "A test template description" },
      });

      const nextButton = screen.getByRole("button", { name: /next/i });
      fireEvent.click(nextButton);

      await waitFor(() => {
        expect(
          screen.getByText("Please select a category")
        ).toBeInTheDocument();
      });
    });

    test("proceeds to next step when validation passes", async () => {
      renderTemplateSubmissionForm();

      // Fill in valid data
      const nameInput = screen.getByLabelText(/template name/i);
      fireEvent.change(nameInput, { target: { value: "Test Template" } });

      const descInput = screen.getByLabelText(/description/i);
      fireEvent.change(descInput, {
        target: { value: "A test template description" },
      });

      const categorySelect = screen.getByLabelText(/category/i);
      fireEvent.mouseDown(categorySelect);

      await waitFor(() => {
        fireEvent.click(screen.getByText("Web Servers"));
      });

      const versionInput = screen.getByLabelText(/version/i);
      fireEvent.change(versionInput, { target: { value: "1.0.0" } });

      const nextButton = screen.getByRole("button", { name: /next/i });
      fireEvent.click(nextButton);

      await waitFor(() => {
        expect(screen.getByText(/Docker Compose YAML/)).toBeInTheDocument();
      });
    });
  });

  describe("Tags management", () => {
    test("adds tags when add button is clicked", async () => {
      renderTemplateSubmissionForm();

      const tagInput = screen.getByLabelText(/add tag/i);
      fireEvent.change(tagInput, { target: { value: "test-tag" } });

      const addButton = screen.getByRole("button", { name: /add/i });
      fireEvent.click(addButton);

      await waitFor(() => {
        expect(screen.getByText("test-tag")).toBeInTheDocument();
      });
    });

    test("removes tags when delete is clicked", async () => {
      renderTemplateSubmissionForm();

      // Add a tag first
      const tagInput = screen.getByLabelText(/add tag/i);
      fireEvent.change(tagInput, { target: { value: "test-tag" } });

      const addButton = screen.getByRole("button", { name: /add/i });
      fireEvent.click(addButton);

      await waitFor(() => {
        expect(screen.getByText("test-tag")).toBeInTheDocument();
      });

      // Remove the tag
      const deleteButton = screen.getByTestId("RemoveIcon");
      fireEvent.click(deleteButton);

      await waitFor(() => {
        expect(screen.queryByText("test-tag")).not.toBeInTheDocument();
      });
    });

    test("does not add duplicate tags", async () => {
      renderTemplateSubmissionForm();

      const tagInput = screen.getByLabelText(/add tag/i);
      const addButton = screen.getByRole("button", { name: /add/i });

      // Add first tag
      fireEvent.change(tagInput, { target: { value: "test-tag" } });
      fireEvent.click(addButton);

      // Try to add same tag again
      fireEvent.change(tagInput, { target: { value: "test-tag" } });
      fireEvent.click(addButton);

      await waitFor(() => {
        const tagElements = screen.getAllByText("test-tag");
        expect(tagElements).toHaveLength(1);
      });
    });
  });

  describe("Docker Compose step", () => {
    test("shows Docker Compose textarea on second step", async () => {
      renderTemplateSubmissionForm();

      // Navigate to second step
      await fillBasicInfoAndProceed();

      expect(screen.getByText(/Docker Compose YAML/)).toBeInTheDocument();
      expect(
        screen.getByRole("textbox", { name: /docker compose yaml/i })
      ).toBeInTheDocument();
    });

    test("validates Docker Compose YAML", async () => {
      renderTemplateSubmissionForm();

      await fillBasicInfoAndProceed();

      const nextButton = screen.getByRole("button", { name: /next/i });
      fireEvent.click(nextButton);

      await waitFor(() => {
        expect(
          screen.getByText("Docker Compose YAML is required")
        ).toBeInTheDocument();
      });
    });

    test("validates Docker Compose YAML length", async () => {
      renderTemplateSubmissionForm();

      await fillBasicInfoAndProceed();

      const yamlInput = screen.getByRole("textbox", {
        name: /docker compose yaml/i,
      });
      fireEvent.change(yamlInput, { target: { value: "short" } });

      const nextButton = screen.getByRole("button", { name: /next/i });
      fireEvent.click(nextButton);

      await waitFor(() => {
        expect(
          screen.getByText("Docker Compose YAML seems too short")
        ).toBeInTheDocument();
      });
    });
  });

  describe("Review step", () => {
    test("shows review information on final step", async () => {
      renderTemplateSubmissionForm();

      await fillBasicInfoAndProceed();
      await fillDockerComposeAndProceed();

      expect(screen.getByText("Review Your Template")).toBeInTheDocument();
      expect(screen.getByText("Test Template")).toBeInTheDocument();
      expect(
        screen.getByText("A test template description")
      ).toBeInTheDocument();
      expect(screen.getByText("Web Servers")).toBeInTheDocument();
    });

    test("shows submit button on final step", async () => {
      renderTemplateSubmissionForm();

      await fillBasicInfoAndProceed();
      await fillDockerComposeAndProceed();

      expect(
        screen.getByRole("button", { name: /submit template/i })
      ).toBeInTheDocument();
    });
  });

  describe("Form submission", () => {
    test("submits form with correct data", async () => {
      const mockExecute = jest.fn().mockResolvedValue({ id: 1 });
      const mockOnSubmitted = jest.fn();

      mockUseApiCall.mockReturnValue({
        loading: false,
        error: null,
        execute: mockExecute,
      });

      renderTemplateSubmissionForm({ onSubmitted: mockOnSubmitted });

      await fillBasicInfoAndProceed();
      await fillDockerComposeAndProceed();

      const submitButton = screen.getByRole("button", {
        name: /submit template/i,
      });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(mockExecute).toHaveBeenCalledWith({
          name: "Test Template",
          description: "A test template description",
          category_id: 1,
          docker_compose_yaml:
            "version: '3.8'\nservices:\n  app:\n    image: nginx",
          tags: [],
          version: "1.0.0",
        });
        expect(mockOnSubmitted).toHaveBeenCalled();
      });
    });

    test("shows loading state during submission", async () => {
      mockUseApiCall.mockReturnValue({
        loading: true,
        error: null,
        execute: jest.fn(),
      });

      renderTemplateSubmissionForm();

      await fillBasicInfoAndProceed();
      await fillDockerComposeAndProceed();

      expect(screen.getByText("Submitting...")).toBeInTheDocument();
    });

    test("shows error state on submission failure", async () => {
      const error = new Error("Submission failed");

      mockUseApiCall.mockReturnValue({
        loading: false,
        error,
        execute: jest.fn(),
      });

      renderTemplateSubmissionForm();

      await fillBasicInfoAndProceed();
      await fillDockerComposeAndProceed();

      expect(screen.getByText(/Failed to submit template/)).toBeInTheDocument();
    });
  });

  describe("Navigation", () => {
    test("goes back to previous step", async () => {
      renderTemplateSubmissionForm();

      await fillBasicInfoAndProceed();

      const backButton = screen.getByRole("button", { name: /back/i });
      fireEvent.click(backButton);

      await waitFor(() => {
        expect(screen.getByLabelText(/template name/i)).toBeInTheDocument();
      });
    });

    test("closes dialog when cancel is clicked", () => {
      const mockOnClose = jest.fn();
      renderTemplateSubmissionForm({ onClose: mockOnClose });

      const cancelButton = screen.getByRole("button", { name: /cancel/i });
      fireEvent.click(cancelButton);

      expect(mockOnClose).toHaveBeenCalled();
    });
  });

  // Helper functions
  async function fillBasicInfoAndProceed() {
    const nameInput = screen.getByLabelText(/template name/i);
    fireEvent.change(nameInput, { target: { value: "Test Template" } });

    const descInput = screen.getByLabelText(/description/i);
    fireEvent.change(descInput, {
      target: { value: "A test template description" },
    });

    // Find the category select by its role (there's only one combobox)
    const categorySelect = screen.getByRole("combobox");
    fireEvent.mouseDown(categorySelect);

    await waitFor(() => {
      fireEvent.click(screen.getByText("Web Servers"));
    });

    const versionInput = screen.getByLabelText(/version/i);
    fireEvent.change(versionInput, { target: { value: "1.0.0" } });

    const nextButton = screen.getByRole("button", { name: /next/i });
    fireEvent.click(nextButton);

    await waitFor(() => {
      expect(screen.getAllByText(/Docker Compose YAML/)[0]).toBeInTheDocument();
    });
  }

  async function fillDockerComposeAndProceed() {
    const yamlInput = screen.getByRole("textbox", {
      name: /docker compose yaml/i,
    });
    fireEvent.change(yamlInput, {
      target: { value: "version: '3.8'\nservices:\n  app:\n    image: nginx" },
    });

    const nextButton = screen.getByRole("button", { name: /next/i });
    fireEvent.click(nextButton);

    await waitFor(() => {
      expect(screen.getByText("Review Your Template")).toBeInTheDocument();
    });
  }
});
