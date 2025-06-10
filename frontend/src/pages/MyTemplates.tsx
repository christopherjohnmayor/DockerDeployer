import React, { useState, useEffect } from "react";
import {
  Box,
  Typography,
  Button,
  Grid,
  Alert,
  Tabs,
  Tab,
  Paper,
  Container,
} from "@mui/material";
import {
  Add as AddIcon,
  Pending as PendingIcon,
  CheckCircle as ApprovedIcon,
  Cancel as RejectedIcon,
} from "@mui/icons-material";
import { useApiCall } from "../hooks/useApiCall";
import { LoadingState } from "../components/LoadingState";
import ErrorDisplay from "../components/ErrorDisplay";
import TemplateCard from "../components/marketplace/TemplateCard";
import TemplateDetail from "../components/marketplace/TemplateDetail";
import TemplateSubmissionForm from "../components/marketplace/TemplateSubmissionForm";
import {
  fetchMyTemplates,
  fetchCategories,
  Template,
  Category,
} from "../api/marketplace";

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
      id={`templates-tabpanel-${index}`}
      aria-labelledby={`templates-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

/**
 * My Templates Page Component
 * 
 * User dashboard for managing submitted templates.
 * Shows templates organized by status with management capabilities.
 * 
 * Features:
 * - Templates organized by status (all, pending, approved, rejected)
 * - Template submission functionality
 * - Template detail viewing
 * - Status-based filtering with tabs
 * - Template statistics display
 * - Responsive grid layout
 */
const MyTemplates: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null);
  const [showSubmissionForm, setShowSubmissionForm] = useState(false);

  // API calls
  const {
    data: templates,
    loading: templatesLoading,
    error: templatesError,
    execute: loadTemplates,
  } = useApiCall<Template[]>(fetchMyTemplates);

  const {
    data: categories,
    loading: categoriesLoading,
    execute: loadCategories,
  } = useApiCall<Category[]>(fetchCategories);

  // Load data on component mount
  useEffect(() => {
    loadTemplates();
    loadCategories();
  }, [loadTemplates, loadCategories]);

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleViewTemplate = (template: Template) => {
    setSelectedTemplate(template);
  };

  const handleDownloadTemplate = (template: Template) => {
    // Create a downloadable file
    const blob = new Blob([template.docker_compose_yaml], {
      type: "text/yaml",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${template.name.replace(/\s+/g, "-").toLowerCase()}-docker-compose.yml`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleTemplateSubmitted = () => {
    setShowSubmissionForm(false);
    loadTemplates(); // Refresh templates list
  };

  const filterTemplatesByStatus = (status?: string) => {
    if (!templates) return [];
    if (!status) return templates;
    return templates.filter(template => template.status === status);
  };

  const getTemplateStats = () => {
    if (!templates) return { total: 0, pending: 0, approved: 0, rejected: 0 };
    
    return {
      total: templates.length,
      pending: templates.filter(t => t.status === "pending").length,
      approved: templates.filter(t => t.status === "approved").length,
      rejected: templates.filter(t => t.status === "rejected").length,
    };
  };

  const renderTemplateGrid = (filteredTemplates: Template[]) => {
    if (filteredTemplates.length === 0) {
      return (
        <Alert severity="info">
          No templates found in this category.
          {tabValue === 0 && " Get started by submitting your first template!"}
        </Alert>
      );
    }

    return (
      <Grid container spacing={3}>
        {filteredTemplates.map((template) => (
          <Grid item xs={12} sm={6} md={4} lg={3} key={template.id}>
            <TemplateCard
              template={template}
              onView={handleViewTemplate}
              onDownload={template.status === "approved" ? handleDownloadTemplate : undefined}
              showAuthor={false} // Don't show author for own templates
            />
          </Grid>
        ))}
      </Grid>
    );
  };

  const stats = getTemplateStats();

  // Show loading state
  if (templatesLoading && !templates) {
    return (
      <Container maxWidth="xl">
        <LoadingState message="Loading your templates..." />
      </Container>
    );
  }

  // Show error state
  if (templatesError && !templates) {
    return (
      <Container maxWidth="xl">
        <ErrorDisplay
          error={templatesError}
          onRetry={loadTemplates}
          title="Failed to load your templates"
        />
      </Container>
    );
  }

  return (
    <Container maxWidth="xl">
      <Box py={3}>
        {/* Header */}
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
          <Box>
            <Typography variant="h4" component="h1" gutterBottom>
              My Templates
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Manage your submitted templates and track their approval status
            </Typography>
          </Box>
          
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setShowSubmissionForm(true)}
            size="large"
          >
            Submit New Template
          </Button>
        </Box>

        {/* Statistics */}
        <Grid container spacing={2} mb={4}>
          <Grid item xs={6} sm={3}>
            <Paper sx={{ p: 2, textAlign: "center" }}>
              <Typography variant="h4" color="primary">
                {stats.total}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Templates
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Paper sx={{ p: 2, textAlign: "center" }}>
              <Typography variant="h4" color="warning.main">
                {stats.pending}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Pending Review
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Paper sx={{ p: 2, textAlign: "center" }}>
              <Typography variant="h4" color="success.main">
                {stats.approved}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Approved
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Paper sx={{ p: 2, textAlign: "center" }}>
              <Typography variant="h4" color="error.main">
                {stats.rejected}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Rejected
              </Typography>
            </Paper>
          </Grid>
        </Grid>

        {/* Tabs */}
        <Paper sx={{ mb: 3 }}>
          <Tabs
            value={tabValue}
            onChange={handleTabChange}
            sx={{ borderBottom: 1, borderColor: "divider" }}
          >
            <Tab label={`All (${stats.total})`} />
            <Tab
              label={`Pending (${stats.pending})`}
              icon={<PendingIcon />}
              iconPosition="start"
            />
            <Tab
              label={`Approved (${stats.approved})`}
              icon={<ApprovedIcon />}
              iconPosition="start"
            />
            <Tab
              label={`Rejected (${stats.rejected})`}
              icon={<RejectedIcon />}
              iconPosition="start"
            />
          </Tabs>

          {/* Tab Panels */}
          <TabPanel value={tabValue} index={0}>
            {renderTemplateGrid(filterTemplatesByStatus())}
          </TabPanel>
          <TabPanel value={tabValue} index={1}>
            {renderTemplateGrid(filterTemplatesByStatus("pending"))}
          </TabPanel>
          <TabPanel value={tabValue} index={2}>
            {renderTemplateGrid(filterTemplatesByStatus("approved"))}
          </TabPanel>
          <TabPanel value={tabValue} index={3}>
            {renderTemplateGrid(filterTemplatesByStatus("rejected"))}
          </TabPanel>
        </Paper>

        {/* Template detail modal */}
        {selectedTemplate && (
          <TemplateDetail
            template={selectedTemplate}
            open={!!selectedTemplate}
            onClose={() => setSelectedTemplate(null)}
            onDownload={handleDownloadTemplate}
          />
        )}

        {/* Template submission form */}
        {showSubmissionForm && (
          <TemplateSubmissionForm
            open={showSubmissionForm}
            onClose={() => setShowSubmissionForm(false)}
            onSubmitted={handleTemplateSubmitted}
            categories={categories || []}
          />
        )}
      </Box>
    </Container>
  );
};

export default MyTemplates;
