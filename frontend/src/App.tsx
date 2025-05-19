import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import CssBaseline from "@mui/material/CssBaseline";
import Box from "@mui/material/Box";
import AppBar from "@mui/material/AppBar";
import Toolbar from "@mui/material/Toolbar";
import Typography from "@mui/material/Typography";
import Container from "@mui/material/Container";
import theme from "./theme";
import { ThemeProvider } from "@mui/material/styles";
import Sidebar from "./components/Sidebar";
import Dashboard from "./pages/Dashboard";
import Containers from "./pages/Containers";
import Templates from "./pages/Templates";
import Logs from "./pages/Logs";
import Settings from "./pages/Settings";

const drawerWidth = 220;

const App: React.FC = () => {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Box sx={{ display: "flex" }}>
          <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
            <Toolbar>
              <Typography variant="h6" noWrap component="div">
                DockerDeployer Dashboard
              </Typography>
            </Toolbar>
          </AppBar>
          <Sidebar />
          <Box
            component="main"
            sx={{
              flexGrow: 1,
              bgcolor: "background.default",
              minHeight: "100vh",
              p: 4,
              ml: `${drawerWidth}px`,
            }}
          >
            <Toolbar />
            <Container maxWidth="md">
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/containers" element={<Containers />} />
                <Route path="/templates" element={<Templates />} />
                <Route path="/logs" element={<Logs />} />
                <Route path="/settings" element={<Settings />} />
              </Routes>
            </Container>
          </Box>
        </Box>
      </Router>
    </ThemeProvider>
  );
};

export default App;
