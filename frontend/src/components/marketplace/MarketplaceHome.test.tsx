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
import MarketplaceHome from "./MarketplaceHome";
import { Template, TemplateList, Category } from "../../api/marketplace";
import { useApiCall } from "../../hooks/useApiCall";
import { useAuth } from "../../hooks/useAuth";

// Mock the API functions
jest.mock("../../api/marketplace", () => ({
  fetchTemplates: jest.fn(),
  fetchCategories: jest.fn(),
}));

// Mock the useApiCall hook
jest.mock("../../hooks/useApiCall", () => ({
  useApiCall: jest.fn(),
}));

// Mock the useAuth hook
jest.mock("../../hooks/useAuth", () => ({
  useAuth: jest.fn(),
}));

// Mock child components
jest.mock("./TemplateCard", () => {
  return function MockTemplateCard({ template, onView, onDownload }: any) {
    return (
      <div data-testid={`template-card-${template.id}`}>
        <h3>{template.name}</h3>
        <button onClick={() => onView(template)}>View</button>
        {onDownload && (
          <button onClick={() => onDownload(template)}>Download</button>
        )}
      </div>
    );
  };
});

jest.mock("./TemplateSearch", () => {
  return function MockTemplateSearch({ onSearch }: any) {
    return (
      <div data-testid="template-search">
        <button onClick={() => onSearch({ query: "test" })}>Search</button>
      </div>
    );
  };
});

jest.mock("./TemplateDetail", () => {
  return function MockTemplateDetail({ template, open, onClose }: any) {
    return open ? (
      <div data-testid="template-detail">
        <h2>{template.name}</h2>
        <button onClick={onClose}>Close</button>
      </div>
    ) : null;
  };
});

jest.mock("./TemplateSubmissionForm", () => {
  return function MockTemplateSubmissionForm({
    open,
    onClose,
    onSubmitted,
  }: any) {
    return open ? (
      <div data-testid="template-submission-form">
        <h2>Submit Template</h2>
        <button onClick={onClose}>Cancel</button>
        <button onClick={onSubmitted}>Submit</button>
      </div>
    ) : null;
  };
});

const theme = createTheme();

const mockTemplate: Template = {
  id: 1,
  name: "Test Template",
  description: "A test template",
  author_id: 1,
  category_id: 1,
  version: "1.0.0",
  docker_compose_yaml: "version: '3.8'\nservices:\n  app:\n    image: nginx",
  tags: ["test"],
  status: "approved",
  downloads: 10,
  rating_avg: 4.5,
  rating_count: 2,
  created_at: "2023-01-01T00:00:00Z",
  updated_at: "2023-01-01T00:00:00Z",
};

const mockTemplateList: TemplateList = {
  templates: [mockTemplate],
  total: 1,
  page: 1,
  per_page: 20,
  pages: 1,
};

const mockCategory: Category = {
  id: 1,
  name: "Web Servers",
  description: "Web server templates",
  icon: "web",
  sort_order: 1,
  is_active: true,
  created_at: "2023-01-01T00:00:00Z",
  updated_at: "2023-01-01T00:00:00Z",
  template_count: 5,
};

const renderMarketplaceHome = () => {
  return render(
    <ThemeProvider theme={theme}>
      <MarketplaceHome />
    </ThemeProvider>
  );
};

describe("MarketplaceHome", () => {
  const mockUseApiCall = useApiCall as jest.MockedFunction<typeof useApiCall>;
  const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;

  beforeEach(() => {
    jest.clearAllMocks();

    // Default mock implementations
    mockUseAuth.mockReturnValue({
      user: { id: 1, username: "testuser", role: "user" },
    });

    // Mock useApiCall for templates
    mockUseApiCall
      .mockReturnValueOnce({
        data: mockTemplateList,
        loading: false,
        error: null,
        execute: jest.fn(),
      })
      .mockReturnValueOnce({
        data: [mockCategory],
        loading: false,
        error: null,
        execute: jest.fn(),
      });
  });

  describe("Rendering", () => {
    test("renders marketplace header", () => {
      renderMarketplaceHome();

      expect(screen.getByText("Template Marketplace")).toBeInTheDocument();
      expect(
        screen.getByText(/Discover and share Docker Compose templates/)
      ).toBeInTheDocument();
    });

    test("renders submit template button for authenticated users", () => {
      renderMarketplaceHome();

      expect(
        screen.getByRole("button", { name: /submit template/i })
      ).toBeInTheDocument();
    });

    test("does not render submit template button for unauthenticated users", () => {
      mockUseAuth.mockReturnValue({ user: null });

      // Reset useApiCall mocks for this test
      mockUseApiCall
        .mockReturnValueOnce({
          data: mockTemplateList,
          loading: false,
          error: null,
          execute: jest.fn(),
        })
        .mockReturnValueOnce({
          data: [mockCategory],
          loading: false,
          error: null,
          execute: jest.fn(),
        });

      renderMarketplaceHome();

      expect(
        screen.queryByRole("button", { name: /submit template/i })
      ).not.toBeInTheDocument();
    });

    test("renders template search component", () => {
      renderMarketplaceHome();

      expect(screen.getByTestId("template-search")).toBeInTheDocument();
    });

    test("renders view mode toggle", () => {
      renderMarketplaceHome();

      expect(
        screen.getByRole("button", { name: /grid view/i })
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /list view/i })
      ).toBeInTheDocument();
    });

    test("renders template cards", () => {
      renderMarketplaceHome();

      expect(screen.getByTestId("template-card-1")).toBeInTheDocument();
      expect(screen.getByText("Test Template")).toBeInTheDocument();
    });

    test("renders results count", () => {
      renderMarketplaceHome();

      expect(screen.getByText(/Showing 1 of 1 templates/)).toBeInTheDocument();
    });

    test("renders pagination when multiple pages", () => {
      const multiPageTemplateList = {
        ...mockTemplateList,
        total: 50,
        pages: 3,
      };

      mockUseApiCall
        .mockReturnValueOnce({
          data: multiPageTemplateList,
          loading: false,
          error: null,
          execute: jest.fn(),
        })
        .mockReturnValueOnce({
          data: [mockCategory],
          loading: false,
          error: null,
          execute: jest.fn(),
        });

      renderMarketplaceHome();

      expect(
        screen.getByRole("navigation", { name: /pagination/i })
      ).toBeInTheDocument();
    });
  });

  describe("Loading states", () => {
    test("shows loading state when categories are loading", () => {
      mockUseApiCall
        .mockReturnValueOnce({
          data: null,
          loading: false,
          error: null,
          execute: jest.fn(),
        })
        .mockReturnValueOnce({
          data: null,
          loading: true,
          error: null,
          execute: jest.fn(),
        });

      renderMarketplaceHome();

      expect(screen.getByText(/Loading marketplace.../)).toBeInTheDocument();
    });

    test("shows skeleton loading for templates", () => {
      mockUseApiCall
        .mockReturnValueOnce({
          data: null,
          loading: true,
          error: null,
          execute: jest.fn(),
        })
        .mockReturnValueOnce({
          data: [mockCategory],
          loading: false,
          error: null,
          execute: jest.fn(),
        });

      renderMarketplaceHome();

      // Should show skeleton loading (mocked as "Loading templates...")
      expect(screen.getByText(/Loading templates.../)).toBeInTheDocument();
    });
  });

  describe("Error states", () => {
    test("shows error when categories fail to load", () => {
      const error = new Error("Failed to load categories");

      mockUseApiCall
        .mockReturnValueOnce({
          data: null,
          loading: false,
          error: null,
          execute: jest.fn(),
        })
        .mockReturnValueOnce({
          data: null,
          loading: false,
          error,
          execute: jest.fn(),
        });

      renderMarketplaceHome();

      expect(
        screen.getByText(/Failed to load marketplace/)
      ).toBeInTheDocument();
    });

    test("shows error when templates fail to load", () => {
      const error = new Error("Failed to load templates");

      mockUseApiCall
        .mockReturnValueOnce({
          data: null,
          loading: false,
          error,
          execute: jest.fn(),
        })
        .mockReturnValueOnce({
          data: [mockCategory],
          loading: false,
          error: null,
          execute: jest.fn(),
        });

      renderMarketplaceHome();

      expect(screen.getByText(/Failed to load templates/)).toBeInTheDocument();
    });
  });

  describe("Empty states", () => {
    test("shows no templates message when no results", () => {
      const emptyTemplateList = {
        ...mockTemplateList,
        templates: [],
        total: 0,
      };

      mockUseApiCall
        .mockReturnValueOnce({
          data: emptyTemplateList,
          loading: false,
          error: null,
          execute: jest.fn(),
        })
        .mockReturnValueOnce({
          data: [mockCategory],
          loading: false,
          error: null,
          execute: jest.fn(),
        });

      renderMarketplaceHome();

      expect(
        screen.getByText(/No templates found matching your criteria/)
      ).toBeInTheDocument();
    });
  });

  describe("Interactions", () => {
    test("opens template detail when template is viewed", async () => {
      renderMarketplaceHome();

      fireEvent.click(screen.getByText("View"));

      await waitFor(() => {
        expect(screen.getByTestId("template-detail")).toBeInTheDocument();
      });
    });

    test("closes template detail when close is clicked", async () => {
      renderMarketplaceHome();

      fireEvent.click(screen.getByText("View"));

      await waitFor(() => {
        expect(screen.getByTestId("template-detail")).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText("Close"));

      await waitFor(() => {
        expect(screen.queryByTestId("template-detail")).not.toBeInTheDocument();
      });
    });

    test("opens submission form when submit button is clicked", async () => {
      renderMarketplaceHome();

      fireEvent.click(screen.getByRole("button", { name: /submit template/i }));

      await waitFor(() => {
        expect(
          screen.getByTestId("template-submission-form")
        ).toBeInTheDocument();
      });
    });

    test("closes submission form and refreshes templates when submitted", async () => {
      const mockExecute = jest.fn();

      mockUseApiCall
        .mockReturnValueOnce({
          data: mockTemplateList,
          loading: false,
          error: null,
          execute: mockExecute,
        })
        .mockReturnValueOnce({
          data: [mockCategory],
          loading: false,
          error: null,
          execute: jest.fn(),
        });

      renderMarketplaceHome();

      const submitButtons = screen.getAllByRole("button", {
        name: /submit template/i,
      });
      fireEvent.click(submitButtons[0]);

      await waitFor(() => {
        expect(
          screen.getByTestId("template-submission-form")
        ).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText("Submit"));

      await waitFor(() => {
        expect(
          screen.queryByTestId("template-submission-form")
        ).not.toBeInTheDocument();
        expect(mockExecute).toHaveBeenCalled();
      });
    });

    test("handles template download", () => {
      // Mock URL.createObjectURL and related DOM methods
      global.URL.createObjectURL = jest.fn(() => "mock-url");
      global.URL.revokeObjectURL = jest.fn();

      const mockLink = {
        href: "",
        download: "",
        click: jest.fn(),
      };

      jest.spyOn(document, "createElement").mockReturnValue(mockLink as any);
      jest
        .spyOn(document.body, "appendChild")
        .mockImplementation(() => mockLink as any);
      jest
        .spyOn(document.body, "removeChild")
        .mockImplementation(() => mockLink as any);

      renderMarketplaceHome();

      fireEvent.click(screen.getByText("Download"));

      expect(global.URL.createObjectURL).toHaveBeenCalled();
      expect(mockLink.click).toHaveBeenCalled();
      expect(global.URL.revokeObjectURL).toHaveBeenCalled();
    });
  });
});
