import React, { useState } from "react";
import {
  Box,
  Typography,
  Rating,
  TextField,
  Button,
  Paper,
  Avatar,
  Divider,
  Alert,
  Collapse,
} from "@mui/material";
import {
  Person as PersonIcon,
  Add as AddIcon,
  Cancel as CancelIcon,
} from "@mui/icons-material";
import { useApiCall } from "../../hooks/useApiCall";
import { LoadingState } from "../LoadingState";
import ErrorDisplay from "../ErrorDisplay";
import { Review, ReviewCreate, createReview } from "../../api/marketplace";

interface TemplateReviewsProps {
  templateId: number;
  reviews: Review[];
  onReviewAdded: () => void;
  canAddReview: boolean;
}

/**
 * Template Reviews Component
 * 
 * Displays template reviews and provides review submission functionality.
 * Shows existing reviews with ratings and comments, and allows authenticated
 * users to submit new reviews.
 * 
 * Features:
 * - Display existing reviews with user info and timestamps
 * - Star rating display for each review
 * - Review submission form with rating and comment
 * - Form validation and error handling
 * - Collapsible review form
 * - Empty state for no reviews
 */
const TemplateReviews: React.FC<TemplateReviewsProps> = ({
  templateId,
  reviews,
  onReviewAdded,
  canAddReview,
}) => {
  const [showReviewForm, setShowReviewForm] = useState(false);
  const [reviewData, setReviewData] = useState<ReviewCreate>({
    rating: 0,
    comment: "",
  });

  // API call for submitting review
  const {
    loading: submittingReview,
    error: submitError,
    execute: submitReview,
  } = useApiCall(createReview, {
    showSuccessToast: true,
    successMessage: "Review submitted successfully!",
  });

  const handleSubmitReview = async () => {
    if (reviewData.rating === 0) {
      return;
    }

    const result = await submitReview(templateId, reviewData);
    if (result) {
      setReviewData({ rating: 0, comment: "" });
      setShowReviewForm(false);
      onReviewAdded();
    }
  };

  const handleCancelReview = () => {
    setReviewData({ rating: 0, comment: "" });
    setShowReviewForm(false);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  const isReviewValid = reviewData.rating > 0;

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h6">
          Reviews ({reviews.length})
        </Typography>
        {canAddReview && !showReviewForm && (
          <Button
            variant="outlined"
            startIcon={<AddIcon />}
            onClick={() => setShowReviewForm(true)}
          >
            Write Review
          </Button>
        )}
      </Box>

      {/* Review submission form */}
      <Collapse in={showReviewForm}>
        <Paper variant="outlined" sx={{ p: 3, mb: 3 }}>
          <Typography variant="subtitle1" gutterBottom>
            Write a Review
          </Typography>
          
          <Box mb={2}>
            <Typography component="legend" variant="body2" gutterBottom>
              Rating *
            </Typography>
            <Rating
              value={reviewData.rating}
              onChange={(_, value) =>
                setReviewData(prev => ({ ...prev, rating: value || 0 }))
              }
              size="large"
            />
          </Box>

          <TextField
            fullWidth
            multiline
            rows={4}
            label="Comment (optional)"
            placeholder="Share your experience with this template..."
            value={reviewData.comment}
            onChange={(e) =>
              setReviewData(prev => ({ ...prev, comment: e.target.value }))
            }
            sx={{ mb: 2 }}
          />

          {submitError && (
            <ErrorDisplay
              error={submitError}
              onRetry={handleSubmitReview}
              title="Failed to submit review"
              sx={{ mb: 2 }}
            />
          )}

          <Box display="flex" gap={2}>
            <Button
              variant="contained"
              onClick={handleSubmitReview}
              disabled={!isReviewValid || submittingReview}
              startIcon={submittingReview ? <LoadingState variant="circular" size="small" /> : undefined}
            >
              Submit Review
            </Button>
            <Button
              variant="outlined"
              startIcon={<CancelIcon />}
              onClick={handleCancelReview}
              disabled={submittingReview}
            >
              Cancel
            </Button>
          </Box>
        </Paper>
      </Collapse>

      {/* Reviews list */}
      {reviews.length === 0 ? (
        <Alert severity="info">
          No reviews yet. Be the first to review this template!
        </Alert>
      ) : (
        <Box>
          {reviews.map((review, index) => (
            <Box key={review.id}>
              <Paper variant="outlined" sx={{ p: 3 }}>
                {/* Review header */}
                <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
                  <Box display="flex" alignItems="center" gap={2}>
                    <Avatar sx={{ width: 32, height: 32 }}>
                      <PersonIcon sx={{ fontSize: 20 }} />
                    </Avatar>
                    <Box>
                      <Typography variant="subtitle2">
                        {review.username || `User ${review.user_id}`}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {formatDate(review.created_at)}
                      </Typography>
                    </Box>
                  </Box>
                  <Rating value={review.rating} readOnly size="small" />
                </Box>

                {/* Review comment */}
                {review.comment && (
                  <Typography variant="body2" sx={{ mt: 1 }}>
                    {review.comment}
                  </Typography>
                )}
              </Paper>

              {/* Divider between reviews */}
              {index < reviews.length - 1 && (
                <Divider sx={{ my: 2 }} />
              )}
            </Box>
          ))}
        </Box>
      )}
    </Box>
  );
};

export default TemplateReviews;
