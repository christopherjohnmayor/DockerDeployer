/**
 * Container Health Score Visualization Component
 * 
 * Displays container health scores with color-coded indicators (0-100 scale)
 * including component breakdowns and recommendations.
 */

import React from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  CircularProgress,
  Chip,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  useTheme,
  Alert,
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  TrendingFlat as TrendingFlatIcon,
} from '@mui/icons-material';
import { HealthScore } from '../types/enhancedMetrics';

interface ContainerHealthScoreVisualizationProps {
  healthScore: HealthScore | null;
  loading?: boolean;
  error?: string;
  showRecommendations?: boolean;
  showComponentBreakdown?: boolean;
  compact?: boolean;
}

const ContainerHealthScoreVisualization: React.FC<ContainerHealthScoreVisualizationProps> = ({
  healthScore,
  loading = false,
  error,
  showRecommendations = true,
  showComponentBreakdown = true,
  compact = false,
}) => {
  const theme = useTheme();

  // Get health status color and icon
  const getHealthStatusDisplay = (score: number, status: string) => {
    switch (status) {
      case 'excellent':
        return {
          color: theme.palette.success.main,
          backgroundColor: theme.palette.success.light,
          icon: <CheckCircleIcon />,
          label: 'Excellent',
        };
      case 'good':
        return {
          color: theme.palette.info.main,
          backgroundColor: theme.palette.info.light,
          icon: <InfoIcon />,
          label: 'Good',
        };
      case 'warning':
        return {
          color: theme.palette.warning.main,
          backgroundColor: theme.palette.warning.light,
          icon: <WarningIcon />,
          label: 'Warning',
        };
      case 'critical':
        return {
          color: theme.palette.error.main,
          backgroundColor: theme.palette.error.light,
          icon: <ErrorIcon />,
          label: 'Critical',
        };
      default:
        return {
          color: theme.palette.grey[500],
          backgroundColor: theme.palette.grey[100],
          icon: <InfoIcon />,
          label: 'Unknown',
        };
    }
  };

  // Get component health color
  const getComponentHealthColor = (score: number) => {
    if (score >= 80) return theme.palette.success.main;
    if (score >= 60) return theme.palette.info.main;
    if (score >= 40) return theme.palette.warning.main;
    return theme.palette.error.main;
  };

  // Get trend icon based on score
  const getTrendIcon = (score: number) => {
    if (score >= 80) return <TrendingUpIcon color="success" />;
    if (score >= 60) return <TrendingFlatIcon color="info" />;
    return <TrendingDownIcon color="error" />;
  };

  if (loading) {
    return (
      <Paper elevation={2} sx={{ p: 2, textAlign: 'center' }}>
        <CircularProgress size={40} />
        <Typography variant="body2" sx={{ mt: 1 }}>
          Loading health score...
        </Typography>
      </Paper>
    );
  }

  if (error) {
    return (
      <Paper elevation={2} sx={{ p: 2 }}>
        <Alert severity="error">{error}</Alert>
      </Paper>
    );
  }

  if (!healthScore) {
    return (
      <Paper elevation={2} sx={{ p: 2 }}>
        <Alert severity="info">No health score data available</Alert>
      </Paper>
    );
  }

  const statusDisplay = getHealthStatusDisplay(
    healthScore.overall_health_score,
    healthScore.health_status
  );

  return (
    <Paper elevation={2} sx={{ p: compact ? 1 : 2 }}>
      <Typography variant={compact ? "subtitle1" : "h6"} gutterBottom>
        Container Health Score
      </Typography>

      {/* Overall Health Score */}
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <Box sx={{ position: 'relative', display: 'inline-flex', mr: 2 }}>
          <CircularProgress
            variant="determinate"
            value={healthScore.overall_health_score}
            size={compact ? 60 : 80}
            thickness={4}
            sx={{
              color: statusDisplay.color,
              '& .MuiCircularProgress-circle': {
                strokeLinecap: 'round',
              },
            }}
          />
          <Box
            sx={{
              top: 0,
              left: 0,
              bottom: 0,
              right: 0,
              position: 'absolute',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Typography
              variant={compact ? "body2" : "h6"}
              component="div"
              color="text.secondary"
              fontWeight="bold"
            >
              {Math.round(healthScore.overall_health_score)}
            </Typography>
          </Box>
        </Box>

        <Box sx={{ flex: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
            {statusDisplay.icon}
            <Chip
              label={statusDisplay.label}
              size="small"
              sx={{
                ml: 1,
                backgroundColor: statusDisplay.backgroundColor,
                color: statusDisplay.color,
              }}
            />
          </Box>
          <Typography variant="body2" color="text.secondary">
            Based on {healthScore.data_points_analyzed} data points
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Analysis period: {healthScore.analysis_period_hours}h
          </Typography>
        </Box>
      </Box>

      {/* Component Health Breakdown */}
      {showComponentBreakdown && (
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            Component Health
          </Typography>
          <Grid container spacing={1}>
            {Object.entries(healthScore.component_scores).map(([component, score]) => (
              <Grid item xs={6} sm={3} key={component}>
                <Box
                  sx={{
                    p: 1,
                    border: 1,
                    borderColor: 'divider',
                    borderRadius: 1,
                    textAlign: 'center',
                  }}
                >
                  <Typography variant="caption" color="text.secondary">
                    {component.replace('_', ' ').toUpperCase()}
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mt: 0.5 }}>
                    <Typography
                      variant="body2"
                      fontWeight="bold"
                      sx={{ color: getComponentHealthColor(score) }}
                    >
                      {Math.round(score)}
                    </Typography>
                    {getTrendIcon(score)}
                  </Box>
                </Box>
              </Grid>
            ))}
          </Grid>
        </Box>
      )}

      {/* Recommendations */}
      {showRecommendations && healthScore.recommendations.length > 0 && (
        <Box>
          <Typography variant="subtitle2" gutterBottom>
            Recommendations
          </Typography>
          <List dense>
            {healthScore.recommendations.slice(0, compact ? 2 : 5).map((recommendation, index) => (
              <ListItem key={index} sx={{ py: 0.5 }}>
                <ListItemIcon sx={{ minWidth: 32 }}>
                  <InfoIcon fontSize="small" color="info" />
                </ListItemIcon>
                <ListItemText
                  primary={recommendation}
                  primaryTypographyProps={{
                    variant: 'body2',
                    color: 'text.secondary',
                  }}
                />
              </ListItem>
            ))}
          </List>
          {compact && healthScore.recommendations.length > 2 && (
            <Typography variant="caption" color="text.secondary">
              +{healthScore.recommendations.length - 2} more recommendations
            </Typography>
          )}
        </Box>
      )}
    </Paper>
  );
};

export default ContainerHealthScoreVisualization;
