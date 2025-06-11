import React, { useState, useEffect } from "react";
import {
  Box,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Checkbox,
  Alert,
  Tooltip,
} from "@mui/material";
import {
  Visibility as ViewIcon,
  CheckCircle as ApproveIcon,
  Cancel as RejectIcon,
  SelectAll as SelectAllIcon,
} from "@mui/icons-material";
import { useApiCall } from "../../hooks/useApiCall";
import { LoadingState } from "../LoadingState";
import ErrorDisplay from "../ErrorDisplay";
import TemplateDetail from "./TemplateDetail";
import {
  fetchPendingTemplates,
  approveTemplate,
  Template,
  TemplateApproval,
} from "../../api/marketplace";

/**
 * Admin Template Queue Component
 *
 * Administrative interface for reviewing and approving pending templates.
 * Provides bulk operations and individual template management.
 *
 * Features:
 * - Pending templates list with metadata
 * - Individual approve/reject actions
 * - Bulk selection and operations
 * - Template preview functionality
 * - Rejection reason input
 * - Real-time status updates
 */
const AdminTemplateQueue: React.FC = () => {
  const [selectedTemplates, setSelectedTemplates] = useState<Set<number>>(
    new Set()
  );
  const [viewingTemplate, setViewingTemplate] = useState<Template | null>(null);
  const [rejectingTemplate, setRejectingTemplate] = useState<Template | null>(
    null
  );
  const [rejectionReason, setRejectionReason] = useState("");

  // API calls
  const {
    data: pendingTemplates,
    loading: templatesLoading,
    error: templatesError,
    execute: loadPendingTemplates,
  } = useApiCall<Template[]>(fetchPendingTemplates);

  const {
    loading: processingTemplate,
    error: processError,
    execute: processTemplate,
  } = useApiCall(approveTemplate, {
    showSuccessToast: true,
  });

  // Load pending templates on mount
  useEffect(() => {
    loadPendingTemplates();
  }, [loadPendingTemplates]);

  const handleSelectTemplate = (templateId: number) => {
    const newSelected = new Set(selectedTemplates);
    if (newSelected.has(templateId)) {
      newSelected.delete(templateId);
    } else {
      newSelected.add(templateId);
    }
    setSelectedTemplates(newSelected);
  };

  const handleSelectAll = () => {
    if (!pendingTemplates) return;

    if (selectedTemplates.size === pendingTemplates.length) {
      setSelectedTemplates(new Set());
    } else {
      setSelectedTemplates(new Set(pendingTemplates.map((t) => t.id)));
    }
  };

  const handleApproveTemplate = async (templateId: number) => {
    const approval: TemplateApproval = { approved: true };
    const result = await processTemplate(templateId, approval);
    if (result) {
      loadPendingTemplates(); // Refresh list
      setSelectedTemplates((prev) => {
        const newSet = new Set(prev);
        newSet.delete(templateId);
        return newSet;
      });
    }
  };

  const handleRejectTemplate = async () => {
    if (!rejectingTemplate || !rejectionReason.trim()) return;

    const approval: TemplateApproval = {
      approved: false,
      rejection_reason: rejectionReason.trim(),
    };

    const result = await processTemplate(rejectingTemplate.id, approval);
    if (result) {
      loadPendingTemplates(); // Refresh list
      setSelectedTemplates((prev) => {
        const newSet = new Set(prev);
        newSet.delete(rejectingTemplate.id);
        return newSet;
      });
      setRejectingTemplate(null);
      setRejectionReason("");
    }
  };

  const handleBulkApprove = async () => {
    const templateIds = Array.from(selectedTemplates);
    const approval: TemplateApproval = { approved: true };

    // Process templates sequentially to avoid rate limiting
    for (const templateId of templateIds) {
      await processTemplate(templateId, approval);
    }

    loadPendingTemplates();
    setSelectedTemplates(new Set());
  };

  const handleDownloadTemplate = (template: Template) => {
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

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  // Show loading state
  if (templatesLoading && !pendingTemplates) {
    return <LoadingState message="Loading pending templates..." />;
  }

  // Show error state
  if (templatesError && !pendingTemplates) {
    return (
      <ErrorDisplay
        error={templatesError}
        onRetry={loadPendingTemplates}
        title="Failed to load pending templates"
      />
    );
  }

  const templates = pendingTemplates || [];
  const hasSelected = selectedTemplates.size > 0;

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
          <Typography variant="h5" gutterBottom>
            Template Approval Queue
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {templates.length} templates pending review
          </Typography>
        </Box>

        {hasSelected && (
          <Box display="flex" gap={2}>
            <Button
              variant="contained"
              color="success"
              startIcon={<ApproveIcon />}
              onClick={handleBulkApprove}
              disabled={processingTemplate}
            >
              Approve Selected ({selectedTemplates.size})
            </Button>
          </Box>
        )}
      </Box>

      {processError && (
        <ErrorDisplay
          error={processError}
          title="Failed to process template"
          sx={{ mb: 3 }}
        />
      )}

      {/* Templates table */}
      {templates.length === 0 ? (
        <Alert severity="info">
          No templates pending approval. All caught up! 🎉
        </Alert>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell padding="checkbox">
                  <Checkbox
                    indeterminate={
                      hasSelected && selectedTemplates.size < templates.length
                    }
                    checked={
                      templates.length > 0 &&
                      selectedTemplates.size === templates.length
                    }
                    onChange={handleSelectAll}
                  />
                </TableCell>
                <TableCell>Template</TableCell>
                <TableCell>Author</TableCell>
                <TableCell>Category</TableCell>
                <TableCell>Submitted</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {templates.map((template) => (
                <TableRow key={template.id} hover>
                  <TableCell padding="checkbox">
                    <Checkbox
                      checked={selectedTemplates.has(template.id)}
                      onChange={() => handleSelectTemplate(template.id)}
                    />
                  </TableCell>
                  <TableCell>
                    <Box>
                      <Typography variant="subtitle2">
                        {template.name}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" noWrap>
                        {template.description.substring(0, 60)}...
                      </Typography>
                      <Box display="flex" gap={0.5} mt={0.5}>
                        <Chip label={`v${template.version}`} size="small" />
                        {template.tags.slice(0, 2).map((tag, index) => (
                          <Chip
                            key={index}
                            label={tag}
                            size="small"
                            variant="outlined"
                          />
                        ))}
                      </Box>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {template.author_username || `User ${template.author_id}`}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={template.category_name}
                      size="small"
                      color="primary"
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {formatDate(template.created_at)}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Box display="flex" gap={1}>
                      <Tooltip title="View Details">
                        <IconButton
                          size="small"
                          onClick={() => setViewingTemplate(template)}
                        >
                          <ViewIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Approve">
                        <span>
                          <IconButton
                            size="small"
                            color="success"
                            onClick={() => handleApproveTemplate(template.id)}
                            disabled={processingTemplate}
                            aria-label="Approve"
                          >
                            <ApproveIcon />
                          </IconButton>
                        </span>
                      </Tooltip>
                      <Tooltip title="Reject">
                        <span>
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => setRejectingTemplate(template)}
                            disabled={processingTemplate}
                            aria-label="Reject"
                          >
                            <RejectIcon />
                          </IconButton>
                        </span>
                      </Tooltip>
                    </Box>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Template detail modal */}
      {viewingTemplate && (
        <TemplateDetail
          template={viewingTemplate}
          open={!!viewingTemplate}
          onClose={() => setViewingTemplate(null)}
          onDownload={handleDownloadTemplate}
        />
      )}

      {/* Rejection dialog */}
      <Dialog
        open={!!rejectingTemplate}
        onClose={() => setRejectingTemplate(null)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Reject Template</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" paragraph>
            Please provide a reason for rejecting "{rejectingTemplate?.name}".
            This will help the author improve their submission.
          </Typography>
          <TextField
            fullWidth
            multiline
            rows={4}
            label="Rejection Reason"
            value={rejectionReason}
            onChange={(e) => setRejectionReason(e.target.value)}
            placeholder="Please explain why this template cannot be approved..."
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRejectingTemplate(null)}>Cancel</Button>
          <Button
            variant="contained"
            color="error"
            onClick={handleRejectTemplate}
            disabled={!rejectionReason.trim() || processingTemplate}
          >
            Reject Template
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AdminTemplateQueue;
