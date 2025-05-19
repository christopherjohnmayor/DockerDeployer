import React from "react";
import { Typography, Paper, Box } from "@mui/material";

const Logs: React.FC = () => {
  return (
    <Box sx={{ mt: 2 }}>
      <Paper elevation={2} sx={{ p: 3 }}>
        <Typography variant="h5" gutterBottom>
          Logs
        </Typography>
        <Typography variant="body1" color="text.secondary">
          This is a placeholder for the Logs page. Here you will be able to view and search logs for your Docker containers.
        </Typography>
      </Paper>
    </Box>
  );
};

export default Logs;
