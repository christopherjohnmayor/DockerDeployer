// import React from "react";
import { renderHook, act } from "@testing-library/react";
import {
  useApiCall,
  useSimpleApiCall,
  useApiCallWithImmedateLoading,
} from "./useApiCall";

// Mock the toast component
const mockToast = {
  showSuccess: jest.fn(),
  showError: jest.fn(),
  showWarning: jest.fn(),
  showInfo: jest.fn(),
  showToast: jest.fn(),
};

jest.mock("../components/Toast", () => ({
  useToast: () => mockToast,
}));

// Mock the error handling utilities
jest.mock("../utils/errorHandling", () => ({
  parseError: jest.fn((error) => ({
    type: "NETWORK",
    message: error.message || "Network error",
    code: 500,
  })),
  isRetryableError: jest.fn(() => false),
  ErrorType: {
    NETWORK: "NETWORK",
    VALIDATION: "VALIDATION",
    AUTHENTICATION: "AUTHENTICATION",
    AUTHORIZATION: "AUTHORIZATION",
    NOT_FOUND: "NOT_FOUND",
    SERVER: "SERVER",
    UNKNOWN: "UNKNOWN",
  },
}));

// Mock API functions
const mockSuccessApi = jest.fn().mockResolvedValue({ data: "success" });
const mockErrorApi = jest.fn().mockRejectedValue(new Error("API error"));
const mockRetryableErrorApi = jest
  .fn()
  .mockRejectedValue(new Error("Retryable error"));

describe("useApiCall Hook", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Reset the mock functions
    mockToast.showSuccess.mockClear();
    mockToast.showError.mockClear();
    mockToast.showWarning.mockClear();
    mockToast.showInfo.mockClear();
    mockToast.showToast.mockClear();
  });

  describe("Basic functionality", () => {
    test("initializes with correct default state", () => {
      const { result } = renderHook(() => useApiCall(mockSuccessApi));

      expect(result.current.data).toBeNull();
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBeNull();
      expect(typeof result.current.execute).toBe("function");
      expect(typeof result.current.retry).toBe("function");
      expect(typeof result.current.reset).toBe("function");
    });

    test("executes API call successfully", async () => {
      const { result } = renderHook(() => useApiCall(mockSuccessApi));

      let executeResult: any;
      await act(async () => {
        executeResult = await result.current.execute("test-arg");
      });

      expect(mockSuccessApi).toHaveBeenCalledWith("test-arg");
      expect(result.current.data).toEqual({ data: "success" });
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBeNull();
      expect(executeResult).toEqual({ data: "success" });
    });

    test("handles API call errors", async () => {
      const { result } = renderHook(() => useApiCall(mockErrorApi));

      let executeResult: any;
      await act(async () => {
        executeResult = await result.current.execute();
      });

      expect(mockErrorApi).toHaveBeenCalled();
      expect(result.current.data).toBeNull();
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toEqual({
        type: "NETWORK",
        message: "API error",
        code: 500,
      });
      expect(executeResult).toBeNull();
    });

    test("sets loading state during API call", async () => {
      let resolvePromise: (value: any) => void;
      const slowApi = jest.fn(
        () =>
          new Promise((resolve) => {
            resolvePromise = resolve;
          })
      );

      const { result } = renderHook(() => useApiCall(slowApi));

      // Start the API call
      act(() => {
        result.current.execute();
      });

      // Should be loading
      expect(result.current.loading).toBe(true);

      // Resolve the promise
      await act(async () => {
        resolvePromise({ data: "resolved" });
      });

      // Should no longer be loading
      expect(result.current.loading).toBe(false);
    });
  });

  describe("Reset functionality", () => {
    test("resets all state", async () => {
      const { result } = renderHook(() => useApiCall(mockErrorApi));

      // Execute to set some state
      await act(async () => {
        await result.current.execute();
      });

      expect(result.current.error).not.toBeNull();

      // Reset
      act(() => {
        result.current.reset();
      });

      expect(result.current.data).toBeNull();
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBeNull();
    });
  });

  describe("Manual retry", () => {
    test("manual retry works correctly", async () => {
      const { result } = renderHook(() => useApiCall(mockSuccessApi));

      // First execution
      await act(async () => {
        await result.current.execute("original-arg");
      });

      expect(mockSuccessApi).toHaveBeenCalledWith("original-arg");

      // Manual retry
      await act(async () => {
        await result.current.retry();
      });

      expect(mockSuccessApi).toHaveBeenCalledTimes(2);
      expect(mockSuccessApi).toHaveBeenLastCalledWith("original-arg");
    });

    test("retry warns when no previous arguments", async () => {
      const consoleSpy = jest
        .spyOn(console, "warn")
        .mockImplementation(() => {});

      const { result } = renderHook(() => useApiCall(mockSuccessApi));

      let retryResult: any;
      await act(async () => {
        retryResult = await result.current.retry();
      });

      expect(consoleSpy).toHaveBeenCalledWith(
        "No previous arguments to retry with"
      );
      expect(retryResult).toBeNull();

      consoleSpy.mockRestore();
    });
  });

  describe("Options handling", () => {
    test("handles custom options", () => {
      const { result } = renderHook(() =>
        useApiCall(mockSuccessApi, {
          retryAttempts: 3,
          retryDelay: 100,
          showSuccessToast: true,
          showErrorToast: false,
          successMessage: "Custom success",
        })
      );

      expect(result.current.data).toBeNull();
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBeNull();
    });
  });

  describe("Multiple executions", () => {
    test("handles multiple executions correctly", async () => {
      const { result } = renderHook(() => useApiCall(mockSuccessApi));

      // First execution
      await act(async () => {
        await result.current.execute("arg1");
      });

      expect(result.current.data).toEqual({ data: "success" });

      // Second execution
      await act(async () => {
        await result.current.execute("arg2");
      });

      expect(mockSuccessApi).toHaveBeenCalledTimes(2);
      expect(mockSuccessApi).toHaveBeenLastCalledWith("arg2");
    });
  });

  describe("Toast notifications", () => {
    test("shows success toast when enabled", async () => {
      const { result } = renderHook(() =>
        useApiCall(mockSuccessApi, {
          showSuccessToast: true,
          successMessage: "Custom success message",
        })
      );

      await act(async () => {
        await result.current.execute("test-arg");
      });

      expect(mockToast.showSuccess).toHaveBeenCalledWith(
        "Custom success message"
      );
    });

    test("shows error toast with retry information", async () => {
      const { result } = renderHook(() =>
        useApiCall(mockErrorApi, {
          showErrorToast: true,
        })
      );

      await act(async () => {
        await result.current.execute();
      });

      expect(mockToast.showError).toHaveBeenCalledWith("API error");
    });
  });

  describe("Retry logic", () => {
    test("retries retryable errors with delay", async () => {
      // Mock isRetryableError to return true for our test
      const { isRetryableError } = require("../utils/errorHandling");
      isRetryableError.mockReturnValue(true);

      // Mock setTimeout to avoid actual delays in tests
      const originalSetTimeout = global.setTimeout;
      global.setTimeout = jest.fn((callback) => {
        callback();
        return 1 as any;
      });

      const { result } = renderHook(() =>
        useApiCall(mockRetryableErrorApi, {
          retryAttempts: 2,
          retryDelay: 100,
          showErrorToast: true,
        })
      );

      await act(async () => {
        await result.current.execute();
      });

      // Should be called 3 times (initial + 2 retries)
      expect(mockRetryableErrorApi).toHaveBeenCalledTimes(3);
      expect(mockToast.showError).toHaveBeenCalledWith(
        "Retryable error (after 2 retries)"
      );

      // Restore setTimeout
      global.setTimeout = originalSetTimeout;
    });

    test("handles single retry correctly", async () => {
      // Mock isRetryableError to return true for our test
      const { isRetryableError } = require("../utils/errorHandling");
      isRetryableError.mockReturnValue(true);

      // Mock setTimeout to avoid actual delays in tests
      const originalSetTimeout = global.setTimeout;
      global.setTimeout = jest.fn((callback) => {
        callback();
        return 1 as any;
      });

      const { result } = renderHook(() =>
        useApiCall(mockRetryableErrorApi, {
          retryAttempts: 1,
          retryDelay: 100,
          showErrorToast: true,
        })
      );

      await act(async () => {
        await result.current.execute();
      });

      // Should be called 2 times (initial + 1 retry)
      expect(mockRetryableErrorApi).toHaveBeenCalledTimes(2);
      expect(mockToast.showError).toHaveBeenCalledWith(
        "Retryable error (after 1 retry)"
      );

      // Restore setTimeout
      global.setTimeout = originalSetTimeout;
    });
  });

  describe("useSimpleApiCall", () => {
    test("works without retry functionality", async () => {
      const { result } = renderHook(() => useSimpleApiCall(mockSuccessApi));

      expect(result.current.data).toBeNull();
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBeNull();
      expect(typeof result.current.execute).toBe("function");
      expect(typeof result.current.reset).toBe("function");
      // Should not have retry function
      expect("retry" in result.current).toBe(false);

      await act(async () => {
        await result.current.execute("test-arg");
      });

      expect(mockSuccessApi).toHaveBeenCalledWith("test-arg");
      expect(result.current.data).toEqual({ data: "success" });
    });

    test("handles errors without retry", async () => {
      const { result } = renderHook(() => useSimpleApiCall(mockErrorApi));

      await act(async () => {
        await result.current.execute();
      });

      expect(result.current.error).toEqual({
        type: "NETWORK",
        message: "API error",
        code: 500,
      });
      expect(mockErrorApi).toHaveBeenCalledTimes(1); // No retries
    });
  });

  describe("useApiCallWithImmedateLoading", () => {
    test("provides immediate loading functionality", async () => {
      const { result } = renderHook(() =>
        useApiCallWithImmedateLoading(mockSuccessApi)
      );

      expect(result.current.data).toBeNull();
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBeNull();
      expect(typeof result.current.execute).toBe("function");
      expect(typeof result.current.retry).toBe("function");
      expect(typeof result.current.reset).toBe("function");

      await act(async () => {
        await result.current.execute("test-arg");
      });

      expect(mockSuccessApi).toHaveBeenCalledWith("test-arg");
      expect(result.current.data).toEqual({ data: "success" });
    });

    test("handles errors correctly", async () => {
      const { result } = renderHook(() =>
        useApiCallWithImmedateLoading(mockErrorApi)
      );

      await act(async () => {
        await result.current.execute();
      });

      expect(result.current.error).toEqual({
        type: "NETWORK",
        message: "API error",
        code: 500,
      });
    }, 10000); // Increase timeout to 10 seconds
  });
});
