import React from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
import CssBaseline from "@mui/material/CssBaseline";
import Box from "@mui/material/Box";
import AppBar from "@mui/material/AppBar";
import Toolbar from "@mui/material/Toolbar";
import Typography from "@mui/material/Typography";
import Container from "@mui/material/Container";
import Button from "@mui/material/Button";
import theme from "./theme";
import { ThemeProvider } from "@mui/material/styles";
import Sidebar from "./components/Sidebar";
import Dashboard from "./pages/Dashboard";
import Containers from "./pages/Containers";
import Templates from "./pages/Templates";
import Logs from "./pages/Logs";
import Settings from "./pages/Settings";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Unauthorized from "./pages/Unauthorized";
import ProtectedRoute from "./components/ProtectedRoute";
import { AuthProvider } from "./contexts/AuthContext";
import { useAuth } from "./hooks/useAuth";

const drawerWidth = 220;

// Header component with logout button
const Header: React.FC = () => {
  const { isAuthenticated, user, logout } = useAuth();

  return (
    <AppBar
      position="fixed"
      sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}
    >
      <Toolbar>
        <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
          DockerDeployer Dashboard
        </Typography>
        {isAuthenticated && (
          <Box sx={{ display: "flex", alignItems: "center" }}>
            <Typography variant="body2" sx={{ mr: 2 }}>
              {user?.username} ({user?.role})
            </Typography>
            <Button color="inherit" onClick={logout}>
              Logout
            </Button>
          </Box>
        )}
      </Toolbar>
    </AppBar>
  );
};

// Main layout for authenticated users
const MainLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <Box sx={{ display: "flex" }}>
      <Header />
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
        <Container maxWidth="md">{children}</Container>
      </Box>
    </Box>
  );
};

const App: React.FC = () => {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <Router>
          <Routes>
            {/* Public routes */}
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/unauthorized" element={<Unauthorized />} />

            {/* Protected routes */}
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <MainLayout>
                    <Dashboard />
                  </MainLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/containers"
              element={
                <ProtectedRoute>
                  <MainLayout>
                    <Containers />
                  </MainLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/templates"
              element={
                <ProtectedRoute>
                  <MainLayout>
                    <Templates />
                  </MainLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/logs"
              element={
                <ProtectedRoute>
                  <MainLayout>
                    <Logs />
                  </MainLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/settings"
              element={
                <ProtectedRoute requiredRole="admin">
                  <MainLayout>
                    <Settings />
                  </MainLayout>
                </ProtectedRoute>
              }
            />

            {/* Fallback route */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Router>
      </AuthProvider>
    </ThemeProvider>
  );
};

export default App;
