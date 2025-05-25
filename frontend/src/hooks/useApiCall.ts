import { useState, useCallback } from "react";
import { parseError, isRetryableError, AppError } from "../utils/errorHandling";
import { useToast } from "../components/Toast";

interface UseApiCallOptions {
  showSuccessToast?: boolean;
  showErrorToast?: boolean;
  successMessage?: string;
  retryAttempts?: number;
  retryDelay?: number;
}

interface UseApiCallReturn<T> {
  data: T | null;
  loading: boolean;
  error: AppError | null;
  execute: (...args: any[]) => Promise<T | null>;
  retry: () => Promise<T | null>;
  reset: () => void;
}

/**
 * Custom hook for handling API calls with error handling, loading states, and retry logic
 *
 * Features:
 * - Automatic error parsing and handling
 * - Loading state management
 * - Retry mechanism for retryable errors
 * - Toast notifications for success/error
 * - Reset functionality
 * - Type-safe return values
 *
 * @param apiFunction - The API function to call
 * @param options - Configuration options
 * @returns Object with data, loading, error states and control functions
 */
export function useApiCall<T>(
  apiFunction: (...args: any[]) => Promise<T>,
  options: UseApiCallOptions = {}
): UseApiCallReturn<T> {
  const {
    showSuccessToast = false,
    showErrorToast = true,
    successMessage = "Operation completed successfully",
    retryAttempts = 3,
    retryDelay = 1000,
  } = options;

  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<AppError | null>(null);
  const [lastArgs, setLastArgs] = useState<any[]>([]);
  const [, setCurrentRetryAttempt] = useState(0);

  const toast = useToast();

  // Simple execute function without retry logic
  // const execute = useCallback(
  //   async (...args: any[]): Promise<T | null> => {
  //     setLoading(true);
  //     setError(null);
  //     setLastArgs(args);
  //     setCurrentRetryAttempt(0);

  //     try {
  //       const result = await apiFunction(...args);
  //       setData(result);

  //       if (showSuccessToast) {
  //         toast.showSuccess(successMessage);
  //       }

  //       return result;
  //     } catch (err) {
  //       const parsedError = parseError(err);
  //       setError(parsedError);

  //       if (showErrorToast) {
  //         toast.showError(parsedError.message);
  //       }

  //       return null;
  //     } finally {
  //       setLoading(false);
  //     }
  //   },
  //   [apiFunction, showSuccessToast, showErrorToast, successMessage, toast]
  // );

  const executeWithRetry = useCallback(
    async (args: any[], attempt: number = 0): Promise<T | null> => {
      try {
        const result = await apiFunction(...args);
        setData(result);
        setCurrentRetryAttempt(0);

        if (showSuccessToast) {
          toast.showSuccess(successMessage);
        }

        return result;
      } catch (err) {
        const parsedError = parseError(err);

        // Check if we should retry
        if (attempt < retryAttempts && isRetryableError(err)) {
          setCurrentRetryAttempt(attempt + 1);

          // Wait before retrying
          await new Promise((resolve) =>
            setTimeout(resolve, retryDelay * (attempt + 1))
          );

          return executeWithRetry(args, attempt + 1);
        }

        // No more retries or non-retryable error
        setError(parsedError);
        setCurrentRetryAttempt(0);

        if (showErrorToast) {
          const retryMessage =
            attempt > 0
              ? ` (after ${attempt} ${attempt === 1 ? "retry" : "retries"})`
              : "";
          toast.showError(`${parsedError.message}${retryMessage}`);
        }

        return null;
      }
    },
    [
      apiFunction,
      retryAttempts,
      retryDelay,
      showSuccessToast,
      showErrorToast,
      successMessage,
      toast,
    ]
  );

  const executeWithAutoRetry = useCallback(
    async (...args: any[]): Promise<T | null> => {
      setLoading(true);
      setError(null);
      setLastArgs(args);

      const result = await executeWithRetry(args);

      setLoading(false);
      return result;
    },
    [executeWithRetry]
  );

  const _retry = useCallback(async (): Promise<T | null> => {
    if (lastArgs.length === 0) {
      console.warn("No previous arguments to retry with");
      return null;
    }

    return executeWithAutoRetry(...lastArgs);
  }, [lastArgs, executeWithAutoRetry]);

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setLoading(false);
    setLastArgs([]);
    setCurrentRetryAttempt(0);
  }, []);

  return {
    data,
    loading,
    error,
    execute: executeWithAutoRetry,
    retry: _retry,
    reset,
  };
}

/**
 * Simplified hook for API calls without retry logic
 */
export function useSimpleApiCall<T>(
  apiFunction: (...args: any[]) => Promise<T>,
  options: Omit<UseApiCallOptions, "retryAttempts" | "retryDelay"> = {}
): Omit<UseApiCallReturn<T>, "retry"> {
  const result = useApiCall(apiFunction, {
    ...options,
    retryAttempts: 0,
  });
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const { retry, ...rest } = result;
  return rest;
}

/**
 * Hook for API calls that should show loading state immediately
 */
export function useApiCallWithImmedateLoading<T>(
  apiFunction: (...args: any[]) => Promise<T>,
  options: UseApiCallOptions = {}
): UseApiCallReturn<T> {
  const result = useApiCall(apiFunction, options);

  const executeWithImmediateLoading = useCallback(
    async (...args: any[]): Promise<T | null> => {
      // Set loading immediately
      return result.execute(...args);
    },
    [result.execute]
  );

  return {
    ...result,
    execute: executeWithImmediateLoading,
  };
}
