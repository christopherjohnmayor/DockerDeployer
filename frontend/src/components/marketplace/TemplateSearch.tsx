import React, { useState, useEffect } from "react";
import {
  Box,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Rating,
  Typography,
  Chip,
  IconButton,
  Tooltip,
  Paper,
  Collapse,
  Button,
} from "@mui/material";
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  Clear as ClearIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
} from "@mui/icons-material";
import { TemplateSearch, Category } from "../../api/marketplace";

interface TemplateSearchProps {
  onSearch: (params: TemplateSearch) => void;
  categories: Category[];
  loading?: boolean;
  initialParams?: TemplateSearch;
}

/**
 * Template Search Component
 * 
 * Provides comprehensive search and filtering capabilities for the marketplace.
 * Includes text search, category filtering, rating filtering, and sorting options.
 * 
 * Features:
 * - Real-time search with debouncing
 * - Category dropdown filtering
 * - Minimum rating filter with star selector
 * - Sort by options (newest, rating, downloads, name)
 * - Sort order toggle (ascending/descending)
 * - Collapsible advanced filters
 * - Clear all filters functionality
 * - Active filter indicators
 */
const TemplateSearch: React.FC<TemplateSearchProps> = ({
  onSearch,
  categories,
  loading = false,
  initialParams = {},
}) => {
  const [searchParams, setSearchParams] = useState<TemplateSearch>(initialParams);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [searchTimeout, setSearchTimeout] = useState<NodeJS.Timeout | null>(null);

  // Debounced search effect
  useEffect(() => {
    if (searchTimeout) {
      clearTimeout(searchTimeout);
    }

    const timeout = setTimeout(() => {
      onSearch(searchParams);
    }, 300);

    setSearchTimeout(timeout);

    return () => {
      if (timeout) {
        clearTimeout(timeout);
      }
    };
  }, [searchParams, onSearch]);

  const handleParamChange = (key: keyof TemplateSearch, value: any) => {
    setSearchParams(prev => ({
      ...prev,
      [key]: value,
      page: 1, // Reset to first page when filters change
    }));
  };

  const clearFilters = () => {
    setSearchParams({
      query: "",
      category_id: undefined,
      min_rating: undefined,
      sort_by: "created_at",
      sort_order: "desc",
      page: 1,
      per_page: 20,
    });
  };

  const getActiveFilterCount = () => {
    let count = 0;
    if (searchParams.query) count++;
    if (searchParams.category_id) count++;
    if (searchParams.min_rating) count++;
    return count;
  };

  const sortOptions = [
    { value: "created_at", label: "Newest" },
    { value: "rating_avg", label: "Rating" },
    { value: "downloads", label: "Downloads" },
    { value: "name", label: "Name" },
  ];

  return (
    <Paper elevation={1} sx={{ p: 2, mb: 3 }}>
      {/* Main search bar */}
      <Box display="flex" gap={2} alignItems="center" mb={2}>
        <TextField
          fullWidth
          placeholder="Search templates..."
          value={searchParams.query || ""}
          onChange={(e) => handleParamChange("query", e.target.value)}
          InputProps={{
            startAdornment: <SearchIcon color="action" sx={{ mr: 1 }} />,
            endAdornment: searchParams.query && (
              <IconButton
                size="small"
                onClick={() => handleParamChange("query", "")}
              >
                <ClearIcon />
              </IconButton>
            ),
          }}
          disabled={loading}
        />
        
        <Button
          variant="outlined"
          startIcon={<FilterIcon />}
          endIcon={showAdvanced ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          onClick={() => setShowAdvanced(!showAdvanced)}
          sx={{ minWidth: 120 }}
        >
          Filters
          {getActiveFilterCount() > 0 && (
            <Chip
              label={getActiveFilterCount()}
              size="small"
              color="primary"
              sx={{ ml: 1, height: 20, fontSize: "0.7rem" }}
            />
          )}
        </Button>
      </Box>

      {/* Advanced filters */}
      <Collapse in={showAdvanced}>
        <Box display="flex" flexWrap="wrap" gap={2} alignItems="center">
          {/* Category filter */}
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Category</InputLabel>
            <Select
              value={searchParams.category_id || ""}
              label="Category"
              onChange={(e) => handleParamChange("category_id", e.target.value || undefined)}
              disabled={loading}
            >
              <MenuItem value="">All Categories</MenuItem>
              {categories.map((category) => (
                <MenuItem key={category.id} value={category.id}>
                  {category.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          {/* Rating filter */}
          <Box display="flex" alignItems="center" gap={1}>
            <Typography variant="body2" color="text.secondary">
              Min Rating:
            </Typography>
            <Rating
              value={searchParams.min_rating || 0}
              onChange={(_, value) => handleParamChange("min_rating", value || undefined)}
              size="small"
              disabled={loading}
            />
            {searchParams.min_rating && (
              <IconButton
                size="small"
                onClick={() => handleParamChange("min_rating", undefined)}
              >
                <ClearIcon fontSize="small" />
              </IconButton>
            )}
          </Box>

          {/* Sort options */}
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Sort By</InputLabel>
            <Select
              value={searchParams.sort_by || "created_at"}
              label="Sort By"
              onChange={(e) => handleParamChange("sort_by", e.target.value)}
              disabled={loading}
            >
              {sortOptions.map((option) => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControl size="small" sx={{ minWidth: 100 }}>
            <InputLabel>Order</InputLabel>
            <Select
              value={searchParams.sort_order || "desc"}
              label="Order"
              onChange={(e) => handleParamChange("sort_order", e.target.value as "asc" | "desc")}
              disabled={loading}
            >
              <MenuItem value="desc">Descending</MenuItem>
              <MenuItem value="asc">Ascending</MenuItem>
            </Select>
          </FormControl>

          {/* Clear filters */}
          {getActiveFilterCount() > 0 && (
            <Tooltip title="Clear all filters">
              <Button
                variant="outlined"
                size="small"
                startIcon={<ClearIcon />}
                onClick={clearFilters}
                disabled={loading}
              >
                Clear
              </Button>
            </Tooltip>
          )}
        </Box>
      </Collapse>

      {/* Active filters display */}
      {getActiveFilterCount() > 0 && (
        <Box display="flex" flexWrap="wrap" gap={1} mt={2}>
          {searchParams.query && (
            <Chip
              label={`Search: "${searchParams.query}"`}
              size="small"
              onDelete={() => handleParamChange("query", "")}
              color="primary"
              variant="outlined"
            />
          )}
          {searchParams.category_id && (
            <Chip
              label={`Category: ${categories.find(c => c.id === searchParams.category_id)?.name}`}
              size="small"
              onDelete={() => handleParamChange("category_id", undefined)}
              color="primary"
              variant="outlined"
            />
          )}
          {searchParams.min_rating && (
            <Chip
              label={`Min Rating: ${searchParams.min_rating}★`}
              size="small"
              onDelete={() => handleParamChange("min_rating", undefined)}
              color="primary"
              variant="outlined"
            />
          )}
        </Box>
      )}
    </Paper>
  );
};

export default TemplateSearch;
