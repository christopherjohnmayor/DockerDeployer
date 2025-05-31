import { AxiosError } from "axios";
import {
  ErrorType,
  parseError,
  getErrorMessage,
  isRetryableError,
  getErrorSeverity,
  getValidationErrors,
} from "./errorHandling";

// Mock AxiosError for testing
const createAxiosError = (
  status: number,
  data?: any,
  message: string = "Request failed"
): AxiosError => {
  const error = new Error(message) as AxiosError;
  error.isAxiosError = true;
  error.response = {
    status,
    data,
    statusText: "Error",
    headers: {},
    config: {} as any,
  };
  error.config = {} as any;
  return error;
};

describe("errorHandling utilities", () => {
  describe("parseError", () => {
    describe("Axios errors", () => {
      test("handles network errors (no response)", () => {
        const networkError = new Error("Network Error") as AxiosError;
        networkError.isAxiosError = true;
        networkError.response = undefined;
        networkError.message = "Network Error";

        const result = parseError(networkError);

        expect(result).toEqual({
          type: ErrorType.NETWORK,
          message:
            "Network connection failed. Please check your internet connection and try again.",
          details: "Network Error",
        });
      });

      test("handles 400 validation errors", () => {
        const error = createAxiosError(400, {
          detail: "Invalid input data",
        });

        const result = parseError(error);

        expect(result).toEqual({
          type: ErrorType.VALIDATION,
          message: "Invalid input data",
          details: "Request failed",
          code: 400,
          field: "",
        });
      });

      test("handles 401 authentication errors", () => {
        const error = createAxiosError(401, {
          detail: "Invalid credentials",
        });

        const result = parseError(error);

        expect(result).toEqual({
          type: ErrorType.AUTHENTICATION,
          message: "Invalid credentials",
          details: "Request failed",
          code: 401,
          field: "",
        });
      });

      test("handles 403 authorization errors", () => {
        const error = createAxiosError(403, {
          detail: "Access denied",
        });

        const result = parseError(error);

        expect(result).toEqual({
          type: ErrorType.AUTHORIZATION,
          message: "Access denied",
          details: "Request failed",
          code: 403,
          field: "",
        });
      });

      test("handles 404 not found errors", () => {
        const error = createAxiosError(404, {
          detail: "Resource not found",
        });

        const result = parseError(error);

        expect(result).toEqual({
          type: ErrorType.NOT_FOUND,
          message: "Resource not found",
          details: "Request failed",
          code: 404,
          field: "",
        });
      });

      test("handles 500 server errors", () => {
        const error = createAxiosError(500, {
          detail: "Internal server error",
        });

        const result = parseError(error);

        expect(result).toEqual({
          type: ErrorType.SERVER,
          message: "Internal server error",
          details: "Request failed",
          code: 500,
          field: "",
        });
      });

      test("handles FastAPI validation errors with array detail", () => {
        const error = createAxiosError(422, {
          detail: [
            {
              loc: ["body", "email"],
              msg: "field required",
              type: "value_error.missing",
            },
            {
              loc: ["body", "password"],
              msg: "ensure this value has at least 8 characters",
              type: "value_error.any_str.min_length",
            },
          ],
        });

        const result = parseError(error);

        expect(result).toEqual({
          type: ErrorType.VALIDATION,
          message:
            "body.email: field required, body.password: ensure this value has at least 8 characters",
          details: "Request failed",
          code: 422,
          field: "body.email",
        });
      });

      test("handles errors with message field", () => {
        const error = createAxiosError(400, {
          message: "Custom error message",
        });

        const result = parseError(error);

        expect(result).toEqual({
          type: ErrorType.VALIDATION,
          message: "Custom error message",
          details: "Request failed",
          code: 400,
          field: "",
        });
      });

      test("handles errors with error field", () => {
        const error = createAxiosError(500, {
          error: "Database connection failed",
        });

        const result = parseError(error);

        expect(result).toEqual({
          type: ErrorType.SERVER,
          message: "Database connection failed",
          details: "Request failed",
          code: 500,
          field: "",
        });
      });

      test("handles unknown status codes", () => {
        const error = createAxiosError(418, {
          detail: "I'm a teapot",
        });

        const result = parseError(error);

        expect(result).toEqual({
          type: ErrorType.UNKNOWN,
          message: "I'm a teapot",
          details: "Request failed",
          code: 418,
          field: "",
        });
      });

      test("handles errors without data", () => {
        const error = createAxiosError(500);

        const result = parseError(error);

        expect(result).toEqual({
          type: ErrorType.SERVER,
          message: "A server error occurred. Please try again later.",
          details: "Request failed",
          code: 500,
          field: "",
        });
      });
    });

    describe("JavaScript errors", () => {
      test("handles standard Error objects", () => {
        const error = new Error("Something went wrong");
        error.stack = "Error stack trace";

        const result = parseError(error);

        expect(result).toEqual({
          type: ErrorType.UNKNOWN,
          message: "Something went wrong",
          details: "Error stack trace",
        });
      });

      test("handles Error objects without message", () => {
        const error = new Error();

        const result = parseError(error);

        expect(result).toEqual({
          type: ErrorType.UNKNOWN,
          message: "An unexpected error occurred. Please try again.",
          details: error.stack,
        });
      });
    });

    describe("String errors", () => {
      test("handles string errors", () => {
        const error = "String error message";

        const result = parseError(error);

        expect(result).toEqual({
          type: ErrorType.UNKNOWN,
          message: "String error message",
        });
      });
    });

    describe("Unknown errors", () => {
      test("handles null errors", () => {
        const result = parseError(null);

        expect(result).toEqual({
          type: ErrorType.UNKNOWN,
          message: "An unexpected error occurred. Please try again.",
          details: "null",
        });
      });

      test("handles undefined errors", () => {
        const result = parseError(undefined);

        expect(result).toEqual({
          type: ErrorType.UNKNOWN,
          message: "An unexpected error occurred. Please try again.",
          details: "undefined",
        });
      });

      test("handles object errors", () => {
        const error = { custom: "error object" };

        const result = parseError(error);

        expect(result).toEqual({
          type: ErrorType.UNKNOWN,
          message: "An unexpected error occurred. Please try again.",
          details: "[object Object]",
        });
      });
    });
  });

  describe("getErrorMessage", () => {
    test("returns parsed error message", () => {
      const error = new Error("Test error");
      const message = getErrorMessage(error);

      expect(message).toBe("Test error");
    });

    test("returns message for Axios error", () => {
      const error = createAxiosError(400, { detail: "Validation failed" });
      const message = getErrorMessage(error);

      expect(message).toBe("Validation failed");
    });
  });

  describe("isRetryableError", () => {
    test("returns true for network errors", () => {
      const networkError = new Error("Network Error") as AxiosError;
      networkError.isAxiosError = true;
      networkError.response = undefined;

      expect(isRetryableError(networkError)).toBe(true);
    });

    test("returns true for server errors", () => {
      const error = createAxiosError(500);

      expect(isRetryableError(error)).toBe(true);
    });

    test("returns false for validation errors", () => {
      const error = createAxiosError(400);

      expect(isRetryableError(error)).toBe(false);
    });

    test("returns false for authentication errors", () => {
      const error = createAxiosError(401);

      expect(isRetryableError(error)).toBe(false);
    });

    test("returns false for authorization errors", () => {
      const error = createAxiosError(403);

      expect(isRetryableError(error)).toBe(false);
    });
  });

  describe("getErrorSeverity", () => {
    test("returns warning for validation errors", () => {
      const error = createAxiosError(400);

      expect(getErrorSeverity(error)).toBe("warning");
    });

    test("returns info for authentication errors", () => {
      const error = createAxiosError(401);

      expect(getErrorSeverity(error)).toBe("info");
    });

    test("returns info for authorization errors", () => {
      const error = createAxiosError(403);

      expect(getErrorSeverity(error)).toBe("info");
    });

    test("returns error for network errors", () => {
      const networkError = new Error("Network Error") as AxiosError;
      networkError.isAxiosError = true;
      networkError.response = undefined;

      expect(getErrorSeverity(networkError)).toBe("error");
    });

    test("returns error for server errors", () => {
      const error = createAxiosError(500);

      expect(getErrorSeverity(error)).toBe("error");
    });
  });

  describe("getValidationErrors", () => {
    test("returns empty object for non-validation errors", () => {
      const error = createAxiosError(500);

      const result = getValidationErrors(error);

      expect(result).toEqual({});
    });

    test("handles FastAPI validation errors", () => {
      const error = createAxiosError(422, {
        detail: [
          {
            loc: ["body", "email"],
            msg: "field required",
          },
          {
            loc: ["body", "password"],
            msg: "password too short",
          },
        ],
      });

      const result = getValidationErrors(error);

      expect(result).toEqual({
        "body.email": "field required",
        "body.password": "password too short",
      });
    });

    test("handles validation errors without loc field", () => {
      const error = createAxiosError(422, {
        detail: [
          {
            msg: "general validation error",
          },
        ],
      });

      const result = getValidationErrors(error);

      expect(result).toEqual({
        general: "general validation error",
      });
    });
  });
});
