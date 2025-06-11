import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { ThemeProvider } from "@mui/material/styles";
import ContainerHealthScoreVisualization from "../ContainerHealthScoreVisualization";
import { HealthScore } from "../../types/enhancedMetrics";
import theme from "../../theme";

const renderWithTheme = (component: React.ReactElement) => {
  return render(<ThemeProvider theme={theme}>{component}</ThemeProvider>);
};

const mockHealthScore: HealthScore = {
  overall_health_score: 85,
  health_status: "good",
  component_scores: {
    cpu_health: 90,
    memory_health: 80,
    network_health: 85,
    disk_health: 85,
  },
  recommendations: [
    "Consider optimizing memory usage",
    "Monitor CPU spikes during peak hours",
    "Review disk I/O patterns",
  ],
  data_points_analyzed: 100,
  analysis_period_hours: 24,
};

const mockExcellentHealthScore: HealthScore = {
  overall_health_score: 95,
  health_status: "excellent",
  component_scores: {
    cpu_health: 95,
    memory_health: 95,
    network_health: 95,
    disk_health: 95,
  },
  recommendations: ["System is performing optimally"],
  data_points_analyzed: 150,
  analysis_period_hours: 24,
};

const mockCriticalHealthScore: HealthScore = {
  overall_health_score: 25,
  health_status: "critical",
  component_scores: {
    cpu_health: 20,
    memory_health: 30,
    network_health: 25,
    disk_health: 25,
  },
  recommendations: [
    "Immediate attention required for CPU usage",
    "Memory usage is critically high",
    "Consider scaling resources",
  ],
  data_points_analyzed: 50,
  analysis_period_hours: 1,
};

describe("ContainerHealthScoreVisualization", () => {
  it("renders loading state correctly", () => {
    renderWithTheme(
      <ContainerHealthScoreVisualization healthScore={null} loading={true} />
    );

    expect(screen.getByText("Loading health score...")).toBeInTheDocument();
  });

  it("renders error state correctly", () => {
    const errorMessage = "Failed to load health score";
    renderWithTheme(
      <ContainerHealthScoreVisualization
        healthScore={null}
        error={errorMessage}
      />
    );

    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });

  it("renders no data state correctly", () => {
    renderWithTheme(<ContainerHealthScoreVisualization healthScore={null} />);

    expect(
      screen.getByText("No health score data available")
    ).toBeInTheDocument();
  });

  it("renders health score with good status", async () => {
    renderWithTheme(
      <ContainerHealthScoreVisualization healthScore={mockHealthScore} />
    );

    await waitFor(() => {
      expect(screen.getByText("Container Health Score")).toBeInTheDocument();
      const healthScores = screen.getAllByText("85");
      expect(healthScores.length).toBeGreaterThan(0);
      expect(screen.getByText("Good")).toBeInTheDocument();
      expect(screen.getByText("Based on 100 data points")).toBeInTheDocument();
      expect(screen.getByText("Analysis period: 24h")).toBeInTheDocument();
    });
  });

  it("renders excellent health status correctly", async () => {
    renderWithTheme(
      <ContainerHealthScoreVisualization
        healthScore={mockExcellentHealthScore}
      />
    );

    await waitFor(() => {
      const healthScores = screen.getAllByText("95");
      expect(healthScores.length).toBeGreaterThan(0);
      expect(screen.getByText("Excellent")).toBeInTheDocument();
    });
  });

  it("renders critical health status correctly", async () => {
    renderWithTheme(
      <ContainerHealthScoreVisualization
        healthScore={mockCriticalHealthScore}
      />
    );

    await waitFor(() => {
      const healthScores = screen.getAllByText("25");
      expect(healthScores.length).toBeGreaterThan(0);
      expect(screen.getByText("Critical")).toBeInTheDocument();
    });
  });

  it("displays component health breakdown", async () => {
    renderWithTheme(
      <ContainerHealthScoreVisualization
        healthScore={mockHealthScore}
        showComponentBreakdown={true}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("Component Health")).toBeInTheDocument();
      expect(screen.getByText("CPU HEALTH")).toBeInTheDocument();
      expect(screen.getByText("MEMORY HEALTH")).toBeInTheDocument();
      expect(screen.getByText("NETWORK HEALTH")).toBeInTheDocument();
      expect(screen.getByText("DISK HEALTH")).toBeInTheDocument();
      expect(screen.getByText("90")).toBeInTheDocument(); // CPU health score
      expect(screen.getByText("80")).toBeInTheDocument(); // Memory health score
    });
  });

  it("displays recommendations when enabled", async () => {
    renderWithTheme(
      <ContainerHealthScoreVisualization
        healthScore={mockHealthScore}
        showRecommendations={true}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("Recommendations")).toBeInTheDocument();
      expect(
        screen.getByText("Consider optimizing memory usage")
      ).toBeInTheDocument();
      expect(
        screen.getByText("Monitor CPU spikes during peak hours")
      ).toBeInTheDocument();
      expect(screen.getByText("Review disk I/O patterns")).toBeInTheDocument();
    });
  });

  it("hides component breakdown when disabled", () => {
    renderWithTheme(
      <ContainerHealthScoreVisualization
        healthScore={mockHealthScore}
        showComponentBreakdown={false}
      />
    );

    expect(screen.queryByText("Component Health")).not.toBeInTheDocument();
  });

  it("hides recommendations when disabled", () => {
    renderWithTheme(
      <ContainerHealthScoreVisualization
        healthScore={mockHealthScore}
        showRecommendations={false}
      />
    );

    expect(screen.queryByText("Recommendations")).not.toBeInTheDocument();
  });

  it("renders in compact mode correctly", async () => {
    renderWithTheme(
      <ContainerHealthScoreVisualization
        healthScore={mockHealthScore}
        compact={true}
        showRecommendations={true}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("Container Health Score")).toBeInTheDocument();
      const healthScores = screen.getAllByText("85");
      expect(healthScores.length).toBeGreaterThan(0);

      // In compact mode, only first 2 recommendations should be shown
      expect(
        screen.getByText("Consider optimizing memory usage")
      ).toBeInTheDocument();
      expect(
        screen.getByText("Monitor CPU spikes during peak hours")
      ).toBeInTheDocument();
      expect(screen.getByText("+1 more recommendations")).toBeInTheDocument();
    });
  });

  it("handles empty recommendations array", async () => {
    const healthScoreWithoutRecommendations: HealthScore = {
      ...mockHealthScore,
      recommendations: [],
    };

    renderWithTheme(
      <ContainerHealthScoreVisualization
        healthScore={healthScoreWithoutRecommendations}
        showRecommendations={true}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("Container Health Score")).toBeInTheDocument();
      expect(screen.queryByText("Recommendations")).not.toBeInTheDocument();
    });
  });

  it("displays correct health status colors and icons", async () => {
    const { rerender } = renderWithTheme(
      <ContainerHealthScoreVisualization
        healthScore={mockExcellentHealthScore}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("Excellent")).toBeInTheDocument();
    });

    rerender(
      <ThemeProvider theme={theme}>
        <ContainerHealthScoreVisualization
          healthScore={mockCriticalHealthScore}
        />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(screen.getByText("Critical")).toBeInTheDocument();
    });
  });

  it("handles different analysis periods correctly", async () => {
    const shortPeriodHealthScore: HealthScore = {
      ...mockHealthScore,
      analysis_period_hours: 1,
      data_points_analyzed: 20,
    };

    renderWithTheme(
      <ContainerHealthScoreVisualization healthScore={shortPeriodHealthScore} />
    );

    await waitFor(() => {
      expect(screen.getByText("Based on 20 data points")).toBeInTheDocument();
      expect(screen.getByText("Analysis period: 1h")).toBeInTheDocument();
    });
  });
});
