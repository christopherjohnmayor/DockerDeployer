import React from "react";
import {
  render,
  screen,
  fireEvent,
  waitFor,
  act,
} from "@testing-library/react";
import { ThemeProvider } from "@mui/material/styles";
import AdminTemplateQueue from "../AdminTemplateQueue";
import { useApiCall } from "../../../hooks/useApiCall";
import theme from "../../../theme";

// Mock the useApiCall hook
jest.mock("../../../hooks/useApiCall");
const mockUseApiCall = useApiCall as jest.MockedFunction<typeof useApiCall>;

// Mock the marketplace API
jest.mock("../../../api/marketplace", () => ({
  fetchPendingTemplates: jest.fn(),
  approveTemplate: jest.fn(),
}));

// Mock LoadingState and ErrorDisplay components
jest.mock("../../LoadingState", () => ({
  LoadingState: ({ message }: { message: string }) => (
    <div data-testid="loading-state">{message}</div>
  ),
}));

jest.mock("../../ErrorDisplay", () => ({
  __esModule: true,
  default: ({ error, onRetry, title, sx }: any) => (
    <div data-testid="error-display" style={sx}>
      <div>{title}</div>
      <div>{error?.message || "Error occurred"}</div>
      <button onClick={onRetry}>Retry</button>
    </div>
  ),
}));

// Mock TemplateDetail component
jest.mock("../TemplateDetail", () => ({
  __esModule: true,
  default: ({ template, open, onClose, onDownload }: any) =>
    open ? (
      <div data-testid="template-detail-modal">
        <div>Template Detail: {template.name}</div>
        <button onClick={onClose}>Close</button>
        <button onClick={() => onDownload(template)}>Download</button>
      </div>
    ) : null,
}));

// Mock URL.createObjectURL and related APIs
global.URL.createObjectURL = jest.fn(() => "mock-blob-url");
global.URL.revokeObjectURL = jest.fn();

const renderWithTheme = (component: React.ReactElement) => {
  return render(<ThemeProvider theme={theme}>{component}</ThemeProvider>);
};

const mockTemplate = {
  id: 1,
  name: "NGINX Load Balancer",
  description:
    "High-performance load balancer configuration with SSL termination",
  version: "1.0.0",
  tags: ["nginx", "load-balancer", "ssl"],
  author_id: 123,
  author_username: "john_doe",
  category_name: "Web Servers",
  docker_compose_yaml:
    "version: '3.8'\nservices:\n  nginx:\n    image: nginx:latest",
  created_at: "2023-12-11T14:30:00Z",
  updated_at: "2023-12-11T14:30:00Z",
  status: "pending",
  downloads: 0,
  rating: 0,
  review_count: 0,
};

const mockPendingTemplates = [
  mockTemplate,
  {
    ...mockTemplate,
    id: 2,
    name: "Redis Cluster",
    description: "Redis cluster setup with sentinel configuration",
    tags: ["redis", "cluster", "cache"],
    category_name: "Databases",
  },
];

const mockApiCallReturn = {
  data: null,
  loading: false,
  error: null,
  execute: jest.fn(),
};

describe("AdminTemplateQueue", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseApiCall.mockReturnValue(mockApiCallReturn);

    // Mock document methods
    document.createElement = jest.fn().mockImplementation((tagName) => {
      const element = {
        tagName: tagName.toUpperCase(),
        href: "",
        download: "",
        click: jest.fn(),
        style: {},
      };
      return element;
    });

    document.body.appendChild = jest.fn();
    document.body.removeChild = jest.fn();
  });

  describe("Component Rendering", () => {
    it("renders template approval queue header", () => {
      mockUseApiCall
        .mockReturnValueOnce({
          ...mockApiCallReturn,
          data: mockPendingTemplates,
        })
        .mockReturnValueOnce(mockApiCallReturn);

      renderWithTheme(<AdminTemplateQueue />);

      expect(screen.getByText("Template Approval Queue")).toBeInTheDocument();
      expect(
        screen.getByText("2 templates pending review")
      ).toBeInTheDocument();
    });

    it("renders empty state when no templates", () => {
      mockUseApiCall
        .mockReturnValueOnce({
          ...mockApiCallReturn,
          data: [],
        })
        .mockReturnValueOnce(mockApiCallReturn);

      renderWithTheme(<AdminTemplateQueue />);

      expect(
        screen.getByText("No templates pending approval. All caught up! 🎉")
      ).toBeInTheDocument();
    });

    it("renders templates table with data", () => {
      mockUseApiCall
        .mockReturnValueOnce({
          ...mockApiCallReturn,
          data: mockPendingTemplates,
        })
        .mockReturnValueOnce(mockApiCallReturn);

      renderWithTheme(<AdminTemplateQueue />);

      expect(screen.getByText("NGINX Load Balancer")).toBeInTheDocument();
      expect(screen.getByText("Redis Cluster")).toBeInTheDocument();
      expect(screen.getByText("john_doe")).toBeInTheDocument();
      expect(screen.getByText("Web Servers")).toBeInTheDocument();
      expect(screen.getByText("Databases")).toBeInTheDocument();
    });

    it("renders template metadata correctly", () => {
      mockUseApiCall
        .mockReturnValueOnce({
          ...mockApiCallReturn,
          data: [mockTemplate],
        })
        .mockReturnValueOnce(mockApiCallReturn);

      renderWithTheme(<AdminTemplateQueue />);

      expect(screen.getByText("v1.0.0")).toBeInTheDocument();
      expect(screen.getByText("nginx")).toBeInTheDocument();
      expect(screen.getByText("load-balancer")).toBeInTheDocument();
      expect(
        screen.getByText(
          "High-performance load balancer configuration with SSL..."
        )
      ).toBeInTheDocument();
    });

    it("renders action buttons for each template", () => {
      mockUseApiCall
        .mockReturnValueOnce({
          ...mockApiCallReturn,
          data: [mockTemplate],
        })
        .mockReturnValueOnce(mockApiCallReturn);

      renderWithTheme(<AdminTemplateQueue />);

      expect(
        screen.getByRole("button", { name: /view details/i })
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /approve/i })
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /reject/i })
      ).toBeInTheDocument();
    });
  });

  describe("Loading States", () => {
    it("shows loading state when loading and no data", () => {
      mockUseApiCall
        .mockReturnValueOnce({
          ...mockApiCallReturn,
          loading: true,
          data: null,
        })
        .mockReturnValueOnce(mockApiCallReturn);

      renderWithTheme(<AdminTemplateQueue />);

      expect(screen.getByTestId("loading-state")).toBeInTheDocument();
      expect(
        screen.getByText("Loading pending templates...")
      ).toBeInTheDocument();
    });

    it("shows content when loading but data exists", () => {
      mockUseApiCall
        .mockReturnValueOnce({
          ...mockApiCallReturn,
          loading: true,
          data: mockPendingTemplates,
        })
        .mockReturnValueOnce(mockApiCallReturn);

      renderWithTheme(<AdminTemplateQueue />);

      expect(screen.getByText("Template Approval Queue")).toBeInTheDocument();
      expect(screen.queryByTestId("loading-state")).not.toBeInTheDocument();
    });
  });

  describe("Error Handling", () => {
    it("shows error state when error and no data", () => {
      const mockError = new Error("Failed to fetch templates");
      mockUseApiCall
        .mockReturnValueOnce({
          ...mockApiCallReturn,
          error: mockError,
          data: null,
        })
        .mockReturnValueOnce(mockApiCallReturn);

      renderWithTheme(<AdminTemplateQueue />);

      expect(screen.getByTestId("error-display")).toBeInTheDocument();
      expect(
        screen.getByText("Failed to load pending templates")
      ).toBeInTheDocument();
      expect(screen.getByText("Failed to fetch templates")).toBeInTheDocument();
    });

    it("shows content when error but data exists", () => {
      const mockError = new Error("Failed to fetch templates");
      mockUseApiCall
        .mockReturnValueOnce({
          ...mockApiCallReturn,
          error: mockError,
          data: mockPendingTemplates,
        })
        .mockReturnValueOnce(mockApiCallReturn);

      renderWithTheme(<AdminTemplateQueue />);

      expect(screen.getByText("Template Approval Queue")).toBeInTheDocument();
      expect(screen.queryByTestId("error-display")).not.toBeInTheDocument();
    });

    it("shows process error when template processing fails", () => {
      const mockError = new Error("Processing failed");
      mockUseApiCall
        .mockReturnValueOnce({
          ...mockApiCallReturn,
          data: [mockTemplate],
        })
        .mockReturnValueOnce({
          ...mockApiCallReturn,
          error: mockError,
        });

      renderWithTheme(<AdminTemplateQueue />);

      expect(
        screen.getByText("Failed to process template")
      ).toBeInTheDocument();
      expect(screen.getByText("Processing failed")).toBeInTheDocument();
    });

    it("handles retry action", async () => {
      const mockError = new Error("Network error");
      const mockExecute = jest.fn();
      mockUseApiCall
        .mockReturnValueOnce({
          ...mockApiCallReturn,
          error: mockError,
          data: null,
          execute: mockExecute,
        })
        .mockReturnValueOnce(mockApiCallReturn);

      renderWithTheme(<AdminTemplateQueue />);

      const retryButton = screen.getByText("Retry");

      await act(async () => {
        fireEvent.click(retryButton);
      });

      expect(mockExecute).toHaveBeenCalled();
    });
  });

  describe("Template Selection", () => {
    it("handles individual template selection", async () => {
      mockUseApiCall
        .mockReturnValueOnce({
          ...mockApiCallReturn,
          data: mockPendingTemplates,
        })
        .mockReturnValueOnce(mockApiCallReturn);

      renderWithTheme(<AdminTemplateQueue />);

      const checkboxes = screen.getAllByRole("checkbox");
      const templateCheckbox = checkboxes[1]; // First template checkbox (index 0 is select all)

      await act(async () => {
        fireEvent.click(templateCheckbox);
      });

      expect(templateCheckbox).toBeChecked();
    });

    it("handles select all functionality", async () => {
      mockUseApiCall
        .mockReturnValueOnce({
          ...mockApiCallReturn,
          data: mockPendingTemplates,
        })
        .mockReturnValueOnce(mockApiCallReturn);

      renderWithTheme(<AdminTemplateQueue />);

      const selectAllCheckbox = screen.getAllByRole("checkbox")[0];

      await act(async () => {
        fireEvent.click(selectAllCheckbox);
      });

      expect(selectAllCheckbox).toBeChecked();
    });

    it("shows bulk approve button when templates selected", async () => {
      mockUseApiCall
        .mockReturnValueOnce({
          ...mockApiCallReturn,
          data: mockPendingTemplates,
        })
        .mockReturnValueOnce(mockApiCallReturn);

      renderWithTheme(<AdminTemplateQueue />);

      const templateCheckbox = screen.getAllByRole("checkbox")[1];

      await act(async () => {
        fireEvent.click(templateCheckbox);
      });

      await waitFor(
        () => {
          expect(screen.getByText("Approve Selected (1)")).toBeInTheDocument();
        },
        { timeout: 20000 }
      );
    });

    it("deselects template when clicked again", async () => {
      mockUseApiCall
        .mockReturnValueOnce({
          ...mockApiCallReturn,
          data: mockPendingTemplates,
        })
        .mockReturnValueOnce(mockApiCallReturn);

      renderWithTheme(<AdminTemplateQueue />);

      const templateCheckbox = screen.getAllByRole("checkbox")[1];

      // Select
      await act(async () => {
        fireEvent.click(templateCheckbox);
      });

      expect(templateCheckbox).toBeChecked();

      // Deselect
      await act(async () => {
        fireEvent.click(templateCheckbox);
      });

      expect(templateCheckbox).not.toBeChecked();
    });
  });

  describe("Template Actions", () => {
    it("opens template detail modal when view button clicked", async () => {
      mockUseApiCall
        .mockReturnValueOnce({
          ...mockApiCallReturn,
          data: [mockTemplate],
        })
        .mockReturnValueOnce(mockApiCallReturn);

      renderWithTheme(<AdminTemplateQueue />);

      const viewButton = screen.getByRole("button", { name: /view details/i });

      await act(async () => {
        fireEvent.click(viewButton);
      });

      await waitFor(
        () => {
          expect(
            screen.getByTestId("template-detail-modal")
          ).toBeInTheDocument();
          expect(
            screen.getByText("Template Detail: NGINX Load Balancer")
          ).toBeInTheDocument();
        },
        { timeout: 20000 }
      );
    });

    it("closes template detail modal", async () => {
      mockUseApiCall
        .mockReturnValueOnce({
          ...mockApiCallReturn,
          data: [mockTemplate],
        })
        .mockReturnValueOnce(mockApiCallReturn);

      renderWithTheme(<AdminTemplateQueue />);

      // Open modal
      const viewButton = screen.getByRole("button", { name: /view details/i });
      await act(async () => {
        fireEvent.click(viewButton);
      });

      // Close modal
      const closeButton = screen.getByText("Close");
      await act(async () => {
        fireEvent.click(closeButton);
      });

      await waitFor(
        () => {
          expect(
            screen.queryByTestId("template-detail-modal")
          ).not.toBeInTheDocument();
        },
        { timeout: 20000 }
      );
    });

    it("handles template download", async () => {
      mockUseApiCall
        .mockReturnValueOnce({
          ...mockApiCallReturn,
          data: [mockTemplate],
        })
        .mockReturnValueOnce(mockApiCallReturn);

      renderWithTheme(<AdminTemplateQueue />);

      // Open modal
      const viewButton = screen.getByRole("button", { name: /view details/i });
      await act(async () => {
        fireEvent.click(viewButton);
      });

      // Click download
      const downloadButton = screen.getByText("Download");
      await act(async () => {
        fireEvent.click(downloadButton);
      });

      expect(global.URL.createObjectURL).toHaveBeenCalled();
      expect(document.createElement).toHaveBeenCalledWith("a");
    });

    it("handles individual template approval", async () => {
      const mockExecute = jest.fn().mockResolvedValue(true);
      const mockLoadTemplates = jest.fn();

      mockUseApiCall
        .mockReturnValueOnce({
          ...mockApiCallReturn,
          data: [mockTemplate],
          execute: mockLoadTemplates,
        })
        .mockReturnValueOnce({
          ...mockApiCallReturn,
          execute: mockExecute,
        });

      renderWithTheme(<AdminTemplateQueue />);

      const approveButton = screen.getByRole("button", { name: /approve/i });

      await act(async () => {
        fireEvent.click(approveButton);
      });

      expect(mockExecute).toHaveBeenCalledWith(1, { approved: true });
    });

    it("opens rejection dialog when reject button clicked", async () => {
      mockUseApiCall
        .mockReturnValueOnce({
          ...mockApiCallReturn,
          data: [mockTemplate],
        })
        .mockReturnValueOnce(mockApiCallReturn);

      renderWithTheme(<AdminTemplateQueue />);

      const rejectButton = screen.getByRole("button", { name: /reject/i });

      await act(async () => {
        fireEvent.click(rejectButton);
      });

      await waitFor(
        () => {
          expect(screen.getByText("Reject Template")).toBeInTheDocument();
          expect(
            screen.getByText(
              'Please provide a reason for rejecting "NGINX Load Balancer".'
            )
          ).toBeInTheDocument();
        },
        { timeout: 20000 }
      );
    });

    it("handles template rejection with reason", async () => {
      const mockExecute = jest.fn().mockResolvedValue(true);
      const mockLoadTemplates = jest.fn();

      mockUseApiCall
        .mockReturnValueOnce({
          ...mockApiCallReturn,
          data: [mockTemplate],
          execute: mockLoadTemplates,
        })
        .mockReturnValueOnce({
          ...mockApiCallReturn,
          execute: mockExecute,
        });

      renderWithTheme(<AdminTemplateQueue />);

      // Open rejection dialog
      const rejectButton = screen.getByRole("button", { name: /reject/i });
      await act(async () => {
        fireEvent.click(rejectButton);
      });

      // Enter rejection reason
      const reasonInput = screen.getByLabelText("Rejection Reason");
      await act(async () => {
        fireEvent.change(reasonInput, {
          target: { value: "Security concerns" },
        });
      });

      // Submit rejection
      const rejectTemplateButton = screen.getByText("Reject Template");
      await act(async () => {
        fireEvent.click(rejectTemplateButton);
      });

      expect(mockExecute).toHaveBeenCalledWith(1, {
        approved: false,
        rejection_reason: "Security concerns",
      });
    });

    it("disables reject button when no reason provided", async () => {
      mockUseApiCall
        .mockReturnValueOnce({
          ...mockApiCallReturn,
          data: [mockTemplate],
        })
        .mockReturnValueOnce(mockApiCallReturn);

      renderWithTheme(<AdminTemplateQueue />);

      // Open rejection dialog
      const rejectButton = screen.getByRole("button", { name: /reject/i });
      await act(async () => {
        fireEvent.click(rejectButton);
      });

      const rejectTemplateButton = screen.getByText("Reject Template");
      expect(rejectTemplateButton).toBeDisabled();
    });

    it("cancels rejection dialog", async () => {
      mockUseApiCall
        .mockReturnValueOnce({
          ...mockApiCallReturn,
          data: [mockTemplate],
        })
        .mockReturnValueOnce(mockApiCallReturn);

      renderWithTheme(<AdminTemplateQueue />);

      // Open rejection dialog
      const rejectButton = screen.getByRole("button", { name: /reject/i });
      await act(async () => {
        fireEvent.click(rejectButton);
      });

      // Cancel
      const cancelButton = screen.getByText("Cancel");
      await act(async () => {
        fireEvent.click(cancelButton);
      });

      await waitFor(
        () => {
          expect(screen.queryByText("Reject Template")).not.toBeInTheDocument();
        },
        { timeout: 20000 }
      );
    });
  });

  describe("Bulk Operations", () => {
    it("handles bulk approval", async () => {
      const mockExecute = jest.fn().mockResolvedValue(true);
      const mockLoadTemplates = jest.fn();

      mockUseApiCall
        .mockReturnValueOnce({
          ...mockApiCallReturn,
          data: mockPendingTemplates,
          execute: mockLoadTemplates,
        })
        .mockReturnValueOnce({
          ...mockApiCallReturn,
          execute: mockExecute,
        });

      renderWithTheme(<AdminTemplateQueue />);

      // Select all templates
      const selectAllCheckbox = screen.getAllByRole("checkbox")[0];
      await act(async () => {
        fireEvent.click(selectAllCheckbox);
      });

      // Click bulk approve
      const bulkApproveButton = screen.getByText("Approve Selected (2)");
      await act(async () => {
        fireEvent.click(bulkApproveButton);
      });

      expect(mockExecute).toHaveBeenCalledTimes(2);
      expect(mockExecute).toHaveBeenCalledWith(1, { approved: true });
      expect(mockExecute).toHaveBeenCalledWith(2, { approved: true });
    });

    it("disables bulk approve when processing", async () => {
      mockUseApiCall
        .mockReturnValueOnce({
          ...mockApiCallReturn,
          data: mockPendingTemplates,
        })
        .mockReturnValueOnce({
          ...mockApiCallReturn,
          loading: true,
        });

      renderWithTheme(<AdminTemplateQueue />);

      // Select template
      const templateCheckbox = screen.getAllByRole("checkbox")[1];
      await act(async () => {
        fireEvent.click(templateCheckbox);
      });

      const bulkApproveButton = screen.getByText("Approve Selected (1)");
      expect(bulkApproveButton).toBeDisabled();
    });

    it("clears selection after bulk approval", async () => {
      const mockExecute = jest.fn().mockResolvedValue(true);
      const mockLoadTemplates = jest.fn();

      mockUseApiCall
        .mockReturnValueOnce({
          ...mockApiCallReturn,
          data: mockPendingTemplates,
          execute: mockLoadTemplates,
        })
        .mockReturnValueOnce({
          ...mockApiCallReturn,
          execute: mockExecute,
        });

      renderWithTheme(<AdminTemplateQueue />);

      // Select template
      const templateCheckbox = screen.getAllByRole("checkbox")[1];
      await act(async () => {
        fireEvent.click(templateCheckbox);
      });

      // Bulk approve
      const bulkApproveButton = screen.getByText("Approve Selected (1)");
      await act(async () => {
        fireEvent.click(bulkApproveButton);
      });

      // Selection should be cleared
      await waitFor(
        () => {
          expect(
            screen.queryByText("Approve Selected")
          ).not.toBeInTheDocument();
        },
        { timeout: 20000 }
      );
    });
  });

  describe("Date Formatting", () => {
    it("formats dates correctly", () => {
      mockUseApiCall
        .mockReturnValueOnce({
          ...mockApiCallReturn,
          data: [mockTemplate],
        })
        .mockReturnValueOnce(mockApiCallReturn);

      renderWithTheme(<AdminTemplateQueue />);

      // Check for formatted date display
      expect(screen.getByText("Dec 11, 2023, 2:30 PM")).toBeInTheDocument();
    });

    it("handles invalid dates", () => {
      const templateWithInvalidDate = {
        ...mockTemplate,
        created_at: "invalid-date",
      };

      mockUseApiCall
        .mockReturnValueOnce({
          ...mockApiCallReturn,
          data: [templateWithInvalidDate],
        })
        .mockReturnValueOnce(mockApiCallReturn);

      renderWithTheme(<AdminTemplateQueue />);

      // Should not crash with invalid date
      expect(screen.getByText("NGINX Load Balancer")).toBeInTheDocument();
    });
  });

  describe("Component Lifecycle", () => {
    it("calls loadPendingTemplates on mount", () => {
      const mockExecute = jest.fn();
      mockUseApiCall
        .mockReturnValueOnce({
          ...mockApiCallReturn,
          execute: mockExecute,
        })
        .mockReturnValueOnce(mockApiCallReturn);

      renderWithTheme(<AdminTemplateQueue />);

      expect(mockExecute).toHaveBeenCalledTimes(1);
    });

    it("refreshes templates after successful approval", async () => {
      const mockExecute = jest.fn().mockResolvedValue(true);
      const mockLoadTemplates = jest.fn();

      mockUseApiCall
        .mockReturnValueOnce({
          ...mockApiCallReturn,
          data: [mockTemplate],
          execute: mockLoadTemplates,
        })
        .mockReturnValueOnce({
          ...mockApiCallReturn,
          execute: mockExecute,
        });

      renderWithTheme(<AdminTemplateQueue />);

      const approveButton = screen.getByRole("button", { name: /approve/i });

      await act(async () => {
        fireEvent.click(approveButton);
      });

      // Should refresh templates after approval
      expect(mockLoadTemplates).toHaveBeenCalledTimes(2); // Once on mount, once after approval
    });

    it("refreshes templates after successful rejection", async () => {
      const mockExecute = jest.fn().mockResolvedValue(true);
      const mockLoadTemplates = jest.fn();

      mockUseApiCall
        .mockReturnValueOnce({
          ...mockApiCallReturn,
          data: [mockTemplate],
          execute: mockLoadTemplates,
        })
        .mockReturnValueOnce({
          ...mockApiCallReturn,
          execute: mockExecute,
        });

      renderWithTheme(<AdminTemplateQueue />);

      // Open rejection dialog
      const rejectButton = screen.getByRole("button", { name: /reject/i });
      await act(async () => {
        fireEvent.click(rejectButton);
      });

      // Enter reason and submit
      const reasonInput = screen.getByLabelText("Rejection Reason");
      await act(async () => {
        fireEvent.change(reasonInput, { target: { value: "Test reason" } });
      });

      const rejectTemplateButton = screen.getByText("Reject Template");
      await act(async () => {
        fireEvent.click(rejectTemplateButton);
      });

      // Should refresh templates after rejection
      expect(mockLoadTemplates).toHaveBeenCalledTimes(2);
    });
  });

  describe("Edge Cases", () => {
    it("handles template without author_username", () => {
      const templateWithoutUsername = {
        ...mockTemplate,
        author_username: null,
      };

      mockUseApiCall
        .mockReturnValueOnce({
          ...mockApiCallReturn,
          data: [templateWithoutUsername],
        })
        .mockReturnValueOnce(mockApiCallReturn);

      renderWithTheme(<AdminTemplateQueue />);

      expect(screen.getByText("User 123")).toBeInTheDocument();
    });

    it("handles template with empty tags", () => {
      const templateWithEmptyTags = {
        ...mockTemplate,
        tags: [],
      };

      mockUseApiCall
        .mockReturnValueOnce({
          ...mockApiCallReturn,
          data: [templateWithEmptyTags],
        })
        .mockReturnValueOnce(mockApiCallReturn);

      renderWithTheme(<AdminTemplateQueue />);

      expect(screen.getByText("NGINX Load Balancer")).toBeInTheDocument();
    });

    it("handles template with long description", () => {
      const templateWithLongDescription = {
        ...mockTemplate,
        description:
          "This is a very long description that should be truncated to show only the first 60 characters and then add ellipsis",
      };

      mockUseApiCall
        .mockReturnValueOnce({
          ...mockApiCallReturn,
          data: [templateWithLongDescription],
        })
        .mockReturnValueOnce(mockApiCallReturn);

      renderWithTheme(<AdminTemplateQueue />);

      expect(
        screen.getByText(
          "This is a very long description that should be truncated..."
        )
      ).toBeInTheDocument();
    });

    it("handles template with many tags", () => {
      const templateWithManyTags = {
        ...mockTemplate,
        tags: [
          "nginx",
          "load-balancer",
          "ssl",
          "proxy",
          "web-server",
          "docker",
        ],
      };

      mockUseApiCall
        .mockReturnValueOnce({
          ...mockApiCallReturn,
          data: [templateWithManyTags],
        })
        .mockReturnValueOnce(mockApiCallReturn);

      renderWithTheme(<AdminTemplateQueue />);

      // Should only show first 2 tags
      expect(screen.getByText("nginx")).toBeInTheDocument();
      expect(screen.getByText("load-balancer")).toBeInTheDocument();
      expect(screen.queryByText("ssl")).not.toBeInTheDocument();
    });

    it("handles failed template processing", async () => {
      const mockExecute = jest.fn().mockResolvedValue(false);

      mockUseApiCall
        .mockReturnValueOnce({
          ...mockApiCallReturn,
          data: [mockTemplate],
        })
        .mockReturnValueOnce({
          ...mockApiCallReturn,
          execute: mockExecute,
        });

      renderWithTheme(<AdminTemplateQueue />);

      const approveButton = screen.getByRole("button", { name: /approve/i });

      await act(async () => {
        fireEvent.click(approveButton);
      });

      expect(mockExecute).toHaveBeenCalledWith(1, { approved: true });
      // Should not refresh templates if processing failed
    });

    it("handles whitespace-only rejection reason", async () => {
      mockUseApiCall
        .mockReturnValueOnce({
          ...mockApiCallReturn,
          data: [mockTemplate],
        })
        .mockReturnValueOnce(mockApiCallReturn);

      renderWithTheme(<AdminTemplateQueue />);

      // Open rejection dialog
      const rejectButton = screen.getByRole("button", { name: /reject/i });
      await act(async () => {
        fireEvent.click(rejectButton);
      });

      // Enter whitespace-only reason
      const reasonInput = screen.getByLabelText("Rejection Reason");
      await act(async () => {
        fireEvent.change(reasonInput, { target: { value: "   " } });
      });

      const rejectTemplateButton = screen.getByText("Reject Template");
      expect(rejectTemplateButton).toBeDisabled();
    });

    it("handles select all with empty template list", async () => {
      mockUseApiCall
        .mockReturnValueOnce({
          ...mockApiCallReturn,
          data: [],
        })
        .mockReturnValueOnce(mockApiCallReturn);

      renderWithTheme(<AdminTemplateQueue />);

      // Should not crash when trying to select all with no templates
      expect(
        screen.getByText("No templates pending approval. All caught up! 🎉")
      ).toBeInTheDocument();
    });

    it("disables action buttons when processing", async () => {
      mockUseApiCall
        .mockReturnValueOnce({
          ...mockApiCallReturn,
          data: [mockTemplate],
        })
        .mockReturnValueOnce({
          ...mockApiCallReturn,
          loading: true,
        });

      renderWithTheme(<AdminTemplateQueue />);

      const approveButton = screen.getByRole("button", { name: /approve/i });
      const rejectButton = screen.getByRole("button", { name: /reject/i });

      expect(approveButton).toBeDisabled();
      expect(rejectButton).toBeDisabled();
    });
  });

  describe("Accessibility", () => {
    it("renders proper table structure", () => {
      mockUseApiCall
        .mockReturnValueOnce({
          ...mockApiCallReturn,
          data: mockPendingTemplates,
        })
        .mockReturnValueOnce(mockApiCallReturn);

      renderWithTheme(<AdminTemplateQueue />);

      expect(screen.getByRole("table")).toBeInTheDocument();
      expect(screen.getAllByRole("columnheader")).toHaveLength(6);
      expect(screen.getAllByRole("row")).toHaveLength(3); // Header + 2 data rows
    });

    it("renders proper checkbox labels", () => {
      mockUseApiCall
        .mockReturnValueOnce({
          ...mockApiCallReturn,
          data: [mockTemplate],
        })
        .mockReturnValueOnce(mockApiCallReturn);

      renderWithTheme(<AdminTemplateQueue />);

      const checkboxes = screen.getAllByRole("checkbox");
      expect(checkboxes).toHaveLength(2); // Select all + template checkbox
    });

    it("renders proper button tooltips", () => {
      mockUseApiCall
        .mockReturnValueOnce({
          ...mockApiCallReturn,
          data: [mockTemplate],
        })
        .mockReturnValueOnce(mockApiCallReturn);

      renderWithTheme(<AdminTemplateQueue />);

      expect(
        screen.getByRole("button", { name: /view details/i })
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /approve/i })
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /reject/i })
      ).toBeInTheDocument();
    });
  });
});
