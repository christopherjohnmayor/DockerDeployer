/**
 * WebSocket utility functions for DockerDeployer
 * Handles environment-aware WebSocket URL construction
 */

/**
 * Get the appropriate WebSocket URL based on the current environment
 * @param path - WebSocket endpoint path (e.g., '/ws/notifications/123')
 * @param token - Authentication token
 * @returns Complete WebSocket URL
 */
export const getWebSocketUrl = (path: string, token?: string): string => {
  // Determine the base URL based on environment
  let baseUrl: string;

  // Check if we're in a test environment or if import.meta is not available
  const isDev =
    (typeof window !== "undefined" && (window as any).import?.meta?.env?.DEV) ||
    process.env.NODE_ENV === "development";

  if (isDev) {
    // Development environment - use Vite proxy
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    baseUrl = `${protocol}//${window.location.host}`;
  } else {
    // Production environment - use current domain
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    baseUrl = `${protocol}//${window.location.host}`;
  }

  // Ensure path starts with /
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;

  // Construct the full URL
  let url = `${baseUrl}${normalizedPath}`;

  // Add token as query parameter if provided
  if (token) {
    const separator = url.includes("?") ? "&" : "?";
    url += `${separator}token=${encodeURIComponent(token)}`;
  }

  return url;
};

/**
 * Get WebSocket URL for notifications
 * @param userId - User ID
 * @param token - Authentication token
 * @returns WebSocket URL for notifications
 */
export const getNotificationWebSocketUrl = (
  userId: number,
  token: string
): string => {
  return getWebSocketUrl(`/ws/notifications/${userId}`, token);
};

/**
 * Get WebSocket URL for metrics
 * @param token - Authentication token
 * @returns WebSocket URL for metrics
 */
export const getMetricsWebSocketUrl = (token: string): string => {
  return getWebSocketUrl("/ws/metrics/multiple", token);
};

/**
 * Get WebSocket URL for enhanced metrics with health scores and predictions
 * @param containerId - Container ID for enhanced metrics
 * @param token - Authentication token
 * @returns WebSocket URL for enhanced metrics
 */
export const getEnhancedMetricsWebSocketUrl = (
  containerId: string,
  token: string
): string => {
  return getWebSocketUrl(`/ws/metrics/enhanced/${containerId}`, token);
};
