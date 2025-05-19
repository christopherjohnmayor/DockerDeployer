import React, { useState, useEffect } from "react";
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  CircularProgress,
  Alert,
  Stack,
  Chip,
  Autocomplete,
  Divider,
  IconButton,
  Tooltip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Collapse,
} from "@mui/material";
import SendIcon from "@mui/icons-material/Send";
import HistoryIcon from "@mui/icons-material/History";
import LightbulbIcon from "@mui/icons-material/Lightbulb";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import axios from "axios";

// Example commands for suggestions
const EXAMPLE_COMMANDS = [
  "Deploy a WordPress stack",
  "Start all containers",
  "Stop container named web-server",
  "Show logs for database container",
  "Create a LEMP stack with PHP 8.1",
  "List all running containers",
  "Restart nginx container",
  "Deploy a Node.js application",
  "Create a container with Redis",
  "Show container stats",
];

const NaturalLanguageInput: React.FC = () => {
  const [command, setCommand] = useState("");
  const [response, setResponse] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [commandHistory, setCommandHistory] = useState<string[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);

  // Load command history from localStorage on component mount
  useEffect(() => {
    const savedHistory = localStorage.getItem("commandHistory");
    if (savedHistory) {
      try {
        setCommandHistory(JSON.parse(savedHistory));
      } catch (e) {
        console.error("Failed to parse command history:", e);
      }
    }
  }, []);

  const saveCommandToHistory = (cmd: string) => {
    const newHistory = [cmd, ...commandHistory.filter((c) => c !== cmd)].slice(
      0,
      10
    );
    setCommandHistory(newHistory);
    localStorage.setItem("commandHistory", JSON.stringify(newHistory));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!command.trim()) return;

    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      saveCommandToHistory(command);
      const res = await axios.post("/api/nlp/parse", { command });
      setResponse(
        res.data && res.data.action_plan
          ? JSON.stringify(res.data.action_plan, null, 2)
          : "No response from backend."
      );
    } catch (err: any) {
      setError(
        err?.response?.data?.detail ||
          err?.message ||
          "Failed to process command."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleHistoryItemClick = (cmd: string) => {
    setCommand(cmd);
    setShowHistory(false);
  };

  const handleSuggestionClick = (cmd: string) => {
    setCommand(cmd);
    setShowSuggestions(false);
  };

  return (
    <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
      <Typography variant="h6" gutterBottom>
        Natural Language Command
      </Typography>
      <form onSubmit={handleSubmit}>
        <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
          <Autocomplete
            freeSolo
            options={[...commandHistory, ...EXAMPLE_COMMANDS]}
            value={command}
            onChange={(_, newValue) => {
              if (newValue) setCommand(newValue);
            }}
            onInputChange={(_, newValue) => setCommand(newValue)}
            renderInput={(params) => (
              <TextField
                {...params}
                label="Enter a command (e.g., 'Deploy a WordPress stack')"
                variant="outlined"
                fullWidth
                disabled={loading}
                autoFocus
              />
            )}
            sx={{ flexGrow: 1 }}
          />
          <Button
            type="submit"
            variant="contained"
            color="primary"
            endIcon={<SendIcon />}
            disabled={loading || !command.trim()}
            sx={{ minWidth: 120 }}
          >
            {loading ? <CircularProgress size={22} /> : "Send"}
          </Button>
        </Stack>
      </form>

      <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
        <Tooltip title="Command History">
          <Chip
            icon={<HistoryIcon fontSize="small" />}
            label="History"
            variant="outlined"
            onClick={() => setShowHistory(!showHistory)}
            color={showHistory ? "primary" : "default"}
            size="small"
          />
        </Tooltip>
        <Tooltip title="Command Suggestions">
          <Chip
            icon={<LightbulbIcon fontSize="small" />}
            label="Suggestions"
            variant="outlined"
            onClick={() => setShowSuggestions(!showSuggestions)}
            color={showSuggestions ? "primary" : "default"}
            size="small"
          />
        </Tooltip>
      </Stack>

      <Collapse in={showHistory} timeout="auto" unmountOnExit>
        <Box sx={{ mt: 2, mb: 2 }}>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            Command History:
          </Typography>
          {commandHistory.length === 0 ? (
            <Typography variant="body2" color="text.secondary">
              No command history yet.
            </Typography>
          ) : (
            <List dense>
              {commandHistory.map((cmd, index) => (
                <ListItem
                  key={index}
                  button
                  onClick={() => handleHistoryItemClick(cmd)}
                  sx={{ py: 0.5 }}
                >
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    <HistoryIcon fontSize="small" />
                  </ListItemIcon>
                  <ListItemText primary={cmd} />
                  <Tooltip title="Run this command">
                    <IconButton
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation();
                        setCommand(cmd);
                        handleSubmit(e as any);
                      }}
                    >
                      <PlayArrowIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </ListItem>
              ))}
            </List>
          )}
        </Box>
      </Collapse>

      <Collapse in={showSuggestions} timeout="auto" unmountOnExit>
        <Box sx={{ mt: 2, mb: 2 }}>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            Suggested Commands:
          </Typography>
          <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1 }}>
            {EXAMPLE_COMMANDS.map((cmd, index) => (
              <Chip
                key={index}
                label={cmd}
                onClick={() => handleSuggestionClick(cmd)}
                variant="outlined"
                size="small"
                sx={{ m: 0.5 }}
              />
            ))}
          </Box>
        </Box>
      </Collapse>

      {error && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      )}
      {response && (
        <Box sx={{ mt: 2 }}>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            Response:
          </Typography>
          <Paper
            variant="outlined"
            sx={{
              p: 2,
              bgcolor: "#f9f9fa",
              fontFamily: "monospace",
              fontSize: "0.95em",
              whiteSpace: "pre-wrap",
              overflowX: "auto",
            }}
          >
            {response}
          </Paper>
        </Box>
      )}
    </Paper>
  );
};

export default NaturalLanguageInput;
