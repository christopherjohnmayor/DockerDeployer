import React, { Component, ErrorInfo, ReactNode } from "react";
import {
  Alert,
  AlertTitle,
  Box,
  Button,
  Container,
  Typography,
} from "@mui/material";
import RefreshIcon from "@mui/icons-material/Refresh";
import BugReportIcon from "@mui/icons-material/BugReport";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

/**
 * Error Boundary component to catch and handle React errors gracefully
 *
 * Features:
 * - Catches JavaScript errors anywhere in the child component tree
 * - Logs error details for debugging
 * - Shows user-friendly error message
 * - Provides retry functionality
 * - Prevents app crashes from unhandled errors
 */
class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): State {
    // Update state so the next render will show the fallback UI
    return {
      hasError: true,
      error,
      errorInfo: null,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log error details for debugging
    console.error("ErrorBoundary caught an error:", error, errorInfo);

    this.setState({
      error,
      errorInfo,
    });

    // You can also log the error to an error reporting service here
    // Example: logErrorToService(error, errorInfo);
  }

  handleRetry = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI
      return (
        <Container maxWidth="md" sx={{ mt: 4 }}>
          <Alert severity="error" icon={<BugReportIcon />} sx={{ mb: 3 }}>
            <AlertTitle>Something went wrong</AlertTitle>
            <Typography variant="body2" sx={{ mb: 2 }}>
              An unexpected error occurred. This has been logged and our team
              will investigate.
            </Typography>

            <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap" }}>
              <Button
                variant="contained"
                startIcon={<RefreshIcon />}
                onClick={this.handleRetry}
                size="small"
              >
                Try Again
              </Button>

              <Button
                variant="outlined"
                onClick={() => window.location.reload()}
                size="small"
              >
                Reload Page
              </Button>
            </Box>
          </Alert>

          {/* Show error details in development */}
          {process.env.NODE_ENV === "development" && this.state.error && (
            <Alert severity="warning" sx={{ mt: 2 }}>
              <AlertTitle>Development Error Details</AlertTitle>
              <Typography
                variant="body2"
                component="pre"
                sx={{
                  fontSize: "0.75rem",
                  overflow: "auto",
                  maxHeight: 200,
                  whiteSpace: "pre-wrap",
                  wordBreak: "break-word",
                }}
              >
                {this.state.error.toString()}
                {this.state.errorInfo?.componentStack}
              </Typography>
            </Alert>
          )}
        </Container>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
