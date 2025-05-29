import React from "react";
import { Typography, Box, Paper, Grid } from "@mui/material";
import NaturalLanguageInput from "../components/NaturalLanguageInput";
import SystemOverview from "../components/SystemOverview";

/**
 * Dashboard component - Main landing page for the DockerDeployer application.
 *
 * This component serves as the primary entry point for users after authentication.
 * It provides an overview of the application and quick access to core functionality
 * through the natural language interface.
 *
 * **Features:**
 * - **Welcome Interface**: Clean, informative landing page design
 * - **Natural Language Input**: Direct access to AI-powered command processing
 * - **Quick Actions**: Immediate access to container management commands
 * - **Responsive Layout**: Adapts to different screen sizes and devices
 *
 * **Layout Structure:**
 * - Header section with welcome message and description
 * - Integrated natural language input component
 * - Future: Will include system overview widgets and quick stats
 *
 * **Usage Context:**
 * This component is typically rendered as the default route ("/") for authenticated
 * users and serves as the main hub for accessing DockerDeployer functionality.
 *
 * @component
 * @example
 * ```tsx
 * // Used in routing
 * <Route path="/" element={
 *   <ProtectedRoute>
 *     <MainLayout>
 *       <Dashboard />
 *     </MainLayout>
 *   </ProtectedRoute>
 * } />
 *
 * // Direct usage
 * <Dashboard />
 * ```
 *
 * @returns {JSX.Element} The rendered Dashboard component with welcome content
 *   and natural language input interface
 */
const Dashboard: React.FC = () => (
  <Box sx={{ p: 3 }}>
    <Paper elevation={2} sx={{ p: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>
      <Typography variant="body1" color="text.secondary">
        Welcome to the DockerDeployer dashboard! Monitor your containers, view
        system metrics, and manage your Docker infrastructure with natural
        language commands.
      </Typography>
    </Paper>

    <Grid container spacing={3}>
      <Grid item xs={12}>
        <SystemOverview />
      </Grid>

      <Grid item xs={12}>
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Quick Actions
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Use natural language to manage your containers and deployments:
          </Typography>
          <NaturalLanguageInput />
        </Paper>
      </Grid>
    </Grid>
  </Box>
);

export default Dashboard;
