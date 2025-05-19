import React from "react";
import { Typography, Box, Paper } from "@mui/material";
import NaturalLanguageInput from "../components/NaturalLanguageInput";

const Dashboard: React.FC = () => (
  <Box sx={{ p: 3 }}>
    <Paper elevation={2} sx={{ p: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>
      <Typography variant="body1" color="text.secondary">
        Welcome to the DockerDeployer dashboard! Here you will see an overview of your containers, resource usage, and quick actions.
        <br />
        (This is a placeholder. More features coming soon.)
      </Typography>
    </Paper>
    <NaturalLanguageInput />
  </Box>
);

export default Dashboard;
