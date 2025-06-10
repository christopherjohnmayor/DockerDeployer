import React from "react";
import {
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Divider,
  useTheme,
  useMediaQuery,
} from "@mui/material";
import { Link, useLocation } from "react-router-dom";
import DashboardIcon from "@mui/icons-material/Dashboard";
import StorageIcon from "@mui/icons-material/Storage";
import ListAltIcon from "@mui/icons-material/ListAlt";
import LayersIcon from "@mui/icons-material/Layers";
import PeopleIcon from "@mui/icons-material/People";
import SettingsIcon from "@mui/icons-material/Settings";
import AssessmentIcon from "@mui/icons-material/Assessment";
import NotificationsActiveIcon from "@mui/icons-material/NotificationsActive";
import MonitorHeartIcon from "@mui/icons-material/MonitorHeart";
import StoreIcon from "@mui/icons-material/Store";
import FolderIcon from "@mui/icons-material/Folder";
import { useAuth } from "../hooks/useAuth";

const drawerWidth = 220;

const Sidebar: React.FC = () => {
  const location = useLocation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));
  const { user } = useAuth();

  const navItems = [
    { text: "Dashboard", icon: <DashboardIcon />, path: "/" },
    { text: "Containers", icon: <StorageIcon />, path: "/containers" },
    { text: "Templates", icon: <ListAltIcon />, path: "/templates" },
    { text: "Marketplace", icon: <StoreIcon />, path: "/marketplace" },
    { text: "My Templates", icon: <FolderIcon />, path: "/my-templates" },
    { text: "Logs", icon: <LayersIcon />, path: "/logs" },
    { text: "Metrics", icon: <AssessmentIcon />, path: "/metrics" },
    { text: "Alerts", icon: <NotificationsActiveIcon />, path: "/alerts" },
    ...(user?.role === "admin"
      ? [
          {
            text: "Production",
            icon: <MonitorHeartIcon />,
            path: "/production",
          },
          { text: "Users", icon: <PeopleIcon />, path: "/users" },
          { text: "Settings", icon: <SettingsIcon />, path: "/settings" },
        ]
      : []),
  ];

  return (
    <Drawer
      variant={isMobile ? "temporary" : "permanent"}
      open={!isMobile || undefined}
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        display: { xs: "none", sm: "block" },
        [`& .MuiDrawer-paper`]: {
          width: drawerWidth,
          boxSizing: "border-box",
          backgroundColor: "#fff",
          borderRight: "1px solid #e0e0e0",
        },
      }}
      ModalProps={{
        keepMounted: true,
      }}
    >
      <Toolbar />
      <Divider />
      <List>
        {navItems.map((item) => {
          const isActive =
            item.path === "/"
              ? location.pathname === "/"
              : location.pathname.startsWith(item.path);
          return (
            <ListItem
              button
              key={item.text}
              component={Link}
              to={item.path}
              selected={isActive}
              sx={{
                borderRadius: 2,
                mx: 1,
                my: 0.5,
                "&.Mui-selected": {
                  backgroundColor: "#e3f2fd",
                  color: "#1976d2",
                  "& .MuiListItemIcon-root": {
                    color: "#1976d2",
                  },
                },
                "&:hover": {
                  backgroundColor: "#f5faff",
                },
                transition: "background 0.2s",
              }}
            >
              <ListItemIcon sx={{ minWidth: 36 }}>{item.icon}</ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItem>
          );
        })}
      </List>
    </Drawer>
  );
};

export default Sidebar;
