import React, { useState, useEffect } from "react";
import {
  Box,
  Button,
  Container,
  TextField,
  Typography,
  Paper,
  Link,
  CircularProgress,
  Alert,
} from "@mui/material";
import { Link as RouterLink, useNavigate, useSearchParams } from "react-router-dom";
import axios from "axios";
import { useToast } from "../components/Toast";
import ErrorDisplay from "../components/ErrorDisplay";
import { parseError, getValidationErrors } from "../utils/errorHandling";

const ResetPassword: React.FC = () => {
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const toast = useToast();

  const token = searchParams.get("token");

  useEffect(() => {
    if (!token) {
      setError("Invalid or missing reset token");
    }
  }, [token]);

  const validateForm = () => {
    // Check if passwords match
    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return false;
    }

    // Check password strength
    if (password.length < 8) {
      setError("Password must be at least 8 characters long");
      return false;
    }

    if (!/[A-Z]/.test(password)) {
      setError("Password must contain at least one uppercase letter");
      return false;
    }

    if (!/[a-z]/.test(password)) {
      setError("Password must contain at least one lowercase letter");
      return false;
    }

    if (!/[0-9]/.test(password)) {
      setError("Password must contain at least one number");
      return false;
    }

    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setFieldErrors({});

    if (!token) {
      setError("Invalid or missing reset token");
      return;
    }

    // Validate form
    if (!validateForm()) {
      return;
    }

    setLoading(true);

    try {
      await axios.post("/auth/password-reset-confirm", {
        token,
        new_password: password,
      });

      setSuccess("Password has been reset successfully!");
      toast.showSuccess("Password reset successful! Redirecting to login...");

      // Redirect to login page after 2 seconds
      setTimeout(() => {
        navigate("/login");
      }, 2000);
    } catch (err: unknown) {
      const parsedError = parseError(err);
      const validationErrors = getValidationErrors(err);

      if (Object.keys(validationErrors).length > 0) {
        setFieldErrors(validationErrors);
      } else {
        setError(parsedError.message);
      }
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return (
      <Container maxWidth="sm">
        <Box
          sx={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            minHeight: "100vh",
          }}
        >
          <Paper
            elevation={3}
            sx={{
              p: 4,
              width: "100%",
              borderRadius: 2,
            }}
          >
            <Typography variant="h4" component="h1" gutterBottom align="center">
              DockerDeployer
            </Typography>
            <Typography variant="h5" component="h2" gutterBottom align="center">
              Invalid Reset Link
            </Typography>
            <Alert severity="error" sx={{ mb: 2 }}>
              This password reset link is invalid or has expired.
            </Alert>
            <Box sx={{ textAlign: "center" }}>
              <Link component={RouterLink} to="/forgot-password" variant="body2">
                Request a new reset link
              </Link>
            </Box>
          </Paper>
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="sm">
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          minHeight: "100vh",
        }}
      >
        <Paper
          elevation={3}
          sx={{
            p: 4,
            width: "100%",
            borderRadius: 2,
          }}
        >
          <Typography variant="h4" component="h1" gutterBottom align="center">
            DockerDeployer
          </Typography>
          <Typography variant="h5" component="h2" gutterBottom align="center">
            Reset Password
          </Typography>
          <Typography variant="body2" align="center" sx={{ mb: 3 }}>
            Enter your new password below.
          </Typography>

          {error && (
            <ErrorDisplay
              error={error}
              onDismiss={() => setError(null)}
              variant="outlined"
            />
          )}

          {success && (
            <Alert severity="success" sx={{ mb: 2 }}>
              {success}
            </Alert>
          )}

          <Box component="form" onSubmit={handleSubmit} noValidate>
            <TextField
              margin="normal"
              required
              fullWidth
              name="password"
              label="New Password"
              type="password"
              id="password"
              autoComplete="new-password"
              autoFocus
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
              error={!!fieldErrors.password}
              helperText={
                fieldErrors.password ||
                "Password must be at least 8 characters long and contain uppercase, lowercase, and numbers"
              }
            />
            <TextField
              margin="normal"
              required
              fullWidth
              name="confirmPassword"
              label="Confirm New Password"
              type="password"
              id="confirmPassword"
              autoComplete="new-password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              disabled={loading}
              error={!!fieldErrors.confirmPassword}
              helperText={fieldErrors.confirmPassword}
            />
            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{ mt: 3, mb: 2 }}
              disabled={loading || !password || !confirmPassword}
            >
              {loading ? <CircularProgress size={24} /> : "Reset Password"}
            </Button>
            <Box sx={{ mt: 2, textAlign: "center" }}>
              <Typography variant="body2">
                Remember your password?{" "}
                <Link component={RouterLink} to="/login" variant="body2">
                  Back to Login
                </Link>
              </Typography>
            </Box>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
};

export default ResetPassword;
