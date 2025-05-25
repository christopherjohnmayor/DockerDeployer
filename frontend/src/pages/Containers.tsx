import React, { useEffect, useState } from "react";
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  Alert,
  Chip,
  Button,
  Stack,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tooltip,
} from "@mui/material";
import axios from "axios";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import StopIcon from "@mui/icons-material/Stop";
import RestartAltIcon from "@mui/icons-material/RestartAlt";
import TerminalIcon from "@mui/icons-material/Terminal";

const Containers: React.FC = () => {
  const [containers, setContainers] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [logOpen, setLogOpen] = useState<boolean>(false);
  const [logContent, setLogContent] = useState<string>("");
  const [logTitle, setLogTitle] = useState<string>("");

  const fetchContainers = async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await axios.get("/api/containers");
      setContainers(resp.data);
    } catch (err: any) {
      setError(
        err?.response?.data?.detail ||
          err.message ||
          "Failed to fetch containers."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchContainers();
    // eslint-disable-next-line
  }, []);

  const handleAction = async (
    containerId: string,
    action: "start" | "stop" | "restart"
  ) => {
    try {
      await axios.post(`/api/containers/${containerId}/action`, { action });
      fetchContainers();
    } catch (err: any) {
      setError(
        err?.response?.data?.detail ||
          err.message ||
          `Failed to ${action} container.`
      );
    }
  };

  const handleShowLogs = async (containerId: string, containerName: string) => {
    setLogOpen(true);
    setLogTitle(`Logs: ${containerName}`);
    setLogContent("Loading...");
    try {
      const resp = await axios.get(`/api/logs/${containerId}`);
      setLogContent(resp.data.logs || "No logs found.");
    } catch (err: any) {
      setLogContent(
        err?.response?.data?.detail || err.message || "Failed to fetch logs."
      );
    }
  };

  const handleCloseLog = () => {
    setLogOpen(false);
    setLogContent("");
    setLogTitle("");
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Docker Containers
      </Typography>
      <Stack direction="row" spacing={2} mb={2}>
        <Button variant="contained" onClick={fetchContainers}>
          Refresh
        </Button>
      </Stack>
      <Paper sx={{ mt: 2, p: 2 }}>
        {loading ? (
          <Box
            display="flex"
            justifyContent="center"
            alignItems="center"
            minHeight={120}
          >
            <CircularProgress />
          </Box>
        ) : error ? (
          <Alert severity="error">{error}</Alert>
        ) : containers.length === 0 ? (
          <Alert severity="info">No containers found.</Alert>
        ) : (
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Name</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Image</TableCell>
                  <TableCell>Ports</TableCell>
                  <TableCell>ID</TableCell>
                  <TableCell align="center">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {containers.map((container) => (
                  <TableRow key={container.id}>
                    <TableCell>
                      <Typography fontWeight={500}>{container.name}</Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={container.status}
                        color={
                          container.status === "running"
                            ? "success"
                            : container.status === "exited"
                              ? "default"
                              : "warning"
                        }
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      {container.image && container.image.length > 0
                        ? container.image.join(", ")
                        : "-"}
                    </TableCell>
                    <TableCell>
                      {container.ports
                        ? Object.keys(container.ports).length > 0
                          ? Object.entries(container.ports)
                              .map(
                                ([k, v]) =>
                                  `${k} \u2192 ${Array.isArray(v) ? v.join(",") : v}`
                              )
                              .join(", ")
                          : "-"
                        : "-"}
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" color="text.secondary">
                        {container.id.slice(0, 12)}
                      </Typography>
                    </TableCell>
                    <TableCell align="center">
                      <Stack
                        direction="row"
                        spacing={1}
                        justifyContent="center"
                      >
                        <Tooltip title="Start">
                          <span>
                            <IconButton
                              color="success"
                              size="small"
                              disabled={container.status === "running"}
                              onClick={() =>
                                handleAction(container.id, "start")
                              }
                            >
                              <PlayArrowIcon />
                            </IconButton>
                          </span>
                        </Tooltip>
                        <Tooltip title="Stop">
                          <span>
                            <IconButton
                              color="error"
                              size="small"
                              disabled={container.status !== "running"}
                              onClick={() => handleAction(container.id, "stop")}
                            >
                              <StopIcon />
                            </IconButton>
                          </span>
                        </Tooltip>
                        <Tooltip title="Restart">
                          <span>
                            <IconButton
                              color="primary"
                              size="small"
                              disabled={container.status !== "running"}
                              onClick={() =>
                                handleAction(container.id, "restart")
                              }
                            >
                              <RestartAltIcon />
                            </IconButton>
                          </span>
                        </Tooltip>
                        <Tooltip title="Logs">
                          <span>
                            <IconButton
                              color="info"
                              size="small"
                              onClick={() =>
                                handleShowLogs(container.id, container.name)
                              }
                            >
                              <TerminalIcon />
                            </IconButton>
                          </span>
                        </Tooltip>
                      </Stack>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>
      <Dialog open={logOpen} onClose={handleCloseLog} maxWidth="md" fullWidth>
        <DialogTitle>{logTitle}</DialogTitle>
        <DialogContent>
          <Box
            component="pre"
            sx={{
              background: "#111",
              color: "#fff",
              borderRadius: 1,
              p: 2,
              minHeight: 200,
              maxHeight: 400,
              overflow: "auto",
              fontSize: "0.95em",
            }}
          >
            {logContent}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseLog}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Containers;
