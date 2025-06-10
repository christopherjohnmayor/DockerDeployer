import React from "react";
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Chip,
  Box,
  Button,
  Rating,
  Avatar,
  IconButton,
  Tooltip,
} from "@mui/material";
import {
  Download as DownloadIcon,
  Visibility as ViewIcon,
  Person as PersonIcon,
  Schedule as ScheduleIcon,
} from "@mui/icons-material";
import { Template } from "../../api/marketplace";

interface TemplateCardProps {
  template: Template;
  onView: (template: Template) => void;
  onDownload?: (template: Template) => void;
  showAuthor?: boolean;
  compact?: boolean;
}

/**
 * Template Card Component
 * 
 * Displays a template in card format with key information and actions.
 * Used in marketplace browsing, search results, and user dashboards.
 * 
 * Features:
 * - Template name, description, and metadata
 * - Rating display with star count
 * - Category and tags display
 * - Author information (optional)
 * - Download count and status indicators
 * - Action buttons (view, download)
 * - Responsive design with compact mode
 */
const TemplateCard: React.FC<TemplateCardProps> = ({
  template,
  onView,
  onDownload,
  showAuthor = true,
  compact = false,
}) => {
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
    return new Date(dateString).toLocaleDateString();
  };

  const truncateDescription = (text: string, maxLength: number = 120) => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + "...";
  };

  return (
    <Card
      sx={{
        height: "100%",
        display: "flex",
        flexDirection: "column",
        transition: "transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out",
        "&:hover": {
          transform: "translateY(-2px)",
          boxShadow: 4,
        },
      }}
    >
      <CardContent sx={{ flexGrow: 1, pb: compact ? 1 : 2 }}>
        {/* Header with title and status */}
        <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={1}>
          <Typography
            variant={compact ? "subtitle1" : "h6"}
            component="h3"
            sx={{
              fontWeight: 600,
              lineHeight: 1.2,
              overflow: "hidden",
              textOverflow: "ellipsis",
              display: "-webkit-box",
              WebkitLineClamp: 2,
              WebkitBoxOrient: "vertical",
            }}
          >
            {template.name}
          </Typography>
          <Chip
            label={template.status}
            size="small"
            color={getStatusColor(template.status) as any}
            sx={{ ml: 1, flexShrink: 0 }}
          />
        </Box>

        {/* Description */}
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{
            mb: compact ? 1 : 2,
            overflow: "hidden",
            textOverflow: "ellipsis",
            display: "-webkit-box",
            WebkitLineClamp: compact ? 2 : 3,
            WebkitBoxOrient: "vertical",
            minHeight: compact ? "2.4em" : "3.6em",
          }}
        >
          {truncateDescription(template.description, compact ? 80 : 120)}
        </Typography>

        {/* Category and Version */}
        <Box display="flex" alignItems="center" gap={1} mb={compact ? 1 : 2}>
          {template.category_name && (
            <Chip
              label={template.category_name}
              size="small"
              variant="outlined"
              color="primary"
            />
          )}
          {template.version && (
            <Chip
              label={`v${template.version}`}
              size="small"
              variant="outlined"
            />
          )}
        </Box>

        {/* Tags */}
        {template.tags && template.tags.length > 0 && (
          <Box display="flex" flexWrap="wrap" gap={0.5} mb={compact ? 1 : 2}>
            {template.tags.slice(0, compact ? 2 : 3).map((tag, index) => (
              <Chip
                key={index}
                label={tag}
                size="small"
                variant="outlined"
                sx={{ fontSize: "0.7rem", height: 20 }}
              />
            ))}
            {template.tags.length > (compact ? 2 : 3) && (
              <Chip
                label={`+${template.tags.length - (compact ? 2 : 3)}`}
                size="small"
                variant="outlined"
                sx={{ fontSize: "0.7rem", height: 20 }}
              />
            )}
          </Box>
        )}

        {/* Rating and Downloads */}
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={1}>
          <Box display="flex" alignItems="center" gap={1}>
            <Rating
              value={template.rating_avg}
              precision={0.1}
              size="small"
              readOnly
            />
            <Typography variant="caption" color="text.secondary">
              ({template.rating_count})
            </Typography>
          </Box>
          <Box display="flex" alignItems="center" gap={0.5}>
            <DownloadIcon sx={{ fontSize: 16 }} color="action" />
            <Typography variant="caption" color="text.secondary">
              {template.downloads}
            </Typography>
          </Box>
        </Box>

        {/* Author and Date */}
        {showAuthor && !compact && (
          <Box display="flex" alignItems="center" justifyContent="space-between">
            <Box display="flex" alignItems="center" gap={1}>
              <Avatar sx={{ width: 20, height: 20 }}>
                <PersonIcon sx={{ fontSize: 14 }} />
              </Avatar>
              <Typography variant="caption" color="text.secondary">
                {template.author_username || `User ${template.author_id}`}
              </Typography>
            </Box>
            <Box display="flex" alignItems="center" gap={0.5}>
              <ScheduleIcon sx={{ fontSize: 14 }} color="action" />
              <Typography variant="caption" color="text.secondary">
                {formatDate(template.created_at)}
              </Typography>
            </Box>
          </Box>
        )}
      </CardContent>

      {/* Actions */}
      <CardActions sx={{ pt: 0, px: 2, pb: 2 }}>
        <Button
          size="small"
          startIcon={<ViewIcon />}
          onClick={() => onView(template)}
          sx={{ mr: 1 }}
        >
          View Details
        </Button>
        {onDownload && template.status === "approved" && (
          <Tooltip title="Download Template">
            <IconButton
              size="small"
              onClick={() => onDownload(template)}
              color="primary"
            >
              <DownloadIcon />
            </IconButton>
          </Tooltip>
        )}
      </CardActions>
    </Card>
  );
};

export default TemplateCard;
