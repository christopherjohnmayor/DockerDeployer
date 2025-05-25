import React from "react";
import {
  Alert,
  AlertTitle,
  Box,
  Button,
  Collapse,
  IconButton,
  Typography,
} from "@mui/material";
import {
  Refresh as RefreshIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
} from "@mui/icons-material";
import { AppError, ErrorType } from "../utils/errorHandling";

interface ErrorDisplayProps {
  error: AppError | string | null;
  onRetry?: () => void;
  onDismiss?: () => void;
  showDetails?: boolean;
  variant?: "standard" | "outlined" | "filled";
  size?: "small" | "medium";
}

/**
 * Comprehensive error display component
 *
 * Features:
 * - Displays standardized error messages
 * - Shows appropriate severity and icons
 * - Expandable error details
 * - Retry functionality for retryable errors
 * - Dismissible alerts
 * - Multiple display variants
 */
const ErrorDisplay: React.FC<ErrorDisplayProps> = ({
  error,
  onRetry,
  onDismiss,
  showDetails = false,
  variant = "standard",
  size = "medium",
}) => {
  const [detailsExpanded, setDetailsExpanded] = React.useState(false);

  if (!error) {
    return null;
  }

  // Parse error if it's a string
  const parsedError: AppError =
    typeof error === "string"
      ? { type: ErrorType.UNKNOWN, message: error }
      : error;

  // Get appropriate severity and icon
  const getSeverity = () => {
    switch (parsedError.type) {
      case ErrorType.VALIDATION:
        return "warning" as const;
      case ErrorType.AUTHENTICATION:
      case ErrorType.AUTHORIZATION:
        return "info" as const;
      case ErrorType.NOT_FOUND:
        return "warning" as const;
      default:
        return "error" as const;
    }
  };

  const getIcon = () => {
    switch (getSeverity()) {
      case "warning":
        return <WarningIcon />;
      case "info":
        return <InfoIcon />;
      default:
        return <ErrorIcon />;
    }
  };

  const getTitle = () => {
    switch (parsedError.type) {
      case ErrorType.NETWORK:
        return "Connection Error";
      case ErrorType.VALIDATION:
        return "Validation Error";
      case ErrorType.AUTHENTICATION:
        return "Authentication Required";
      case ErrorType.AUTHORIZATION:
        return "Access Denied";
      case ErrorType.NOT_FOUND:
        return "Not Found";
      case ErrorType.SERVER:
        return "Server Error";
      default:
        return "Error";
    }
  };

  const isRetryable = [ErrorType.NETWORK, ErrorType.SERVER].includes(
    parsedError.type
  );

  const hasDetails = parsedError.details || parsedError.code;

  return (
    <Alert
      severity={getSeverity()}
      variant={variant}
      icon={getIcon()}
      onClose={onDismiss}
      sx={{
        "& .MuiAlert-message": {
          width: "100%",
        },
      }}
    >
      <AlertTitle>{getTitle()}</AlertTitle>

      <Typography
        variant={size === "small" ? "body2" : "body1"}
        sx={{ mb: hasDetails || onRetry ? 1 : 0 }}
      >
        {parsedError.message}
      </Typography>

      {/* Action buttons */}
      {(onRetry || hasDetails) && (
        <Box sx={{ display: "flex", alignItems: "center", gap: 1, mt: 1 }}>
          {onRetry && isRetryable && (
            <Button
              size="small"
              startIcon={<RefreshIcon />}
              onClick={onRetry}
              variant="outlined"
              color="inherit"
            >
              Try Again
            </Button>
          )}

          {hasDetails && showDetails && (
            <IconButton
              size="small"
              onClick={() => setDetailsExpanded(!detailsExpanded)}
              aria-label={detailsExpanded ? "Hide details" : "Show details"}
            >
              {detailsExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
            </IconButton>
          )}
        </Box>
      )}

      {/* Error details */}
      {hasDetails && showDetails && (
        <Collapse in={detailsExpanded}>
          <Box sx={{ mt: 2, p: 2, bgcolor: "action.hover", borderRadius: 1 }}>
            <Typography variant="subtitle2" gutterBottom>
              Error Details
            </Typography>

            {parsedError.code && (
              <Typography variant="body2" color="text.secondary">
                <strong>Code:</strong> {parsedError.code}
              </Typography>
            )}

            {parsedError.details && (
              <Typography
                variant="body2"
                color="text.secondary"
                component="pre"
                sx={{
                  mt: 1,
                  fontSize: "0.75rem",
                  overflow: "auto",
                  maxHeight: 200,
                  whiteSpace: "pre-wrap",
                  wordBreak: "break-word",
                }}
              >
                {parsedError.details}
              </Typography>
            )}
          </Box>
        </Collapse>
      )}
    </Alert>
  );
};

/**
 * Inline error display for form fields
 */
export const InlineErrorDisplay: React.FC<{
  error: string | null;
  field?: string;
}> = ({ error, _field }) => {
  if (!error) {
    return null;
  }

  return (
    <Typography
      variant="caption"
      color="error"
      sx={{
        display: "block",
        mt: 0.5,
        fontSize: "0.75rem",
      }}
    >
      {error}
    </Typography>
  );
};

/**
 * Compact error display for lists/cards
 */
export const CompactErrorDisplay: React.FC<{
  error: AppError | string | null;
  onRetry?: () => void;
}> = ({ error, onRetry }) => {
  if (!error) {
    return null;
  }

  const message = typeof error === "string" ? error : error.message;

  return (
    <Box
      sx={{
        display: "flex",
        alignItems: "center",
        gap: 1,
        p: 1,
        bgcolor: "error.light",
        color: "error.contrastText",
        borderRadius: 1,
        fontSize: "0.875rem",
      }}
    >
      <ErrorIcon fontSize="small" />
      <Typography variant="body2" sx={{ flex: 1 }}>
        {message}
      </Typography>
      {onRetry && (
        <IconButton size="small" onClick={onRetry} sx={{ color: "inherit" }}>
          <RefreshIcon fontSize="small" />
        </IconButton>
      )}
    </Box>
  );
};

export default ErrorDisplay;
