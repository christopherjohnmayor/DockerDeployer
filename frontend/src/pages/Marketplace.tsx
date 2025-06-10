import React from "react";
import { Box, Container } from "@mui/material";
import MarketplaceHome from "../components/marketplace/MarketplaceHome";

/**
 * Marketplace Page Component
 * 
 * Main page for the Template Marketplace feature.
 * Serves as the entry point for browsing, searching, and managing templates.
 * 
 * Features:
 * - Template browsing and search
 * - Template submission for authenticated users
 * - Responsive layout with proper spacing
 * - Integration with marketplace components
 */
const Marketplace: React.FC = () => {
  return (
    <Container maxWidth="xl">
      <Box py={3}>
        <MarketplaceHome />
      </Box>
    </Container>
  );
};

export default Marketplace;
