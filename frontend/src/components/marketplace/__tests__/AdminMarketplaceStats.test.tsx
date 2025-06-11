import React from "react";
import {
  render,
  screen,
  fireEvent,
  waitFor,
  act,
} from "@testing-library/react";
import { ThemeProvider } from "@mui/material/styles";
import AdminMarketplaceStats from "../AdminMarketplaceStats";
import { useApiCall } from "../../../hooks/useApiCall";
import theme from "../../../theme";

// Mock the useApiCall hook
jest.mock("../../../hooks/useApiCall");
const mockUseApiCall = useApiCall as jest.MockedFunction<typeof useApiCall>;

// Mock the marketplace API
jest.mock("../../../api/marketplace", () => ({
  fetchMarketplaceStats: jest.fn(),
}));

// Mock LoadingState and ErrorDisplay components
jest.mock("../../LoadingState", () => ({
  LoadingState: ({ message }: { message: string }) => (
    <div data-testid="loading-state">{message}</div>
  ),
}));

jest.mock("../../ErrorDisplay", () => ({
  __esModule: true,
  default: ({ error, onRetry, title }: any) => (
    <div data-testid="error-display">
      <div>{title}</div>
      <div>{error?.message || "Error occurred"}</div>
      <button onClick={onRetry}>Retry</button>
    </div>
  ),
}));

const renderWithTheme = (component: React.ReactElement) => {
  return render(<ThemeProvider theme={theme}>{component}</ThemeProvider>);
};

const mockMarketplaceStats = {
  total_templates: 150,
  approved_templates: 120,
  pending_templates: 20,
  rejected_templates: 10,
  total_reviews: 450,
  average_rating: 4.3,
  total_downloads: 2500,
  top_categories: [
    { category_name: "Web Servers", template_count: 45 },
    { category_name: "Databases", template_count: 30 },
    { category_name: "Monitoring", template_count: 25 },
  ],
  recent_activity: [
    {
      action: "approved",
      template_name: "NGINX Load Balancer",
      timestamp: "2023-12-11T14:30:00Z",
    },
    {
      action: "submitted",
      template_name: "Redis Cluster",
      timestamp: "2023-12-11T13:15:00Z",
    },
  ],
};

const mockApiCallReturn = {
  data: null,
  loading: false,
  error: null,
  execute: jest.fn(),
};

describe("AdminMarketplaceStats", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseApiCall.mockReturnValue(mockApiCallReturn);
  });

  describe("Component Rendering", () => {
    it("renders marketplace analytics header", () => {
      mockUseApiCall.mockReturnValue({
        ...mockApiCallReturn,
        data: mockMarketplaceStats,
      });

      renderWithTheme(<AdminMarketplaceStats />);

      expect(screen.getByText("Marketplace Analytics")).toBeInTheDocument();
      expect(
        screen.getByText(
          "Overview of template marketplace performance and user engagement"
        )
      ).toBeInTheDocument();
    });

    it("renders key metrics cards", () => {
      mockUseApiCall.mockReturnValue({
        ...mockApiCallReturn,
        data: mockMarketplaceStats,
      });

      renderWithTheme(<AdminMarketplaceStats />);

      expect(screen.getByText("150")).toBeInTheDocument();
      expect(screen.getByText("Total Templates")).toBeInTheDocument();
      expect(screen.getByText("450")).toBeInTheDocument();
      expect(screen.getByText("Total Reviews")).toBeInTheDocument();
      expect(screen.getByText("4.3")).toBeInTheDocument();
      expect(screen.getByText("Average Rating")).toBeInTheDocument();
      expect(screen.getAllByText("2.5k")).toHaveLength(2); // Appears in both h4 and h5
      expect(screen.getAllByText("Total Downloads")).toHaveLength(2); // Appears in both card and engagement section
    });

    it("renders template status overview", () => {
      mockUseApiCall.mockReturnValue({
        ...mockApiCallReturn,
        data: mockMarketplaceStats,
      });

      renderWithTheme(<AdminMarketplaceStats />);

      expect(screen.getByText("Template Status Overview")).toBeInTheDocument();
      expect(screen.getByText("Approval Rate")).toBeInTheDocument();
      expect(screen.getByText("80%")).toBeInTheDocument(); // 120/150 = 80%
      expect(screen.getAllByText("120")).toHaveLength(2); // Approved (appears in both h4 and h6)
      expect(screen.getAllByText("Approved")).toHaveLength(2); // Appears in both card and status section
      expect(screen.getAllByText("20")).toHaveLength(2); // Pending (appears in both h4 and h6)
      expect(screen.getByText("Pending")).toBeInTheDocument();
      expect(screen.getByText("10")).toBeInTheDocument(); // Rejected
      expect(screen.getByText("Rejected")).toBeInTheDocument();
    });

    it("renders user engagement section", () => {
      mockUseApiCall.mockReturnValue({
        ...mockApiCallReturn,
        data: mockMarketplaceStats,
      });

      renderWithTheme(<AdminMarketplaceStats />);

      expect(screen.getByText("User Engagement")).toBeInTheDocument();
      expect(screen.getByText("4.3")).toBeInTheDocument();
      expect(screen.getByText("Average Rating")).toBeInTheDocument();
      expect(screen.getByText("450")).toBeInTheDocument();
      expect(screen.getByText("Total Reviews")).toBeInTheDocument();
    });

    it("renders popular categories section", () => {
      mockUseApiCall.mockReturnValue({
        ...mockApiCallReturn,
        data: mockMarketplaceStats,
      });

      renderWithTheme(<AdminMarketplaceStats />);

      expect(screen.getByText("Popular Categories")).toBeInTheDocument();
      expect(screen.getByText("Web Servers")).toBeInTheDocument();
      expect(screen.getByText("45 templates")).toBeInTheDocument();
      expect(screen.getByText("Databases")).toBeInTheDocument();
      expect(screen.getByText("30 templates")).toBeInTheDocument();
      expect(screen.getByText("Monitoring")).toBeInTheDocument();
      expect(screen.getByText("25 templates")).toBeInTheDocument();
    });

    it("renders with empty categories", () => {
      const statsWithEmptyCategories = {
        ...mockMarketplaceStats,
        top_categories: [],
      };

      mockUseApiCall.mockReturnValue({
        ...mockApiCallReturn,
        data: statsWithEmptyCategories,
      });

      renderWithTheme(<AdminMarketplaceStats />);

      expect(screen.getByText("Popular Categories")).toBeInTheDocument();
      expect(
        screen.getByText("No categories data available")
      ).toBeInTheDocument();
    });
  });

  describe("Loading States", () => {
    it("shows loading state when loading and no data", () => {
      mockUseApiCall.mockReturnValue({
        ...mockApiCallReturn,
        loading: true,
        data: null,
      });

      renderWithTheme(<AdminMarketplaceStats />);

      expect(screen.getByTestId("loading-state")).toBeInTheDocument();
      expect(
        screen.getByText("Loading marketplace statistics...")
      ).toBeInTheDocument();
    });

    it("shows content when loading but data exists", () => {
      mockUseApiCall.mockReturnValue({
        ...mockApiCallReturn,
        loading: true,
        data: mockMarketplaceStats,
      });

      renderWithTheme(<AdminMarketplaceStats />);

      expect(screen.getByText("Marketplace Analytics")).toBeInTheDocument();
      expect(screen.queryByTestId("loading-state")).not.toBeInTheDocument();
    });
  });

  describe("Error Handling", () => {
    it("shows error state when error and no data", () => {
      const mockError = new Error("Failed to fetch stats");
      mockUseApiCall.mockReturnValue({
        ...mockApiCallReturn,
        error: mockError,
        data: null,
      });

      renderWithTheme(<AdminMarketplaceStats />);

      expect(screen.getByTestId("error-display")).toBeInTheDocument();
      expect(
        screen.getByText("Failed to load marketplace statistics")
      ).toBeInTheDocument();
      expect(screen.getByText("Failed to fetch stats")).toBeInTheDocument();
    });

    it("shows content when error but data exists", () => {
      const mockError = new Error("Failed to fetch stats");
      mockUseApiCall.mockReturnValue({
        ...mockApiCallReturn,
        error: mockError,
        data: mockMarketplaceStats,
      });

      renderWithTheme(<AdminMarketplaceStats />);

      expect(screen.getByText("Marketplace Analytics")).toBeInTheDocument();
      expect(screen.queryByTestId("error-display")).not.toBeInTheDocument();
    });

    it("handles retry action", async () => {
      const mockError = new Error("Network error");
      const mockExecute = jest.fn();
      mockUseApiCall.mockReturnValue({
        ...mockApiCallReturn,
        error: mockError,
        data: null,
        execute: mockExecute,
      });

      renderWithTheme(<AdminMarketplaceStats />);

      const retryButton = screen.getByText("Retry");

      await act(async () => {
        fireEvent.click(retryButton);
      });

      expect(mockExecute).toHaveBeenCalled();
    });
  });

  describe("Data Formatting", () => {
    it("formats large numbers correctly", () => {
      const statsWithLargeNumbers = {
        ...mockMarketplaceStats,
        total_templates: 1500,
        total_downloads: 25000,
        total_reviews: 4500,
      };

      mockUseApiCall.mockReturnValue({
        ...mockApiCallReturn,
        data: statsWithLargeNumbers,
      });

      renderWithTheme(<AdminMarketplaceStats />);

      expect(screen.getByText("1.5k")).toBeInTheDocument(); // total_templates
      expect(screen.getAllByText("25.0k")).toHaveLength(2); // total_downloads appears in both h4 and h5
      expect(screen.getByText("4.5k")).toBeInTheDocument(); // total_reviews
    });

    it("formats small numbers correctly", () => {
      const statsWithSmallNumbers = {
        ...mockMarketplaceStats,
        total_templates: 50,
        total_downloads: 250,
        total_reviews: 45,
      };

      mockUseApiCall.mockReturnValue({
        ...mockApiCallReturn,
        data: statsWithSmallNumbers,
      });

      renderWithTheme(<AdminMarketplaceStats />);

      expect(screen.getByText("50")).toBeInTheDocument(); // total_templates
      expect(screen.getAllByText("250")).toHaveLength(2); // total_downloads appears in both h4 and h5
      expect(screen.getAllByText("45")).toHaveLength(2); // total_reviews appears in both h5 and chip
    });

    it("formats average rating correctly", () => {
      const statsWithRating = {
        ...mockMarketplaceStats,
        average_rating: 4.567,
      };

      mockUseApiCall.mockReturnValue({
        ...mockApiCallReturn,
        data: statsWithRating,
      });

      renderWithTheme(<AdminMarketplaceStats />);

      expect(screen.getByText("4.6")).toBeInTheDocument(); // Rounded to 1 decimal
    });
  });

  describe("Percentage Calculations", () => {
    it("calculates approval rate correctly", () => {
      mockUseApiCall.mockReturnValue({
        ...mockApiCallReturn,
        data: mockMarketplaceStats,
      });

      renderWithTheme(<AdminMarketplaceStats />);

      // 120 approved / 150 total = 80%
      expect(screen.getByText("80%")).toBeInTheDocument();
    });

    it("calculates pending rate correctly", () => {
      mockUseApiCall.mockReturnValue({
        ...mockApiCallReturn,
        data: mockMarketplaceStats,
      });

      renderWithTheme(<AdminMarketplaceStats />);

      // 20 pending / 150 total = 13%
      expect(screen.getByText("13%")).toBeInTheDocument();
    });

    it("handles zero total templates", () => {
      const statsWithZeroTotal = {
        ...mockMarketplaceStats,
        total_templates: 0,
        approved_templates: 0,
        pending_templates: 0,
        rejected_templates: 0,
      };

      mockUseApiCall.mockReturnValue({
        ...mockApiCallReturn,
        data: statsWithZeroTotal,
      });

      renderWithTheme(<AdminMarketplaceStats />);

      expect(screen.getAllByText("0%")).toHaveLength(2); // Approval rate and pending rate both 0%
    });

    it("handles 100% approval rate", () => {
      const statsWithFullApproval = {
        ...mockMarketplaceStats,
        total_templates: 100,
        approved_templates: 100,
        pending_templates: 0,
        rejected_templates: 0,
      };

      mockUseApiCall.mockReturnValue({
        ...mockApiCallReturn,
        data: statsWithFullApproval,
      });

      renderWithTheme(<AdminMarketplaceStats />);

      expect(screen.getByText("100%")).toBeInTheDocument(); // Approval rate
      expect(screen.getByText("0%")).toBeInTheDocument(); // Pending rate
    });
  });

  describe("Component Lifecycle", () => {
    it("calls loadStats on mount", () => {
      const mockExecute = jest.fn();
      mockUseApiCall.mockReturnValue({
        ...mockApiCallReturn,
        execute: mockExecute,
      });

      renderWithTheme(<AdminMarketplaceStats />);

      expect(mockExecute).toHaveBeenCalledTimes(1);
    });

    it("does not render when stats is null", () => {
      mockUseApiCall.mockReturnValue({
        ...mockApiCallReturn,
        data: null,
        loading: false,
        error: null,
      });

      const { container } = renderWithTheme(<AdminMarketplaceStats />);

      expect(container.firstChild).toBeNull();
    });
  });

  describe("Edge Cases", () => {
    it("handles missing recent_activity", () => {
      const statsWithoutActivity = {
        ...mockMarketplaceStats,
        recent_activity: [],
      };

      mockUseApiCall.mockReturnValue({
        ...mockApiCallReturn,
        data: statsWithoutActivity,
      });

      renderWithTheme(<AdminMarketplaceStats />);

      expect(screen.getByText("Marketplace Analytics")).toBeInTheDocument();
    });

    it("handles undefined average_rating", () => {
      const statsWithUndefinedRating = {
        ...mockMarketplaceStats,
        average_rating: 0,
      };

      mockUseApiCall.mockReturnValue({
        ...mockApiCallReturn,
        data: statsWithUndefinedRating,
      });

      renderWithTheme(<AdminMarketplaceStats />);

      expect(screen.getByText("0.0")).toBeInTheDocument();
    });

    it("handles very large numbers", () => {
      const statsWithVeryLargeNumbers = {
        ...mockMarketplaceStats,
        total_templates: 999999,
        total_downloads: 1500000,
      };

      mockUseApiCall.mockReturnValue({
        ...mockApiCallReturn,
        data: statsWithVeryLargeNumbers,
      });

      renderWithTheme(<AdminMarketplaceStats />);

      // Use getAllByText for numbers that appear multiple times
      expect(screen.getAllByText("1000.0k")).toHaveLength(1); // total_templates
      expect(screen.getAllByText("1500.0k")).toHaveLength(2); // total_downloads appears in both h4 and h5
    });

    it("handles single category", () => {
      const statsWithSingleCategory = {
        ...mockMarketplaceStats,
        top_categories: [{ category_name: "Web Servers", template_count: 1 }],
      };

      mockUseApiCall.mockReturnValue({
        ...mockApiCallReturn,
        data: statsWithSingleCategory,
      });

      renderWithTheme(<AdminMarketplaceStats />);

      expect(screen.getByText("Web Servers")).toBeInTheDocument();
      expect(screen.getByText("1 templates")).toBeInTheDocument();
    });

    it("handles category with zero templates", () => {
      const statsWithZeroCategory = {
        ...mockMarketplaceStats,
        top_categories: [
          { category_name: "Empty Category", template_count: 0 },
        ],
      };

      mockUseApiCall.mockReturnValue({
        ...mockApiCallReturn,
        data: statsWithZeroCategory,
      });

      renderWithTheme(<AdminMarketplaceStats />);

      expect(screen.getByText("Empty Category")).toBeInTheDocument();
      expect(screen.getByText("0 templates")).toBeInTheDocument();
    });
  });

  describe("Progress Indicators", () => {
    it("renders approval rate progress bar", () => {
      mockUseApiCall.mockReturnValue({
        ...mockApiCallReturn,
        data: mockMarketplaceStats,
      });

      renderWithTheme(<AdminMarketplaceStats />);

      // Check for LinearProgress component (approval rate)
      const progressBars = document.querySelectorAll(".MuiLinearProgress-root");
      expect(progressBars.length).toBeGreaterThan(0);
    });

    it("renders pending rate progress bar", () => {
      mockUseApiCall.mockReturnValue({
        ...mockApiCallReturn,
        data: mockMarketplaceStats,
      });

      renderWithTheme(<AdminMarketplaceStats />);

      // Check for pending review display (appears in both card and progress section)
      expect(screen.getAllByText("Pending Review")).toHaveLength(2);
      expect(screen.getByText("13%")).toBeInTheDocument();
    });
  });

  describe("Icons and Visual Elements", () => {
    it("renders metric icons", () => {
      mockUseApiCall.mockReturnValue({
        ...mockApiCallReturn,
        data: mockMarketplaceStats,
      });

      renderWithTheme(<AdminMarketplaceStats />);

      // Check for Material-UI icons by their test IDs
      expect(
        document.querySelector('[data-testid="TrendingUpIcon"]')
      ).toBeInTheDocument();
      expect(
        document.querySelector('[data-testid="StarIcon"]')
      ).toBeInTheDocument();
      expect(
        document.querySelector('[data-testid="DownloadIcon"]')
      ).toBeInTheDocument();
    });

    it("renders category chips", () => {
      mockUseApiCall.mockReturnValue({
        ...mockApiCallReturn,
        data: mockMarketplaceStats,
      });

      renderWithTheme(<AdminMarketplaceStats />);

      // Check for category count chips
      const chips = document.querySelectorAll(".MuiChip-root");
      expect(chips.length).toBeGreaterThan(0);
    });
  });

  describe("Responsive Layout", () => {
    it("renders grid layout correctly", () => {
      mockUseApiCall.mockReturnValue({
        ...mockApiCallReturn,
        data: mockMarketplaceStats,
      });

      renderWithTheme(<AdminMarketplaceStats />);

      // Check for Material-UI Grid components
      const gridItems = document.querySelectorAll(".MuiGrid-item");
      expect(gridItems.length).toBeGreaterThan(0);
    });

    it("renders cards with proper structure", () => {
      mockUseApiCall.mockReturnValue({
        ...mockApiCallReturn,
        data: mockMarketplaceStats,
      });

      renderWithTheme(<AdminMarketplaceStats />);

      // Check for Material-UI Card components
      const cards = document.querySelectorAll(".MuiCard-root");
      expect(cards.length).toBeGreaterThan(0);
    });
  });
});
