import React, { useState, useEffect } from "react";
import {
  Box,
  Grid,
  Typography,
  Button,
  Pagination,
  ToggleButton,
  ToggleButtonGroup,
  Alert,
  Fab,
  Tooltip,
} from "@mui/material";
import {
  GridView as GridViewIcon,
  ViewList as ListViewIcon,
  Add as AddIcon,
} from "@mui/icons-material";
import { useApiCall } from "../../hooks/useApiCall";
import LoadingState from "../LoadingState";
import ErrorDisplay from "../ErrorDisplay";
import TemplateCard from "./TemplateCard";
import TemplateSearch from "./TemplateSearch";
import TemplateDetail from "./TemplateDetail";
import TemplateSubmissionForm from "./TemplateSubmissionForm";
import {
  fetchTemplates,
  fetchCategories,
  Template,
  TemplateList,
  TemplateSearch as SearchParams,
  Category,
} from "../../api/marketplace";
import { useAuth } from "../../hooks/useAuth";

/**
 * Marketplace Home Component
 *
 * Main browsing interface for the Template Marketplace.
 * Provides search, filtering, and browsing capabilities.
 *
 * Features:
 * - Template search and filtering
 * - Grid/List view toggle
 * - Pagination for large result sets
 * - Template detail modal
 * - Template submission (authenticated users)
 * - Responsive design
 * - Loading states and error handling
 */
const MarketplaceHome: React.FC = () => {
  const { user } = useAuth();
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
  const [searchParams, setSearchParams] = useState<SearchParams>({
    page: 1,
    per_page: 20,
    sort_by: "created_at",
    sort_order: "desc",
  });
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(
    null
  );
  const [showSubmissionForm, setShowSubmissionForm] = useState(false);

  // API calls
  const {
    data: templateData,
    loading: templatesLoading,
    error: templatesError,
    execute: loadTemplates,
  } = useApiCall<TemplateList>(fetchTemplates);

  const {
    data: categories,
    loading: categoriesLoading,
    error: categoriesError,
    execute: loadCategories,
  } = useApiCall<Category[]>(fetchCategories);

  // Load initial data
  useEffect(() => {
    loadCategories();
  }, [loadCategories]);

  useEffect(() => {
    loadTemplates(searchParams);
  }, [loadTemplates, searchParams]);

  const handleSearch = (params: SearchParams) => {
    setSearchParams((prev) => ({
      ...prev,
      ...params,
      page: 1, // Reset to first page
    }));
  };

  const handlePageChange = (_: React.ChangeEvent<unknown>, page: number) => {
    setSearchParams((prev) => ({
      ...prev,
      page,
    }));
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
    // Refresh templates list
    loadTemplates(searchParams);
  };

  // Show loading state for initial load
  if (categoriesLoading && !categories) {
    return <LoadingState message="Loading marketplace..." />;
  }

  // Show error state
  if (categoriesError && !categories) {
    return (
      <ErrorDisplay
        error={categoriesError}
        onRetry={loadCategories}
        title="Failed to load marketplace"
      />
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box
        display="flex"
        justifyContent="space-between"
        alignItems="center"
        mb={3}
      >
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            Template Marketplace
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Discover and share Docker Compose templates for quick deployments
          </Typography>
        </Box>

        {user && (
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setShowSubmissionForm(true)}
            size="large"
          >
            Submit Template
          </Button>
        )}
      </Box>

      {/* Search and filters */}
      <TemplateSearch
        onSearch={handleSearch}
        categories={categories || []}
        loading={templatesLoading}
        initialParams={searchParams}
      />

      {/* View controls and results info */}
      <Box
        display="flex"
        justifyContent="space-between"
        alignItems="center"
        mb={3}
      >
        <Typography variant="body2" color="text.secondary">
          {templateData
            ? `Showing ${templateData.templates.length} of ${templateData.total} templates`
            : "Loading templates..."}
        </Typography>

        <ToggleButtonGroup
          value={viewMode}
          exclusive
          onChange={(_, value) => value && setViewMode(value)}
          size="small"
        >
          <ToggleButton value="grid">
            <GridViewIcon />
          </ToggleButton>
          <ToggleButton value="list">
            <ListViewIcon />
          </ToggleButton>
        </ToggleButtonGroup>
      </Box>

      {/* Templates grid/list */}
      {templatesLoading && !templateData ? (
        <LoadingState variant="skeleton" rows={6} />
      ) : templatesError ? (
        <ErrorDisplay
          error={templatesError}
          onRetry={() => loadTemplates(searchParams)}
          title="Failed to load templates"
        />
      ) : templateData && templateData.templates.length > 0 ? (
        <>
          <Grid container spacing={viewMode === "grid" ? 3 : 2}>
            {templateData.templates.map((template) => (
              <Grid
                item
                xs={12}
                sm={viewMode === "grid" ? 6 : 12}
                md={viewMode === "grid" ? 4 : 12}
                lg={viewMode === "grid" ? 3 : 12}
                key={template.id}
              >
                <TemplateCard
                  template={template}
                  onView={handleViewTemplate}
                  onDownload={handleDownloadTemplate}
                  compact={viewMode === "list"}
                />
              </Grid>
            ))}
          </Grid>

          {/* Pagination */}
          {templateData.pages > 1 && (
            <Box display="flex" justifyContent="center" mt={4}>
              <Pagination
                count={templateData.pages}
                page={templateData.page}
                onChange={handlePageChange}
                color="primary"
                size="large"
                showFirstButton
                showLastButton
              />
            </Box>
          )}
        </>
      ) : (
        <Alert severity="info" sx={{ mt: 3 }}>
          No templates found matching your criteria. Try adjusting your search
          filters.
        </Alert>
      )}

      {/* Floating action button for mobile */}
      {user && (
        <Tooltip title="Submit Template">
          <Fab
            color="primary"
            sx={{
              position: "fixed",
              bottom: 16,
              right: 16,
              display: { xs: "flex", md: "none" },
            }}
            onClick={() => setShowSubmissionForm(true)}
          >
            <AddIcon />
          </Fab>
        </Tooltip>
      )}

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
  );
};

export default MarketplaceHome;
