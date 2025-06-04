/**
 * Tests for WebSocket utility functions
 */

import {
  getWebSocketUrl,
  getNotificationWebSocketUrl,
  getMetricsWebSocketUrl,
} from "./websocket";

// Mock window.location
const mockLocation = {
  protocol: "http:",
  host: "localhost:3000",
};

Object.defineProperty(window, "location", {
  value: mockLocation,
  writable: true,
});

// Mock environment for testing
const mockEnv = {
  DEV: true,
};

// Mock the window.import.meta.env for testing
Object.defineProperty(window, "import", {
  value: {
    meta: {
      env: mockEnv,
    },
  },
  writable: true,
});

describe("WebSocket Utilities", () => {
  beforeEach(() => {
    // Reset mocks
    mockLocation.protocol = "http:";
    mockLocation.host = "localhost:3000";
    mockEnv.DEV = true;
  });

  describe("getWebSocketUrl", () => {
    it("should generate correct WebSocket URL for development", () => {
      const url = getWebSocketUrl("/ws/test", "token123");
      expect(url).toBe("ws://localhost:3000/ws/test?token=token123");
    });

    it("should generate correct WebSocket URL for production HTTPS", () => {
      mockEnv.DEV = false;
      mockLocation.protocol = "https:";
      mockLocation.host = "example.com";

      const url = getWebSocketUrl("/ws/test", "token123");
      expect(url).toBe("wss://example.com/ws/test?token=token123");
    });

    it("should handle path without leading slash", () => {
      const url = getWebSocketUrl("ws/test", "token123");
      expect(url).toBe("ws://localhost:3000/ws/test?token=token123");
    });

    it("should work without token", () => {
      const url = getWebSocketUrl("/ws/test");
      expect(url).toBe("ws://localhost:3000/ws/test");
    });

    it("should handle existing query parameters", () => {
      const url = getWebSocketUrl("/ws/test?param=value", "token123");
      expect(url).toBe(
        "ws://localhost:3000/ws/test?param=value&token=token123"
      );
    });

    it("should encode token properly", () => {
      const url = getWebSocketUrl("/ws/test", "token with spaces");
      expect(url).toBe(
        "ws://localhost:3000/ws/test?token=token%20with%20spaces"
      );
    });
  });

  describe("getNotificationWebSocketUrl", () => {
    it("should generate correct notification WebSocket URL", () => {
      const url = getNotificationWebSocketUrl(123, "token123");
      expect(url).toBe(
        "ws://localhost:3000/ws/notifications/123?token=token123"
      );
    });
  });

  describe("getMetricsWebSocketUrl", () => {
    it("should generate correct metrics WebSocket URL", () => {
      const url = getMetricsWebSocketUrl("token123");
      expect(url).toBe(
        "ws://localhost:3000/ws/metrics/multiple?token=token123"
      );
    });
  });
});
