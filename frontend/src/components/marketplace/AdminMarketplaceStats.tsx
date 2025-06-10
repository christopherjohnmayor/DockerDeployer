import React, { useEffect } from "react";
import {
  Box,
  Typography,
  Grid,
  Paper,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  Chip,
  LinearProgress,
} from "@mui/material";
import {
  TrendingUp as TrendingUpIcon,
  Category as CategoryIcon,
  Star as StarIcon,
  Download as DownloadIcon,
  Schedule as ScheduleIcon,
} from "@mui/icons-material";
import { useApiCall } from "../../hooks/useApiCall";
import { LoadingState } from "../LoadingState";
import ErrorDisplay from "../ErrorDisplay";
import { fetchMarketplaceStats, MarketplaceStats } from "../../api/marketplace";

/**
 * Admin Marketplace Stats Component
 * 
 * Displays comprehensive marketplace analytics and statistics for administrators.
 * Provides insights into template submissions, approvals, and user engagement.
 * 
 * Features:
 * - Key metrics overview (templates, reviews, downloads)
 * - Category distribution analysis
 * - Recent activity timeline
 * - Template status breakdown
 * - Performance indicators
 * - Visual progress indicators
 */
const AdminMarketplaceStats: React.FC = () => {
  // API call for marketplace stats
  const {
    data: stats,
    loading: statsLoading,
    error: statsError,
    execute: loadStats,
  } = useApiCall<MarketplaceStats>(fetchMarketplaceStats);

  // Load stats on component mount
  useEffect(() => {
    loadStats();
  }, [loadStats]);

  const formatNumber = (num: number) => {
    if (num >= 1000) {
      return (num / 1000).toFixed(1) + "k";
    }
    return num.toString();
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const getApprovalRate = () => {
    if (!stats || stats.total_templates === 0) return 0;
    return Math.round((stats.approved_templates / stats.total_templates) * 100);
  };

  const getPendingRate = () => {
    if (!stats || stats.total_templates === 0) return 0;
    return Math.round((stats.pending_templates / stats.total_templates) * 100);
  };

  // Show loading state
  if (statsLoading && !stats) {
    return <LoadingState message="Loading marketplace statistics..." />;
  }

  // Show error state
  if (statsError && !stats) {
    return (
      <ErrorDisplay
        error={statsError}
        onRetry={loadStats}
        title="Failed to load marketplace statistics"
      />
    );
  }

  if (!stats) {
    return null;
  }

  return (
    <Box>
      {/* Header */}
      <Box mb={4}>
        <Typography variant="h5" gutterBottom>
          Marketplace Analytics
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Overview of template marketplace performance and user engagement
        </Typography>
      </Box>

      {/* Key Metrics */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="h4" color="primary">
                    {formatNumber(stats.total_templates)}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Templates
                  </Typography>
                </Box>
                <TrendingUpIcon color="primary" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="h4" color="success.main">
                    {formatNumber(stats.approved_templates)}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Approved
                  </Typography>
                </Box>
                <CategoryIcon color="success" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="h4" color="warning.main">
                    {formatNumber(stats.pending_templates)}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Pending Review
                  </Typography>
                </Box>
                <ScheduleIcon color="warning" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="h4" color="info.main">
                    {formatNumber(stats.total_downloads)}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Downloads
                  </Typography>
                </Box>
                <DownloadIcon color="info" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Template Status Breakdown */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Template Status Overview
            </Typography>
            
            <Box mb={3}>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                <Typography variant="body2">Approval Rate</Typography>
                <Typography variant="body2" fontWeight="bold">
                  {getApprovalRate()}%
                </Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={getApprovalRate()}
                color="success"
                sx={{ height: 8, borderRadius: 4 }}
              />
            </Box>

            <Box mb={3}>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                <Typography variant="body2">Pending Review</Typography>
                <Typography variant="body2" fontWeight="bold">
                  {getPendingRate()}%
                </Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={getPendingRate()}
                color="warning"
                sx={{ height: 8, borderRadius: 4 }}
              />
            </Box>

            <Grid container spacing={2}>
              <Grid item xs={4}>
                <Box textAlign="center">
                  <Typography variant="h6" color="success.main">
                    {stats.approved_templates}
                  </Typography>
                  <Typography variant="caption">Approved</Typography>
                </Box>
              </Grid>
              <Grid item xs={4}>
                <Box textAlign="center">
                  <Typography variant="h6" color="warning.main">
                    {stats.pending_templates}
                  </Typography>
                  <Typography variant="caption">Pending</Typography>
                </Box>
              </Grid>
              <Grid item xs={4}>
                <Box textAlign="center">
                  <Typography variant="h6" color="error.main">
                    {stats.rejected_templates}
                  </Typography>
                  <Typography variant="caption">Rejected</Typography>
                </Box>
              </Grid>
            </Grid>
          </Paper>
        </Grid>

        {/* Reviews and Rating */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              User Engagement
            </Typography>
            
            <Box display="flex" alignItems="center" gap={2} mb={2}>
              <StarIcon color="warning" />
              <Box>
                <Typography variant="h5">
                  {stats.average_rating.toFixed(1)}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Average Rating
                </Typography>
              </Box>
            </Box>

            <Box display="flex" alignItems="center" gap={2} mb={2}>
              <Typography variant="h5" color="primary">
                {formatNumber(stats.total_reviews)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Reviews
              </Typography>
            </Box>

            <Box display="flex" alignItems="center" gap={2}>
              <Typography variant="h5" color="info.main">
                {formatNumber(stats.total_downloads)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Downloads
              </Typography>
            </Box>
          </Paper>
        </Grid>

        {/* Top Categories */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Popular Categories
            </Typography>
            
            {stats.top_categories.length === 0 ? (
              <Typography variant="body2" color="text.secondary">
                No categories data available
              </Typography>
            ) : (
              <List dense>
                {stats.top_categories.map((category, index) => (
                  <ListItem key={index} sx={{ px: 0 }}>
                    <ListItemText
                      primary={category.category_name}
                      secondary={`${category.template_count} templates`}
                    />
                    <Chip
                      label={category.template_count}
                      size="small"
                      color="primary"
                      variant="outlined"
                    />
                  </ListItem>
                ))}
              </List>
            )}
          </Paper>
        </Grid>

        {/* Recent Activity */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Recent Activity
            </Typography>
            
            {stats.recent_activity.length === 0 ? (
              <Typography variant="body2" color="text.secondary">
                No recent activity
              </Typography>
            ) : (
              <List dense>
                {stats.recent_activity.map((activity, index) => (
                  <ListItem key={index} sx={{ px: 0 }}>
                    <ListItemText
                      primary={activity.template_name}
                      secondary={
                        <Box display="flex" alignItems="center" gap={1}>
                          <Chip
                            label={activity.action}
                            size="small"
                            color={
                              activity.action === "approved"
                                ? "success"
                                : activity.action === "rejected"
                                ? "error"
                                : "default"
                            }
                          />
                          <Typography variant="caption">
                            {formatDate(activity.timestamp)}
                          </Typography>
                        </Box>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default AdminMarketplaceStats;
