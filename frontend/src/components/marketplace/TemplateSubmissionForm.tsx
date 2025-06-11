import React, { useState, useEffect } from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Typography,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Box,
  Stepper,
  Step,
  StepLabel,
  Paper,
  Chip,
  IconButton,
  Alert,
} from "@mui/material";
import {
  Close as CloseIcon,
  Add as AddIcon,
  Remove as RemoveIcon,
} from "@mui/icons-material";
import { useApiCall } from "../../hooks/useApiCall";
import { LoadingState } from "../LoadingState";
import ErrorDisplay from "../ErrorDisplay";
import {
  createTemplate,
  TemplateCreate,
  Category,
} from "../../api/marketplace";

interface TemplateSubmissionFormProps {
  open: boolean;
  onClose: () => void;
  onSubmitted: () => void;
  categories: Category[];
}

const steps = ["Basic Information", "Docker Compose", "Review & Submit"];

/**
 * Template Submission Form Component
 *
 * Multi-step form for submitting new templates to the marketplace.
 * Includes validation, preview, and submission functionality.
 *
 * Features:
 * - Multi-step wizard interface
 * - Form validation with error messages
 * - Docker Compose YAML validation
 * - Tags management with add/remove
 * - Template preview before submission
 * - Loading states and error handling
 */
const TemplateSubmissionForm: React.FC<TemplateSubmissionFormProps> = ({
  open,
  onClose,
  onSubmitted,
  categories,
}) => {
  const [activeStep, setActiveStep] = useState(0);
  const [formData, setFormData] = useState<TemplateCreate>({
    name: "",
    description: "",
    category_id: 0,
    docker_compose_yaml: "",
    tags: [],
    version: "1.0.0",
  });

  // Set default category when categories are available
  useEffect(() => {
    if (categories.length > 0 && formData.category_id === 0) {
      setFormData((prev) => ({ ...prev, category_id: categories[0].id }));
    }
  }, [categories, formData.category_id]);
  const [newTag, setNewTag] = useState("");
  const [validationErrors, setValidationErrors] = useState<
    Record<string, string>
  >({});

  // API call for template submission
  const {
    loading: submitting,
    error: submitError,
    execute: submitTemplate,
  } = useApiCall(createTemplate, {
    showSuccessToast: true,
    successMessage:
      "Template submitted successfully! It will be reviewed by administrators.",
  });

  const validateStep = (step: number): boolean => {
    const errors: Record<string, string> = {};

    switch (step) {
      case 0: // Basic Information
        if (!formData.name.trim()) {
          errors.name = "Template name is required";
        } else if (formData.name.length < 3) {
          errors.name = "Template name must be at least 3 characters";
        }

        if (!formData.description.trim()) {
          errors.description = "Description is required";
        } else if (formData.description.length < 10) {
          errors.description = "Description must be at least 10 characters";
        }

        if (!formData.category_id) {
          errors.category_id = "Please select a category";
        }

        if (!formData.version.trim()) {
          errors.version = "Version is required";
        }
        break;

      case 1: // Docker Compose
        if (!formData.docker_compose_yaml.trim()) {
          errors.docker_compose_yaml = "Docker Compose YAML is required";
        } else if (formData.docker_compose_yaml.length < 50) {
          errors.docker_compose_yaml = "Docker Compose YAML seems too short";
        }
        break;
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleNext = () => {
    if (validateStep(activeStep)) {
      setActiveStep((prev) => prev + 1);
    }
  };

  const handleBack = () => {
    setActiveStep((prev) => prev - 1);
  };

  const handleSubmit = async () => {
    if (validateStep(1)) {
      // Validate all steps
      const result = await submitTemplate(formData);
      if (result) {
        onSubmitted();
        handleClose();
      }
    }
  };

  const handleClose = () => {
    setActiveStep(0);
    setFormData({
      name: "",
      description: "",
      category_id: 0,
      docker_compose_yaml: "",
      tags: [],
      version: "1.0.0",
    });
    setValidationErrors({});
    setNewTag("");
    onClose();
  };

  const handleAddTag = () => {
    if (newTag.trim() && !formData.tags.includes(newTag.trim())) {
      setFormData((prev) => ({
        ...prev,
        tags: [...prev.tags, newTag.trim()],
      }));
      setNewTag("");
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setFormData((prev) => ({
      ...prev,
      tags: prev.tags.filter((tag) => tag !== tagToRemove),
    }));
  };

  const renderStepContent = (step: number) => {
    switch (step) {
      case 0:
        return (
          <Box display="flex" flexDirection="column" gap={3}>
            <TextField
              fullWidth
              label="Template Name"
              value={formData.name}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, name: e.target.value }))
              }
              error={!!validationErrors.name}
              helperText={validationErrors.name}
              required
            />

            <TextField
              fullWidth
              multiline
              rows={4}
              label="Description"
              value={formData.description}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  description: e.target.value,
                }))
              }
              error={!!validationErrors.description}
              helperText={validationErrors.description}
              required
            />

            <FormControl fullWidth error={!!validationErrors.category_id}>
              <InputLabel>Category *</InputLabel>
              <Select
                value={formData.category_id || ""}
                label="Category *"
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    category_id: Number(e.target.value),
                  }))
                }
              >
                {categories.map((category) => (
                  <MenuItem key={category.id} value={category.id}>
                    {category.name}
                  </MenuItem>
                ))}
              </Select>
              {validationErrors.category_id && (
                <Typography
                  variant="caption"
                  color="error"
                  sx={{ mt: 0.5, ml: 1.5 }}
                >
                  {validationErrors.category_id}
                </Typography>
              )}
            </FormControl>

            <TextField
              fullWidth
              label="Version"
              value={formData.version}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, version: e.target.value }))
              }
              error={!!validationErrors.version}
              helperText={
                validationErrors.version ||
                "Semantic versioning recommended (e.g., 1.0.0)"
              }
              required
            />

            {/* Tags */}
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Tags (optional)
              </Typography>
              <Box display="flex" gap={1} mb={2}>
                <TextField
                  size="small"
                  label="Add tag"
                  value={newTag}
                  onChange={(e) => setNewTag(e.target.value)}
                  onKeyPress={(e) => e.key === "Enter" && handleAddTag()}
                />
                <Button
                  variant="outlined"
                  startIcon={<AddIcon />}
                  onClick={handleAddTag}
                  disabled={!newTag.trim()}
                >
                  Add
                </Button>
              </Box>
              <Box display="flex" flexWrap="wrap" gap={1}>
                {formData.tags.map((tag, index) => (
                  <Chip
                    key={index}
                    label={tag}
                    onDelete={() => handleRemoveTag(tag)}
                    deleteIcon={<RemoveIcon />}
                  />
                ))}
              </Box>
            </Box>
          </Box>
        );

      case 1:
        return (
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Docker Compose YAML *
            </Typography>
            <TextField
              fullWidth
              multiline
              rows={20}
              label="Docker Compose YAML"
              value={formData.docker_compose_yaml}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  docker_compose_yaml: e.target.value,
                }))
              }
              error={!!validationErrors.docker_compose_yaml}
              helperText={validationErrors.docker_compose_yaml}
              placeholder="version: '3.8'&#10;services:&#10;  app:&#10;    image: nginx:latest&#10;    ports:&#10;      - '80:80'"
              sx={{
                "& .MuiInputBase-input": {
                  fontFamily: "monospace",
                  fontSize: "0.875rem",
                },
              }}
            />
          </Box>
        );

      case 2:
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              Review Your Template
            </Typography>

            <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Basic Information
              </Typography>
              <Typography>
                <strong>Name:</strong> {formData.name}
              </Typography>
              <Typography>
                <strong>Description:</strong> {formData.description}
              </Typography>
              <Typography>
                <strong>Category:</strong>{" "}
                {categories.find((c) => c.id === formData.category_id)?.name}
              </Typography>
              <Typography>
                <strong>Version:</strong> {formData.version}
              </Typography>
              {formData.tags.length > 0 && (
                <Box mt={1}>
                  <Typography component="span">
                    <strong>Tags:</strong>{" "}
                  </Typography>
                  {formData.tags.map((tag, index) => (
                    <Chip
                      key={index}
                      label={tag}
                      size="small"
                      sx={{ ml: 0.5 }}
                    />
                  ))}
                </Box>
              )}
            </Paper>

            <Alert severity="info" sx={{ mb: 2 }}>
              Your template will be reviewed by administrators before being
              published to the marketplace.
            </Alert>
          </Box>
        );

      default:
        return null;
    }
  };

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: { height: "90vh", maxHeight: 700 },
      }}
    >
      <DialogTitle>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Typography variant="h6">Submit New Template</Typography>
          <IconButton onClick={handleClose}>
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent dividers>
        <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>

        {submitError && (
          <ErrorDisplay
            error={submitError}
            onRetry={handleSubmit}
            title="Failed to submit template"
            sx={{ mb: 3 }}
          />
        )}

        {renderStepContent(activeStep)}
      </DialogContent>

      <DialogActions sx={{ p: 3 }}>
        <Button onClick={handleClose} disabled={submitting}>
          Cancel
        </Button>
        <Box sx={{ flex: 1 }} />
        {activeStep > 0 && (
          <Button onClick={handleBack} disabled={submitting}>
            Back
          </Button>
        )}
        {activeStep < steps.length - 1 ? (
          <Button variant="contained" onClick={handleNext}>
            Next
          </Button>
        ) : (
          <Button
            variant="contained"
            onClick={handleSubmit}
            disabled={submitting}
          >
            {submitting ? "Submitting..." : "Submit Template"}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default TemplateSubmissionForm;
