import React, { useEffect, useState } from "react";
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  CircularProgress,
  Alert,
  Stack,
  TextField,
  InputAdornment,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent,
  Chip,
  Grid,
  Card,
  CardContent,
  CardActions,
  Tabs,
  Tab,
} from "@mui/material";
import SearchIcon from "@mui/icons-material/Search";
import InfoIcon from "@mui/icons-material/Info";

import axios from "axios";

interface Template {
  name: string;
  description?: string;
  version?: string;
  tags?: string[];
  author?: string;
  category?: string;
  complexity?: "simple" | "medium" | "advanced";
  [key: string]: unknown;
}

type CustomizationType = Record<string, string>;

interface TemplateDetailProps {
  template: Template | null;
  open: boolean;
  onClose: () => void;
  onDeploy: (templateName: string, customizations?: CustomizationType) => void;
}

const TemplateDetail: React.FC<TemplateDetailProps> = ({
  template,
  open,
  onClose,
  onDeploy,
}) => {
  const [tabValue, setTabValue] = useState(0);
  const [customizations, setCustomizations] = useState<CustomizationType>({});

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleCustomizationChange = (field: string, value: string) => {
    setCustomizations((prev: CustomizationType) => ({
      ...prev,
      [field]: value,
    }));
  };

  if (!template) return null;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Typography variant="h6">{template.name}</Typography>
          <Box>
            {template.version && (
              <Chip
                label={`v${template.version}`}
                size="small"
                color="primary"
                variant="outlined"
                sx={{ mr: 1 }}
              />
            )}
            {template.complexity && (
              <Chip
                label={template.complexity}
                size="small"
                color={
                  template.complexity === "simple"
                    ? "success"
                    : template.complexity === "medium"
                      ? "warning"
                      : "error"
                }
              />
            )}
          </Box>
        </Box>
      </DialogTitle>
      <DialogContent dividers>
        <Tabs value={tabValue} onChange={handleTabChange} sx={{ mb: 2 }}>
          <Tab label="Overview" />
          <Tab label="Configuration" />
          <Tab label="Preview" />
        </Tabs>

        {tabValue === 0 && (
          <Box>
            <Typography variant="body1" paragraph>
              {template.description || "No description available."}
            </Typography>
            <Typography variant="subtitle2" gutterBottom>
              Tags
            </Typography>
            <Box display="flex" flexWrap="wrap" gap={1} mb={2}>
              {template.tags?.map((tag) => (
                <Chip key={tag} label={tag} size="small" />
              )) || <Typography variant="body2">No tags available</Typography>}
            </Box>
            {template.author && (
              <Typography variant="body2">Author: {template.author}</Typography>
            )}
          </Box>
        )}

        {tabValue === 1 && (
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Customize Deployment
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Stack Name"
                  fullWidth
                  margin="normal"
                  variant="outlined"
                  defaultValue={`${template.name.toLowerCase()}-stack`}
                  onChange={(e) =>
                    handleCustomizationChange("stackName", e.target.value)
                  }
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth margin="normal">
                  <InputLabel>Environment</InputLabel>
                  <Select
                    label="Environment"
                    defaultValue="development"
                    onChange={(e) =>
                      handleCustomizationChange("environment", e.target.value)
                    }
                  >
                    <MenuItem value="development">Development</MenuItem>
                    <MenuItem value="staging">Staging</MenuItem>
                    <MenuItem value="production">Production</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              {/* Additional customization fields would be added here based on template */}
            </Grid>
          </Box>
        )}

        {tabValue === 2 && (
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Configuration Preview
            </Typography>
            <Paper
              variant="outlined"
              sx={{
                p: 2,
                bgcolor: "#f5f5f5",
                fontFamily: "monospace",
                fontSize: "0.9em",
                whiteSpace: "pre-wrap",
                overflowX: "auto",
                maxHeight: 300,
              }}
            >
              {`version: '3'
services:
  # This is a preview of how your ${template.name} stack will be configured
  # Actual configuration may vary based on customizations

  # Example services for ${template.name}
  web:
    image: nginx:latest
    ports:
      - "80:80"
    volumes:
      - ./app:/var/www/html
    depends_on:
      - app

  app:
    image: php:8.0-fpm
    volumes:
      - ./app:/var/www/html

  db:
    image: mysql:8.0
    environment:
      - MYSQL_ROOT_PASSWORD=example
      - MYSQL_DATABASE=app`}
            </Paper>
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          variant="contained"
          color="primary"
          onClick={() => onDeploy(template.name, customizations)}
        >
          Deploy Stack
        </Button>
      </DialogActions>
    </Dialog>
  );
};

const Templates: React.FC = () => {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [filteredTemplates, setFilteredTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [deploying, setDeploying] = useState<string | null>(null);
  const [deploySuccess, setDeploySuccess] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [categoryFilter, setCategoryFilter] = useState<string>("all");
  const [complexityFilter, setComplexityFilter] = useState<string>("all");
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(
    null
  );
  const [detailOpen, setDetailOpen] = useState(false);
  const [viewMode] = useState<"table" | "grid">("grid");

  useEffect(() => {
    const fetchTemplates = async () => {
      setLoading(true);
      setError(null);
      try {
        const resp = await axios.get("/api/templates");
        // Enhance templates with additional metadata for UI
        const enhancedTemplates = resp.data.map((tpl: Template) => ({
          ...tpl,
          // Add default values if not provided by API
          version: tpl.version || "1.0",
          category: tpl.category || "web",
          complexity: tpl.complexity || "medium",
          tags: tpl.tags || [],
        }));
        setTemplates(enhancedTemplates);
        setFilteredTemplates(enhancedTemplates);
      } catch (err: unknown) {
        const error = err as {
          response?: { data?: { detail?: string } };
          message?: string;
        };
        setError(
          error?.response?.data?.detail ||
            error?.message ||
            "Failed to fetch templates."
        );
      } finally {
        setLoading(false);
      }
    };
    fetchTemplates();
  }, []);

  useEffect(() => {
    // Apply filters whenever search term or filters change
    let result = templates;

    // Apply search filter
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      result = result.filter(
        (template) =>
          template.name.toLowerCase().includes(term) ||
          template.description?.toLowerCase().includes(term) ||
          template.tags?.some((tag) => tag.toLowerCase().includes(term))
      );
    }

    // Apply category filter
    if (categoryFilter !== "all") {
      result = result.filter(
        (template) => template.category === categoryFilter
      );
    }

    // Apply complexity filter
    if (complexityFilter !== "all") {
      result = result.filter(
        (template) => template.complexity === complexityFilter
      );
    }

    setFilteredTemplates(result);
  }, [searchTerm, categoryFilter, complexityFilter, templates]);

  const handleCategoryChange = (event: SelectChangeEvent) => {
    setCategoryFilter(event.target.value);
  };

  const handleComplexityChange = (event: SelectChangeEvent) => {
    setComplexityFilter(event.target.value);
  };

  const handleViewDetails = (template: Template) => {
    setSelectedTemplate(template);
    setDetailOpen(true);
  };

  const handleCloseDetail = () => {
    setDetailOpen(false);
  };

  const handleDeploy = async (
    templateName: string,
    customizations?: Record<string, string>
  ) => {
    setDeploying(templateName);
    setDeploySuccess(null);
    setDetailOpen(false);

    try {
      // Include customizations in the request if provided
      const payload = {
        template_name: templateName,
        ...(customizations && { customizations }),
      };

      await axios.post("/api/templates/deploy", payload);
      setDeploySuccess(`Template "${templateName}" deployed successfully!`);
    } catch (err: unknown) {
      const error = err as {
        response?: { data?: { detail?: string } };
        message?: string;
      };
      setError(
        error?.response?.data?.detail ||
          error?.message ||
          `Failed to deploy template "${templateName}".`
      );
    } finally {
      setDeploying(null);
    }
  };

  const renderGridView = () => (
    <Grid container spacing={3}>
      {filteredTemplates.map((template) => (
        <Grid item xs={12} sm={6} md={4} key={template.name}>
          <Card>
            <CardContent>
              <Box
                display="flex"
                justifyContent="space-between"
                alignItems="flex-start"
              >
                <Typography variant="h6" gutterBottom>
                  {template.name}
                </Typography>
                {template.complexity && (
                  <Chip
                    label={template.complexity}
                    size="small"
                    color={
                      template.complexity === "simple"
                        ? "success"
                        : template.complexity === "medium"
                          ? "warning"
                          : "error"
                    }
                  />
                )}
              </Box>
              <Typography
                variant="body2"
                color="text.secondary"
                paragraph
                sx={{
                  height: 60,
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  display: "-webkit-box",
                  WebkitLineClamp: 3,
                  WebkitBoxOrient: "vertical",
                }}
              >
                {template.description || "No description available."}
              </Typography>
              <Box display="flex" flexWrap="wrap" gap={1} mb={2}>
                {template.version && (
                  <Chip
                    label={`v${template.version}`}
                    size="small"
                    color="primary"
                    variant="outlined"
                  />
                )}
                {template.tags
                  ?.slice(0, 3)
                  .map((tag) => <Chip key={tag} label={tag} size="small" />)}
                {template.tags && template.tags.length > 3 && (
                  <Chip
                    label={`+${template.tags.length - 3}`}
                    size="small"
                    variant="outlined"
                  />
                )}
              </Box>
              {template.author && (
                <Typography variant="caption" display="block">
                  Author: {template.author}
                </Typography>
              )}
            </CardContent>
            <CardActions>
              <Button
                size="small"
                color="primary"
                variant="contained"
                disabled={!!deploying}
                onClick={() => handleDeploy(template.name)}
              >
                {deploying === template.name ? (
                  <CircularProgress size={18} color="inherit" />
                ) : (
                  "Deploy"
                )}
              </Button>
              <Button
                size="small"
                startIcon={<InfoIcon />}
                onClick={() => handleViewDetails(template)}
              >
                Details
              </Button>
            </CardActions>
          </Card>
        </Grid>
      ))}
    </Grid>
  );

  const renderTableView = () => (
    <TableContainer>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Name</TableCell>
            <TableCell>Description</TableCell>
            <TableCell align="right">Actions</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {filteredTemplates.map((tpl) => (
            <TableRow key={tpl.name}>
              <TableCell>{tpl.name}</TableCell>
              <TableCell>{tpl.description || "-"}</TableCell>
              <TableCell align="right">
                <Stack direction="row" spacing={1} justifyContent="flex-end">
                  <Button
                    variant="contained"
                    size="small"
                    disabled={!!deploying}
                    onClick={() => handleDeploy(tpl.name)}
                  >
                    {deploying === tpl.name ? (
                      <CircularProgress size={18} color="inherit" />
                    ) : (
                      "Deploy"
                    )}
                  </Button>
                  <Button size="small" onClick={() => handleViewDetails(tpl)}>
                    Details
                  </Button>
                </Stack>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );

  return (
    <Box sx={{ p: 3 }}>
      <Paper elevation={2} sx={{ p: 4 }}>
        <Typography variant="h4" gutterBottom>
          Templates
        </Typography>
        <Typography variant="body1" color="text.secondary" gutterBottom>
          Browse and deploy pre-built Docker stack templates.
        </Typography>

        <Paper sx={{ p: 2, mb: 3 }}>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                placeholder="Search templates..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon />
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <FormControl fullWidth>
                <InputLabel>Category</InputLabel>
                <Select
                  value={categoryFilter}
                  label="Category"
                  onChange={handleCategoryChange}
                >
                  <MenuItem value="all">All Categories</MenuItem>
                  <MenuItem value="web">Web Applications</MenuItem>
                  <MenuItem value="database">Databases</MenuItem>
                  <MenuItem value="cms">Content Management</MenuItem>
                  <MenuItem value="dev">Development Tools</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={3}>
              <FormControl fullWidth>
                <InputLabel>Complexity</InputLabel>
                <Select
                  value={complexityFilter}
                  label="Complexity"
                  onChange={handleComplexityChange}
                >
                  <MenuItem value="all">All Levels</MenuItem>
                  <MenuItem value="simple">Simple</MenuItem>
                  <MenuItem value="medium">Medium</MenuItem>
                  <MenuItem value="advanced">Advanced</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </Paper>

        {loading ? (
          <Box
            display="flex"
            justifyContent="center"
            alignItems="center"
            minHeight={120}
          >
            <CircularProgress />
          </Box>
        ) : error ? (
          <Alert severity="error" sx={{ my: 2 }}>
            {error}
          </Alert>
        ) : (
          <>
            {deploySuccess && (
              <Alert severity="success" sx={{ mb: 2 }}>
                {deploySuccess}
              </Alert>
            )}

            {filteredTemplates.length === 0 ? (
              <Alert severity="info">
                No templates match your search criteria.
              </Alert>
            ) : viewMode === "grid" ? (
              renderGridView()
            ) : (
              renderTableView()
            )}
          </>
        )}
      </Paper>

      <TemplateDetail
        template={selectedTemplate}
        open={detailOpen}
        onClose={handleCloseDetail}
        onDeploy={handleDeploy}
      />
    </Box>
  );
};

export default Templates;
