import { renderHook, act } from "@testing-library/react";
import { useWebSocket } from "../useWebSocket";

// Mock WebSocket
class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  readyState = MockWebSocket.CONNECTING;
  url: string;
  onopen: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;

  constructor(url: string) {
    this.url = url;
    // Store instance for manual control
    MockWebSocket.instances.push(this);
  }

  static instances: MockWebSocket[] = [];

  static clearInstances() {
    MockWebSocket.instances = [];
  }

  connect() {
    this.readyState = MockWebSocket.OPEN;
    this.onopen?.(new Event("open"));
  }

  send(data: string) {
    if (this.readyState !== MockWebSocket.OPEN) {
      throw new Error("WebSocket is not open");
    }
  }

  close() {
    this.readyState = MockWebSocket.CLOSED;
    this.onclose?.(new CloseEvent("close"));
  }

  // Helper methods for testing
  simulateMessage(data: any) {
    if (this.onmessage) {
      const event = new MessageEvent("message", { data: JSON.stringify(data) });
      this.onmessage(event);
    }
  }

  simulateError() {
    if (this.onerror) {
      this.onerror(new Event("error"));
    }
  }

  simulateClose() {
    this.readyState = MockWebSocket.CLOSED;
    if (this.onclose) {
      this.onclose(new CloseEvent("close"));
    }
  }
}

// Mock global WebSocket
(global as any).WebSocket = MockWebSocket;

// Mock timers
jest.useFakeTimers();

describe("useWebSocket", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.clearAllTimers();
    MockWebSocket.clearInstances();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
    jest.useFakeTimers();
  });

  describe("Connection Management", () => {
    it("should initialize with disconnected state", () => {
      const { result } = renderHook(() => useWebSocket(null));

      expect(result.current.isConnected).toBe(false);
      expect(result.current.connectionState).toBe("disconnected");
    });

    it("should connect when URL is provided", async () => {
      const { result } = renderHook(() => useWebSocket("ws://localhost:8080"));

      expect(result.current.connectionState).toBe("connecting");

      // Manually trigger connection
      await act(async () => {
        const mockWebSocket = MockWebSocket.instances[0];
        mockWebSocket.connect();
      });

      expect(result.current.isConnected).toBe(true);
      expect(result.current.connectionState).toBe("connected");
    });

    it("should not connect when URL is null", () => {
      const { result } = renderHook(() => useWebSocket(null));

      expect(result.current.isConnected).toBe(false);
      expect(result.current.connectionState).toBe("disconnected");
    });

    it("should call onConnect callback when connected", async () => {
      const onConnect = jest.fn();
      renderHook(() => useWebSocket("ws://localhost:8080", { onConnect }));

      await act(async () => {
        const mockWebSocket = MockWebSocket.instances[0];
        mockWebSocket.connect();
      });

      expect(onConnect).toHaveBeenCalledTimes(1);
    });

    it("should call onDisconnect callback when disconnected", async () => {
      const onDisconnect = jest.fn();
      const { result } = renderHook(() =>
        useWebSocket("ws://localhost:8080", { onDisconnect })
      );

      // Connect first
      await act(async () => {
        const mockWebSocket = MockWebSocket.instances[0];
        mockWebSocket.connect();
      });

      // Disconnect
      act(() => {
        result.current.disconnect();
      });

      expect(onDisconnect).toHaveBeenCalledTimes(1);
    });
  });

  describe("Message Handling", () => {
    it("should call onMessage callback when message received", async () => {
      const onMessage = jest.fn();
      const { result } = renderHook(() =>
        useWebSocket("ws://localhost:8080", { onMessage })
      );

      // Connect first
      await act(async () => {
        const mockWebSocket = MockWebSocket.instances[0];
        mockWebSocket.connect();
      });

      // Simulate message
      const mockWebSocket = MockWebSocket.instances[0];
      act(() => {
        mockWebSocket.simulateMessage({ type: "test", data: "hello" });
      });

      expect(onMessage).toHaveBeenCalledTimes(1);
    });

    it("should send string messages", async () => {
      const { result } = renderHook(() => useWebSocket("ws://localhost:8080"));

      // Connect first
      await act(async () => {
        const mockWebSocket = MockWebSocket.instances[0];
        mockWebSocket.connect();
      });

      const mockWebSocket = MockWebSocket.instances[0];
      const sendSpy = jest.spyOn(mockWebSocket, "send");

      act(() => {
        result.current.sendMessage("hello");
      });

      expect(sendSpy).toHaveBeenCalledWith("hello");
    });

    it("should send object messages as JSON", async () => {
      const { result } = renderHook(() => useWebSocket("ws://localhost:8080"));

      // Connect first
      await act(async () => {
        const mockWebSocket = MockWebSocket.instances[0];
        mockWebSocket.connect();
      });

      const mockWebSocket = MockWebSocket.instances[0];
      const sendSpy = jest.spyOn(mockWebSocket, "send");

      const message = { type: "test", data: "hello" };
      act(() => {
        result.current.sendMessage(message);
      });

      expect(sendSpy).toHaveBeenCalledWith(JSON.stringify(message));
    });

    it("should not send message when not connected", () => {
      const consoleSpy = jest.spyOn(console, "warn").mockImplementation();
      const { result } = renderHook(() => useWebSocket("ws://localhost:8080"));

      act(() => {
        result.current.sendMessage("hello");
      });

      expect(consoleSpy).toHaveBeenCalledWith(
        "WebSocket is not connected. Message not sent:",
        "hello"
      );

      consoleSpy.mockRestore();
    });
  });

  describe("Error Handling", () => {
    it("should call onError callback when error occurs", async () => {
      const onError = jest.fn();
      renderHook(() => useWebSocket("ws://localhost:8080", { onError }));

      // Connect first
      await act(async () => {
        const mockWebSocket = MockWebSocket.instances[0];
        mockWebSocket.connect();
      });

      // Simulate error
      const mockWebSocket = MockWebSocket.instances[0];
      act(() => {
        mockWebSocket.simulateError();
      });

      expect(onError).toHaveBeenCalledTimes(1);
    });

    it("should set error state when error occurs", async () => {
      const { result } = renderHook(() => useWebSocket("ws://localhost:8080"));

      // Connect first
      await act(async () => {
        const mockWebSocket = MockWebSocket.instances[0];
        mockWebSocket.connect();
      });

      // Simulate error
      const mockWebSocket = MockWebSocket.instances[0];
      act(() => {
        mockWebSocket.simulateError();
      });

      expect(result.current.connectionState).toBe("error");
    });

    it("should handle send message errors gracefully", async () => {
      const consoleSpy = jest.spyOn(console, "error").mockImplementation();
      const { result } = renderHook(() => useWebSocket("ws://localhost:8080"));

      // Connect first
      await act(async () => {
        const mockWebSocket = MockWebSocket.instances[0];
        mockWebSocket.connect();
      });

      const mockWebSocket = MockWebSocket.instances[0];
      jest.spyOn(mockWebSocket, "send").mockImplementation(() => {
        throw new Error("Send failed");
      });

      act(() => {
        result.current.sendMessage("hello");
      });

      expect(consoleSpy).toHaveBeenCalledWith(
        "Error sending WebSocket message:",
        expect.any(Error)
      );

      consoleSpy.mockRestore();
    });
  });

  describe("Reconnection Logic", () => {
    it("should attempt reconnection when connection is lost", async () => {
      const { result } = renderHook(() =>
        useWebSocket("ws://localhost:8080", {
          reconnectInterval: 1000,
          maxReconnectAttempts: 3,
        })
      );

      // Connect first
      await act(async () => {
        const mockWebSocket = MockWebSocket.instances[0];
        mockWebSocket.connect();
      });

      expect(result.current.isConnected).toBe(true);

      // Simulate connection loss
      const mockWebSocket = MockWebSocket.instances[0];
      act(() => {
        mockWebSocket.simulateClose();
      });

      expect(result.current.isConnected).toBe(false);

      // Advance timer to trigger reconnection
      await act(async () => {
        jest.advanceTimersByTime(1000);
      });

      // Should attempt to reconnect
      expect(MockWebSocket.instances).toHaveLength(2);
    });

    it("should stop reconnecting after max attempts", async () => {
      const { result } = renderHook(() =>
        useWebSocket("ws://localhost:8080", {
          reconnectInterval: 1000,
          maxReconnectAttempts: 2,
        })
      );

      // Connect first
      await act(async () => {
        const mockWebSocket = MockWebSocket.instances[0];
        mockWebSocket.connect();
      });

      // Simulate multiple connection losses
      for (let i = 0; i < 3; i++) {
        const currentInstances = MockWebSocket.instances.length;
        if (currentInstances > i) {
          const mockWebSocket = MockWebSocket.instances[i];
          act(() => {
            mockWebSocket.simulateClose();
          });

          await act(async () => {
            jest.advanceTimersByTime(1000);
          });
        }
      }

      // Should have attempted initial + 2 reconnections = 3 total
      expect(MockWebSocket.instances).toHaveLength(3);
    });

    it("should manually reconnect when reconnect is called", async () => {
      const { result } = renderHook(() => useWebSocket("ws://localhost:8080"));

      // Connect first
      await act(async () => {
        const mockWebSocket = MockWebSocket.instances[0];
        mockWebSocket.connect();
      });

      // Manually reconnect
      act(() => {
        result.current.reconnect();
      });

      await act(async () => {
        jest.advanceTimersByTime(100);
      });

      // Should have created 2 WebSocket instances
      expect(MockWebSocket.instances).toHaveLength(2);
    });
  });

  describe("Cleanup", () => {
    it("should cleanup on unmount", async () => {
      const { result, unmount } = renderHook(() =>
        useWebSocket("ws://localhost:8080")
      );

      // Connect first
      await act(async () => {
        const mockWebSocket = MockWebSocket.instances[0];
        mockWebSocket.connect();
      });

      const mockWebSocket = MockWebSocket.instances[0];
      const closeSpy = jest.spyOn(mockWebSocket, "close");

      unmount();

      expect(closeSpy).toHaveBeenCalled();
    });

    it("should clear timeouts on disconnect", async () => {
      const { result } = renderHook(() =>
        useWebSocket("ws://localhost:8080", { reconnectInterval: 1000 })
      );

      // Connect first
      await act(async () => {
        const mockWebSocket = MockWebSocket.instances[0];
        mockWebSocket.connect();
      });

      // Simulate connection loss to start reconnection timer
      const mockWebSocket = MockWebSocket.instances[0];
      act(() => {
        mockWebSocket.simulateClose();
      });

      // Disconnect before reconnection timer fires
      act(() => {
        result.current.disconnect();
      });

      // Advance timer past reconnection interval
      await act(async () => {
        jest.advanceTimersByTime(2000);
      });

      // Should not have attempted reconnection
      expect(MockWebSocket.instances).toHaveLength(1);
    });
  });

  describe("Heartbeat", () => {
    it("should send ping messages when connected", async () => {
      const { result } = renderHook(() => useWebSocket("ws://localhost:8080"));

      // Connect first
      await act(async () => {
        const mockWebSocket = MockWebSocket.instances[0];
        mockWebSocket.connect();
      });

      const mockWebSocket = MockWebSocket.instances[0];
      const sendSpy = jest.spyOn(mockWebSocket, "send");

      // Advance timer to trigger heartbeat
      await act(async () => {
        jest.advanceTimersByTime(30000);
      });

      expect(sendSpy).toHaveBeenCalledWith(JSON.stringify({ type: "ping" }));
    });

    it("should not send ping when disconnected", async () => {
      const { result } = renderHook(() => useWebSocket("ws://localhost:8080"));

      // Don't connect, just advance timer
      await act(async () => {
        jest.advanceTimersByTime(30000);
      });

      // Should have created WebSocket but not sent ping
      expect(MockWebSocket.instances).toHaveLength(1);
      const mockWebSocket = MockWebSocket.instances[0];
      const sendSpy = jest.spyOn(mockWebSocket, "send");
      expect(sendSpy).not.toHaveBeenCalled();
    });
  });
});
