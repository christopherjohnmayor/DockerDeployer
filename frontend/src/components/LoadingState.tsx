import React from 'react';
import {
  Box,
  CircularProgress,
  LinearProgress,
  Skeleton,
  Typography,
  Card,
  CardContent,
} from '@mui/material';

interface LoadingStateProps {
  variant?: 'circular' | 'linear' | 'skeleton' | 'card';
  message?: string;
  size?: 'small' | 'medium' | 'large';
  fullScreen?: boolean;
  rows?: number; // For skeleton variant
}

/**
 * Reusable loading state component with multiple variants
 * 
 * Features:
 * - Multiple loading indicators (circular, linear, skeleton, card)
 * - Configurable sizes and messages
 * - Full-screen loading overlay option
 * - Accessible loading states
 * - Consistent styling across the app
 */
const LoadingState: React.FC<LoadingStateProps> = ({
  variant = 'circular',
  message = 'Loading...',
  size = 'medium',
  fullScreen = false,
  rows = 3,
}) => {
  const getSizeValue = () => {
    switch (size) {
      case 'small':
        return 24;
      case 'large':
        return 60;
      default:
        return 40;
    }
  };

  const renderLoadingContent = () => {
    switch (variant) {
      case 'linear':
        return (
          <Box sx={{ width: '100%' }}>
            <LinearProgress />
            {message && (
              <Typography 
                variant="body2" 
                color="text.secondary" 
                sx={{ mt: 1, textAlign: 'center' }}
              >
                {message}
              </Typography>
            )}
          </Box>
        );

      case 'skeleton':
        return (
          <Box sx={{ width: '100%' }}>
            {Array.from({ length: rows }).map((_, index) => (
              <Skeleton
                key={index}
                variant="rectangular"
                height={40}
                sx={{ mb: 1, borderRadius: 1 }}
                animation="wave"
              />
            ))}
          </Box>
        );

      case 'card':
        return (
          <Card sx={{ minHeight: 200 }}>
            <CardContent>
              <Box
                display="flex"
                flexDirection="column"
                alignItems="center"
                justifyContent="center"
                minHeight={150}
              >
                <CircularProgress size={getSizeValue()} sx={{ mb: 2 }} />
                <Typography variant="body1" color="text.secondary">
                  {message}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        );

      default: // circular
        return (
          <Box
            display="flex"
            flexDirection="column"
            alignItems="center"
            justifyContent="center"
            gap={2}
          >
            <CircularProgress size={getSizeValue()} />
            {message && (
              <Typography 
                variant="body2" 
                color="text.secondary"
                textAlign="center"
              >
                {message}
              </Typography>
            )}
          </Box>
        );
    }
  };

  if (fullScreen) {
    return (
      <Box
        position="fixed"
        top={0}
        left={0}
        right={0}
        bottom={0}
        display="flex"
        alignItems="center"
        justifyContent="center"
        bgcolor="rgba(255, 255, 255, 0.8)"
        zIndex={9999}
        sx={{ backdropFilter: 'blur(2px)' }}
      >
        {renderLoadingContent()}
      </Box>
    );
  }

  return (
    <Box
      display="flex"
      alignItems="center"
      justifyContent="center"
      minHeight={variant === 'skeleton' ? 'auto' : 200}
      p={2}
    >
      {renderLoadingContent()}
    </Box>
  );
};

/**
 * Loading overlay component for existing content
 */
export const LoadingOverlay: React.FC<{
  loading: boolean;
  children: React.ReactNode;
  message?: string;
}> = ({ loading, children, message = 'Loading...' }) => {
  return (
    <Box position="relative">
      {children}
      {loading && (
        <Box
          position="absolute"
          top={0}
          left={0}
          right={0}
          bottom={0}
          display="flex"
          alignItems="center"
          justifyContent="center"
          bgcolor="rgba(255, 255, 255, 0.8)"
          zIndex={1}
          sx={{ backdropFilter: 'blur(1px)' }}
        >
          <Box
            display="flex"
            flexDirection="column"
            alignItems="center"
            gap={2}
          >
            <CircularProgress />
            <Typography variant="body2" color="text.secondary">
              {message}
            </Typography>
          </Box>
        </Box>
      )}
    </Box>
  );
};

/**
 * Table loading skeleton component
 */
export const TableLoadingSkeleton: React.FC<{
  rows?: number;
  columns?: number;
}> = ({ rows = 5, columns = 4 }) => {
  return (
    <Box>
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <Box
          key={rowIndex}
          display="flex"
          gap={2}
          mb={1}
          alignItems="center"
        >
          {Array.from({ length: columns }).map((_, colIndex) => (
            <Skeleton
              key={colIndex}
              variant="rectangular"
              height={40}
              sx={{ flex: 1, borderRadius: 1 }}
              animation="wave"
            />
          ))}
        </Box>
      ))}
    </Box>
  );
};

export default LoadingState;
