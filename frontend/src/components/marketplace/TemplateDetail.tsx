import React, { useState, useEffect } from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Typography,
  Box,
  Button,
  Chip,
  Rating,
  Tabs,
  Tab,
  IconButton,
  Avatar,
  Divider,
  Paper,
  Alert,
} from "@mui/material";
import {
  Close as CloseIcon,
  Download as DownloadIcon,
  Person as PersonIcon,
  Schedule as ScheduleIcon,
  Category as CategoryIcon,
  Code as CodeIcon,
} from "@mui/icons-material";
import { useApiCall } from "../../hooks/useApiCall";
import { LoadingState } from "../LoadingState";
import ErrorDisplay from "../ErrorDisplay";
import TemplateReviews from "./TemplateReviews";
import { Template, fetchTemplateReviews, Review } from "../../api/marketplace";
import { useAuth } from "../../hooks/useAuth";

interface TemplateDetailProps {
  template: Template;
  open: boolean;
  onClose: () => void;
  onDownload: (template: Template) => void;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`template-tabpanel-${index}`}
      aria-labelledby={`template-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 2 }}>{children}</Box>}
    </div>
  );
}

/**
 * Template Detail Component
 * 
 * Displays comprehensive template information in a modal dialog.
 * Includes overview, Docker Compose YAML, and reviews sections.
 * 
 * Features:
 * - Tabbed interface for organized content
 * - Template metadata and description
 * - Syntax-highlighted YAML viewer
 * - Reviews and ratings display
 * - Download functionality
 * - Author information
 * - Responsive design
 */
const TemplateDetail: React.FC<TemplateDetailProps> = ({
  template,
  open,
  onClose,
  onDownload,
}) => {
  const { user } = useAuth();
  const [tabValue, setTabValue] = useState(0);

  // API calls
  const {
    data: reviews,
    loading: reviewsLoading,
    error: reviewsError,
    execute: loadReviews,
  } = useApiCall<Review[]>(fetchTemplateReviews);

  // Load reviews when template changes
  useEffect(() => {
    if (template && open) {
      loadReviews(template.id);
    }
  }, [template, open, loadReviews]);

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "approved":
        return "success";
      case "pending":
        return "warning";
      case "rejected":
        return "error";
      default:
        return "default";
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  const canDownload = template.status === "approved";

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="lg"
      fullWidth
      PaperProps={{
        sx: { height: "90vh", maxHeight: 800 },
      }}
    >
      <DialogTitle>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box display="flex" alignItems="center" gap={2}>
            <Typography variant="h5" component="h2">
              {template.name}
            </Typography>
            <Chip
              label={template.status}
              size="small"
              color={getStatusColor(template.status) as any}
            />
            {template.version && (
              <Chip
                label={`v${template.version}`}
                size="small"
                variant="outlined"
              />
            )}
          </Box>
          <IconButton onClick={onClose} size="large">
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent dividers sx={{ p: 0 }}>
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          sx={{ borderBottom: 1, borderColor: "divider", px: 3 }}
        >
          <Tab label="Overview" />
          <Tab label="Docker Compose" />
          <Tab label="Reviews" />
        </Tabs>

        <Box sx={{ px: 3 }}>
          {/* Overview Tab */}
          <TabPanel value={tabValue} index={0}>
            {/* Template Info */}
            <Box mb={3}>
              <Typography variant="h6" gutterBottom>
                Description
              </Typography>
              <Typography variant="body1" paragraph>
                {template.description}
              </Typography>
            </Box>

            {/* Metadata */}
            <Box mb={3}>
              <Typography variant="h6" gutterBottom>
                Details
              </Typography>
              <Box display="flex" flexWrap="wrap" gap={2} mb={2}>
                {template.category_name && (
                  <Box display="flex" alignItems="center" gap={1}>
                    <CategoryIcon color="action" />
                    <Typography variant="body2">
                      Category: {template.category_name}
                    </Typography>
                  </Box>
                )}
                <Box display="flex" alignItems="center" gap={1}>
                  <ScheduleIcon color="action" />
                  <Typography variant="body2">
                    Created: {formatDate(template.created_at)}
                  </Typography>
                </Box>
                <Box display="flex" alignItems="center" gap={1}>
                  <DownloadIcon color="action" />
                  <Typography variant="body2">
                    Downloads: {template.downloads}
                  </Typography>
                </Box>
              </Box>

              {/* Author */}
              <Box display="flex" alignItems="center" gap={1} mb={2}>
                <Avatar sx={{ width: 24, height: 24 }}>
                  <PersonIcon sx={{ fontSize: 16 }} />
                </Avatar>
                <Typography variant="body2">
                  By {template.author_username || `User ${template.author_id}`}
                </Typography>
              </Box>

              {/* Rating */}
              <Box display="flex" alignItems="center" gap={2} mb={2}>
                <Rating value={template.rating_avg} precision={0.1} readOnly />
                <Typography variant="body2" color="text.secondary">
                  {template.rating_avg.toFixed(1)} ({template.rating_count} reviews)
                </Typography>
              </Box>
            </Box>

            {/* Tags */}
            {template.tags && template.tags.length > 0 && (
              <Box mb={3}>
                <Typography variant="h6" gutterBottom>
                  Tags
                </Typography>
                <Box display="flex" flexWrap="wrap" gap={1}>
                  {template.tags.map((tag, index) => (
                    <Chip
                      key={index}
                      label={tag}
                      size="small"
                      variant="outlined"
                    />
                  ))}
                </Box>
              </Box>
            )}

            {/* Status-specific information */}
            {template.status === "rejected" && template.rejection_reason && (
              <Alert severity="error" sx={{ mb: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Rejection Reason:
                </Typography>
                <Typography variant="body2">
                  {template.rejection_reason}
                </Typography>
              </Alert>
            )}

            {template.status === "pending" && (
              <Alert severity="warning" sx={{ mb: 2 }}>
                This template is pending approval and is not yet available for download.
              </Alert>
            )}
          </TabPanel>

          {/* Docker Compose Tab */}
          <TabPanel value={tabValue} index={1}>
            <Box display="flex" alignItems="center" gap={1} mb={2}>
              <CodeIcon color="action" />
              <Typography variant="h6">
                Docker Compose Configuration
              </Typography>
            </Box>
            <Paper
              variant="outlined"
              sx={{
                p: 2,
                backgroundColor: "grey.50",
                maxHeight: 400,
                overflow: "auto",
              }}
            >
              <pre
                style={{
                  margin: 0,
                  fontFamily: "monospace",
                  fontSize: "0.875rem",
                  lineHeight: 1.5,
                  whiteSpace: "pre-wrap",
                  wordBreak: "break-word",
                }}
              >
                {template.docker_compose_yaml}
              </pre>
            </Paper>
          </TabPanel>

          {/* Reviews Tab */}
          <TabPanel value={tabValue} index={2}>
            {reviewsLoading ? (
              <LoadingState message="Loading reviews..." />
            ) : reviewsError ? (
              <ErrorDisplay
                error={reviewsError}
                onRetry={() => loadReviews(template.id)}
                title="Failed to load reviews"
              />
            ) : (
              <TemplateReviews
                templateId={template.id}
                reviews={reviews || []}
                onReviewAdded={() => loadReviews(template.id)}
                canAddReview={!!user && template.status === "approved"}
              />
            )}
          </TabPanel>
        </Box>
      </DialogContent>

      <DialogActions sx={{ p: 3 }}>
        <Button onClick={onClose}>Close</Button>
        {canDownload && (
          <Button
            variant="contained"
            startIcon={<DownloadIcon />}
            onClick={() => onDownload(template)}
          >
            Download Template
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default TemplateDetail;
