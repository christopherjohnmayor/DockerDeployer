import React from "react";
import { renderHook, act } from "@testing-library/react";
import { useApiCall } from "./useApiCall";

// Mock the toast component
jest.mock("../components/Toast", () => ({
  useToast: () => ({
    showSuccess: jest.fn(),
    showError: jest.fn(),
    showWarning: jest.fn(),
    showInfo: jest.fn(),
    showToast: jest.fn(),
  }),
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

describe("useApiCall Hook", () => {
  beforeEach(() => {
    jest.clearAllMocks();
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
      const slowApi = jest.fn(() => new Promise((resolve) => {
        resolvePromise = resolve;
      }));

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
      const consoleSpy = jest.spyOn(console, "warn").mockImplementation(() => {});
      
      const { result } = renderHook(() => useApiCall(mockSuccessApi));

      let retryResult: any;
      await act(async () => {
        retryResult = await result.current.retry();
      });

      expect(consoleSpy).toHaveBeenCalledWith("No previous arguments to retry with");
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
          successMessage: "Custom success"
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
});
