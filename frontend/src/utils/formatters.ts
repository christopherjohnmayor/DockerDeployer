/**
 * Utility functions for formatting data in the metrics visualization components
 */

/**
 * Format bytes to human-readable format
 * @param bytes - Number of bytes
 * @param decimals - Number of decimal places (default: 2)
 * @returns Formatted string with appropriate unit
 */
export const formatBytes = (bytes: number, decimals: number = 2): string => {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];

  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
};

/**
 * Format percentage with specified decimal places
 * @param value - Percentage value
 * @param decimals - Number of decimal places (default: 1)
 * @returns Formatted percentage string
 */
export const formatPercentage = (value: number, decimals: number = 1): string => {
  return `${value.toFixed(decimals)}%`;
};

/**
 * Format duration in milliseconds to human-readable format
 * @param ms - Duration in milliseconds
 * @returns Formatted duration string
 */
export const formatDuration = (ms: number): string => {
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  if (ms < 3600000) return `${(ms / 60000).toFixed(1)}m`;
  if (ms < 86400000) return `${(ms / 3600000).toFixed(1)}h`;
  return `${(ms / 86400000).toFixed(1)}d`;
};

/**
 * Format timestamp to relative time (e.g., "2 minutes ago")
 * @param timestamp - ISO timestamp string or Date object
 * @returns Relative time string
 */
export const formatRelativeTime = (timestamp: string | Date): string => {
  const now = new Date();
  const time = new Date(timestamp);
  const diffMs = now.getTime() - time.getTime();

  if (diffMs < 60000) return 'Just now';
  if (diffMs < 3600000) return `${Math.floor(diffMs / 60000)} minutes ago`;
  if (diffMs < 86400000) return `${Math.floor(diffMs / 3600000)} hours ago`;
  if (diffMs < 604800000) return `${Math.floor(diffMs / 86400000)} days ago`;
  
  return time.toLocaleDateString();
};

/**
 * Format number with appropriate unit (K, M, B)
 * @param num - Number to format
 * @param decimals - Number of decimal places (default: 1)
 * @returns Formatted number string
 */
export const formatNumber = (num: number, decimals: number = 1): string => {
  if (num === 0) return '0';
  
  const k = 1000;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['', 'K', 'M', 'B', 'T'];

  const i = Math.floor(Math.log(Math.abs(num)) / Math.log(k));

  if (i === 0) return num.toString();

  return parseFloat((num / Math.pow(k, i)).toFixed(dm)) + sizes[i];
};

/**
 * Format CPU usage with color coding
 * @param cpuPercent - CPU usage percentage
 * @returns Object with formatted value and color
 */
export const formatCpuUsage = (cpuPercent: number) => {
  const formatted = formatPercentage(cpuPercent);
  let color = 'success';
  
  if (cpuPercent > 80) color = 'error';
  else if (cpuPercent > 60) color = 'warning';
  
  return { value: formatted, color };
};

/**
 * Format memory usage with color coding
 * @param memoryPercent - Memory usage percentage
 * @returns Object with formatted value and color
 */
export const formatMemoryUsage = (memoryPercent: number) => {
  const formatted = formatPercentage(memoryPercent);
  let color = 'success';
  
  if (memoryPercent > 85) color = 'error';
  else if (memoryPercent > 70) color = 'warning';
  
  return { value: formatted, color };
};

/**
 * Format network speed (bytes per second)
 * @param bytesPerSecond - Network speed in bytes per second
 * @returns Formatted network speed string
 */
export const formatNetworkSpeed = (bytesPerSecond: number): string => {
  return `${formatBytes(bytesPerSecond)}/s`;
};

/**
 * Format uptime duration
 * @param uptimeSeconds - Uptime in seconds
 * @returns Formatted uptime string
 */
export const formatUptime = (uptimeSeconds: number): string => {
  const days = Math.floor(uptimeSeconds / 86400);
  const hours = Math.floor((uptimeSeconds % 86400) / 3600);
  const minutes = Math.floor((uptimeSeconds % 3600) / 60);

  if (days > 0) return `${days}d ${hours}h ${minutes}m`;
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
};

/**
 * Format container status with color coding
 * @param status - Container status string
 * @returns Object with formatted status and color
 */
export const formatContainerStatus = (status: string) => {
  const statusLower = status.toLowerCase();
  
  let color = 'default';
  let label = status;
  
  switch (statusLower) {
    case 'running':
      color = 'success';
      break;
    case 'stopped':
    case 'exited':
      color = 'error';
      break;
    case 'paused':
      color = 'warning';
      break;
    case 'restarting':
      color = 'info';
      break;
    default:
      color = 'default';
  }
  
  return { label, color };
};

/**
 * Format health score with color and description
 * @param score - Health score (0-100)
 * @returns Object with formatted score, color, and description
 */
export const formatHealthScore = (score: number) => {
  let color = 'success';
  let description = 'Healthy';
  
  if (score < 60) {
    color = 'error';
    description = 'Critical';
  } else if (score < 80) {
    color = 'warning';
    description = 'Warning';
  }
  
  return {
    value: score.toString(),
    color,
    description,
  };
};

/**
 * Format metric trend direction
 * @param direction - Trend direction ('increasing', 'decreasing', 'stable')
 * @param strength - Trend strength ('high', 'medium', 'low')
 * @returns Object with icon, color, and description
 */
export const formatTrendDirection = (direction: string, strength: string) => {
  let color = 'info';
  let description = 'Stable';
  
  switch (direction) {
    case 'increasing':
      color = 'error';
      description = `Increasing (${strength})`;
      break;
    case 'decreasing':
      color = 'success';
      description = `Decreasing (${strength})`;
      break;
    default:
      color = 'info';
      description = `Stable (${strength})`;
  }
  
  return { color, description };
};

/**
 * Format timestamp for display
 * @param timestamp - ISO timestamp string
 * @param includeTime - Whether to include time (default: true)
 * @returns Formatted timestamp string
 */
export const formatTimestamp = (timestamp: string, includeTime: boolean = true): string => {
  const date = new Date(timestamp);
  
  if (includeTime) {
    return date.toLocaleString();
  }
  
  return date.toLocaleDateString();
};

/**
 * Format alert threshold condition
 * @param operator - Comparison operator
 * @param value - Threshold value
 * @param metricType - Type of metric
 * @returns Formatted condition string
 */
export const formatAlertCondition = (operator: string, value: number, metricType: string): string => {
  const unit = metricType.includes('percent') ? '%' : 
               metricType.includes('bytes') ? ' bytes' : '';
  
  return `${operator} ${value}${unit}`;
};
