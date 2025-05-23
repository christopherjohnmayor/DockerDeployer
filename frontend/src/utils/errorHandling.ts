import { AxiosError } from 'axios';

/**
 * Standard error types for the application
 */
export enum ErrorType {
  NETWORK = 'NETWORK',
  VALIDATION = 'VALIDATION',
  AUTHENTICATION = 'AUTHENTICATION',
  AUTHORIZATION = 'AUTHORIZATION',
  NOT_FOUND = 'NOT_FOUND',
  SERVER = 'SERVER',
  UNKNOWN = 'UNKNOWN',
}

/**
 * Standardized error interface
 */
export interface AppError {
  type: ErrorType;
  message: string;
  details?: string;
  code?: string | number;
  field?: string; // For validation errors
}

/**
 * HTTP status code to error type mapping
 */
const STATUS_TO_ERROR_TYPE: Record<number, ErrorType> = {
  400: ErrorType.VALIDATION,
  401: ErrorType.AUTHENTICATION,
  403: ErrorType.AUTHORIZATION,
  404: ErrorType.NOT_FOUND,
  422: ErrorType.VALIDATION,
  500: ErrorType.SERVER,
  502: ErrorType.NETWORK,
  503: ErrorType.NETWORK,
  504: ErrorType.NETWORK,
};

/**
 * User-friendly error messages
 */
const ERROR_MESSAGES: Record<ErrorType, string> = {
  [ErrorType.NETWORK]: 'Network connection failed. Please check your internet connection and try again.',
  [ErrorType.VALIDATION]: 'Please check your input and try again.',
  [ErrorType.AUTHENTICATION]: 'Please log in to continue.',
  [ErrorType.AUTHORIZATION]: 'You do not have permission to perform this action.',
  [ErrorType.NOT_FOUND]: 'The requested resource was not found.',
  [ErrorType.SERVER]: 'A server error occurred. Please try again later.',
  [ErrorType.UNKNOWN]: 'An unexpected error occurred. Please try again.',
};

/**
 * Parse and standardize errors from various sources
 * 
 * @param error - Error from API call, validation, etc.
 * @returns Standardized AppError object
 */
export function parseError(error: unknown): AppError {
  // Handle Axios errors
  if (error && typeof error === 'object' && 'isAxiosError' in error) {
    const axiosError = error as AxiosError<any>;
    
    // Network errors (no response)
    if (!axiosError.response) {
      return {
        type: ErrorType.NETWORK,
        message: ERROR_MESSAGES[ErrorType.NETWORK],
        details: axiosError.message,
      };
    }

    const { status, data } = axiosError.response;
    const errorType = STATUS_TO_ERROR_TYPE[status] || ErrorType.UNKNOWN;
    
    // Extract error message from response
    let message = ERROR_MESSAGES[errorType];
    let details = '';
    let field = '';

    if (data) {
      // FastAPI error format
      if (data.detail) {
        if (typeof data.detail === 'string') {
          message = data.detail;
        } else if (Array.isArray(data.detail)) {
          // Validation errors
          const validationErrors = data.detail.map((err: any) => {
            const fieldName = err.loc?.join('.') || 'field';
            return `${fieldName}: ${err.msg}`;
          }).join(', ');
          message = validationErrors;
          field = data.detail[0]?.loc?.join('.') || '';
        }
      }
      
      // Other error formats
      if (data.message) {
        message = data.message;
      }
      
      if (data.error) {
        message = data.error;
      }
    }

    return {
      type: errorType,
      message,
      details: axiosError.message,
      code: status,
      field,
    };
  }

  // Handle JavaScript errors
  if (error instanceof Error) {
    return {
      type: ErrorType.UNKNOWN,
      message: error.message || ERROR_MESSAGES[ErrorType.UNKNOWN],
      details: error.stack,
    };
  }

  // Handle string errors
  if (typeof error === 'string') {
    return {
      type: ErrorType.UNKNOWN,
      message: error,
    };
  }

  // Fallback for unknown error types
  return {
    type: ErrorType.UNKNOWN,
    message: ERROR_MESSAGES[ErrorType.UNKNOWN],
    details: String(error),
  };
}

/**
 * Get user-friendly error message
 * 
 * @param error - Error object or unknown error
 * @returns User-friendly error message
 */
export function getErrorMessage(error: unknown): string {
  const parsedError = parseError(error);
  return parsedError.message;
}

/**
 * Check if error is retryable
 * 
 * @param error - Error object
 * @returns True if the error is retryable
 */
export function isRetryableError(error: unknown): boolean {
  const parsedError = parseError(error);
  return [
    ErrorType.NETWORK,
    ErrorType.SERVER,
  ].includes(parsedError.type);
}

/**
 * Get appropriate error severity for UI display
 * 
 * @param error - Error object
 * @returns Severity level for alerts/toasts
 */
export function getErrorSeverity(error: unknown): 'error' | 'warning' | 'info' {
  const parsedError = parseError(error);
  
  switch (parsedError.type) {
    case ErrorType.VALIDATION:
      return 'warning';
    case ErrorType.AUTHENTICATION:
    case ErrorType.AUTHORIZATION:
      return 'info';
    default:
      return 'error';
  }
}

/**
 * Format validation errors for form display
 * 
 * @param error - Error object
 * @returns Object with field-specific error messages
 */
export function getValidationErrors(error: unknown): Record<string, string> {
  const parsedError = parseError(error);
  
  if (parsedError.type !== ErrorType.VALIDATION) {
    return {};
  }

  // Handle FastAPI validation errors
  if (error && typeof error === 'object' && 'isAxiosError' in error) {
    const axiosError = error as AxiosError<any>;
    const data = axiosError.response?.data;
    
    if (data?.detail && Array.isArray(data.detail)) {
      const validationErrors: Record<string, string> = {};
      
      data.detail.forEach((err: any) => {
        const fieldName = err.loc?.join('.') || 'general';
        validationErrors[fieldName] = err.msg;
      });
      
      return validationErrors;
    }
  }

  // Single field error
  if (parsedError.field) {
    return { [parsedError.field]: parsedError.message };
  }

  return { general: parsedError.message };
}
