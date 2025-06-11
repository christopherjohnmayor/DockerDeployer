/**
 * Enhanced Metrics Types for Container Metrics Visualization
 * 
 * Defines TypeScript interfaces for the enhanced metrics dashboard
 * including health scores, predictions, and real-time data structures.
 */

import { MetricDataPoint } from '../components/MetricsChart';

// Base container metrics interface
export interface ContainerMetrics {
  container_id: string;
  container_name: string;
  cpu_percent: number;
  memory_percent: number;
  memory_usage: number;
  memory_limit: number;
  network_rx_bytes: number;
  network_tx_bytes: number;
  block_read_bytes: number;
  block_write_bytes: number;
  status: string;
  timestamp: string;
}

// Enhanced metrics with health scores and predictions
export interface EnhancedMetricsData {
  container_id: string;
  container_name: string;
  timestamp: string;
  current_metrics: ContainerMetrics;
  health_score: HealthScore;
  predictions?: PredictionData;
  alerts?: AlertData[];
  trends?: TrendData;
}

// Health score breakdown (0-100 scale)
export interface HealthScore {
  overall_health_score: number;
  health_status: 'excellent' | 'good' | 'warning' | 'critical';
  component_scores: {
    cpu_health: number;
    memory_health: number;
    network_health: number;
    disk_health: number;
  };
  recommendations: string[];
  data_points_analyzed: number;
  analysis_period_hours: number;
}

// Performance prediction data
export interface PredictionData {
  container_id: string;
  prediction_timestamp: string;
  prediction_horizon_hours: number;
  predictions: {
    cpu_percent: PredictionPoint[];
    memory_percent: PredictionPoint[];
    network_io: PredictionPoint[];
    disk_io: PredictionPoint[];
  };
  confidence_level: number;
  model_accuracy: number;
}

// Individual prediction point with confidence interval
export interface PredictionPoint {
  timestamp: string;
  predicted_value: number;
  confidence_lower: number;
  confidence_upper: number;
  trend: 'increasing' | 'decreasing' | 'stable';
}

// Alert data for performance issues
export interface AlertData {
  id: string;
  container_id: string;
  alert_type: 'cpu' | 'memory' | 'network' | 'disk' | 'health';
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  threshold_value: number;
  current_value: number;
  timestamp: string;
  resolved: boolean;
}

// Trend analysis data
export interface TrendData {
  container_id: string;
  analysis_period: string;
  trends: {
    cpu_trend: TrendAnalysis;
    memory_trend: TrendAnalysis;
    network_trend: TrendAnalysis;
    disk_trend: TrendAnalysis;
  };
}

// Individual trend analysis
export interface TrendAnalysis {
  direction: 'increasing' | 'decreasing' | 'stable';
  rate_of_change: number;
  confidence: number;
  anomalies_detected: number;
  seasonal_pattern: boolean;
}

// Historical metrics for time-series visualization
export interface HistoricalMetrics {
  container_id: string;
  time_range: string;
  data_points: MetricDataPoint[];
  aggregation_level: 'raw' | '1min' | '5min' | '15min' | '1hour';
  total_points: number;
}

// Multi-container comparison data
export interface ContainerComparison {
  containers: string[];
  comparison_timestamp: string;
  metrics_comparison: {
    [containerId: string]: {
      container_name: string;
      current_metrics: ContainerMetrics;
      health_score: number;
      performance_rank: number;
    };
  };
  aggregated_stats: {
    avg_cpu_percent: number;
    avg_memory_percent: number;
    total_network_io: number;
    total_disk_io: number;
  };
}

// WebSocket message types for enhanced metrics
export interface EnhancedMetricsWebSocketMessage {
  type: 'enhanced_metrics_update' | 'health_score_update' | 'prediction_update' | 'alert_triggered' | 'connection_status';
  container_id?: string;
  data?: EnhancedMetricsData | HealthScore | PredictionData | AlertData;
  timestamp: string;
  message?: string;
}

// Time range options for historical data
export type TimeRange = '1h' | '6h' | '24h' | '7d' | '30d';

// Chart configuration for different metric types
export interface ChartConfig {
  type: 'line' | 'area' | 'bar' | 'gauge' | 'heatmap';
  color: string;
  unit: string;
  formatValue?: (value: number) => string;
  thresholds?: {
    warning: number;
    critical: number;
  };
}

// Dashboard layout configuration
export interface DashboardLayout {
  containerId: string;
  layout: {
    realTimeMetrics: boolean;
    healthScore: boolean;
    predictions: boolean;
    historicalTrends: boolean;
    alerts: boolean;
  };
  refreshInterval: number;
  autoRefresh: boolean;
}

// Performance monitoring configuration
export interface PerformanceConfig {
  updateInterval: number; // milliseconds
  maxDataPoints: number;
  enablePredictions: boolean;
  enableAlerts: boolean;
  alertThresholds: {
    cpu_percent: number;
    memory_percent: number;
    network_io_mbps: number;
    disk_io_mbps: number;
  };
}

// Export utility type for component props
export type MetricsVisualizationProps = {
  containerId: string;
  containerName?: string;
  timeRange?: TimeRange;
  autoRefresh?: boolean;
  refreshInterval?: number;
  showPredictions?: boolean;
  showAlerts?: boolean;
  layout?: Partial<DashboardLayout['layout']>;
};
