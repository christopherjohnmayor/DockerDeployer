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

/**
 * Example commands for suggestions in the natural language input component
 * These provide users with guidance on the types of commands they can use
 * @type {string[]}
 */
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

/**
 * Natural Language Input Component for Docker management commands.
 *
 * This component provides an intelligent text input interface that allows users to
 * enter natural language commands for Docker management operations. It leverages
 * AI/LLM integration to interpret and process user commands.
 *
 * **Key Features:**
 * - **Natural Language Processing**: Converts plain English commands to Docker operations
 * - **Command History**: Persistent storage of previous commands with localStorage
 * - **Smart Suggestions**: Pre-defined example commands for common operations
 * - **Auto-completion**: Combines history and suggestions in a searchable dropdown
 * - **Real-time Feedback**: Displays parsed action plans and error messages
 * - **Responsive Design**: Adapts to different screen sizes with flexible layout
 *
 * **Supported Command Types:**
 * - Container deployment: "Deploy a WordPress stack"
 * - Container management: "Stop all running containers"
 * - Template operations: "Create a LEMP stack with PHP 8.1"
 * - Resource queries: "Show container logs for nginx"
 * - System operations: "List all containers"
 *
 * **State Management:**
 * - Maintains command input state
 * - Tracks loading states during API calls
 * - Stores command history (max 10 items)
 * - Manages UI panel visibility (history/suggestions)
 * - Handles error and success response states
 *
 * @component
 * @example
 * ```tsx
 * // Basic usage in a dashboard
 * <NaturalLanguageInput />
 *
 * // In a container management page
 * <Box sx={{ mb: 3 }}>
 *   <NaturalLanguageInput />
 * </Box>
 * ```
 *
 * @returns {React.ReactElement} The rendered Natural Language Input component with
 *   autocomplete, history, suggestions, and response display
 */
const NaturalLanguageInput: React.FC = () => {
  const [command, setCommand] = useState("");
  const [response, setResponse] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [commandHistory, setCommandHistory] = useState<string[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);

  /**
   * Load command history from localStorage when the component mounts
   * This allows the user's command history to persist between sessions
   */
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

  /**
   * Save a command to the command history
   * Adds the command to the beginning of the history array, removes duplicates,
   * limits the history to 10 items, and persists to localStorage
   *
   * @param {string} cmd - The command to save to history
   */
  const saveCommandToHistory = (cmd: string) => {
    const newHistory = [cmd, ...commandHistory.filter((c) => c !== cmd)].slice(
      0,
      10
    );
    setCommandHistory(newHistory);
    localStorage.setItem("commandHistory", JSON.stringify(newHistory));
  };

  /**
   * Handle form submission for the natural language command
   * Sends the command to the backend API for processing and handles the response
   *
   * @param {React.FormEvent} e - The form submission event
   * @returns {Promise<void>}
   */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!command.trim()) return;

    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      saveCommandToHistory(command);
      const res = await axios.post("/nlp/parse", { command });
      setResponse(
        res.data?.action_plan
          ? JSON.stringify(res.data.action_plan, null, 2)
          : "No response from backend."
      );
    } catch (err: unknown) {
      const error = err as Error & {
        response?: {
          data?: {
            detail?: string;
          };
        };
      };

      setError(
        error?.response?.data?.detail ||
          error?.message ||
          "Failed to process command."
      );
    } finally {
      setLoading(false);
    }
  };

  /**
   * Handle clicking on a history item
   * Sets the command input to the selected history item and hides the history panel
   *
   * @param {string} cmd - The command from history to use
   */
  const handleHistoryItemClick = (cmd: string) => {
    setCommand(cmd);
    setShowHistory(false);
  };

  /**
   * Handle clicking on a suggestion
   * Sets the command input to the selected suggestion and hides the suggestions panel
   *
   * @param {string} cmd - The suggested command to use
   */
  const handleSuggestionClick = (cmd: string) => {
    setCommand(cmd);
    setShowSuggestions(false);
  };

  /**
   * Renders the Natural Language Input component with command input field,
   * history and suggestions panels, and response display
   *
   * @returns {JSX.Element} The rendered component
   */
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
              {commandHistory.map((cmd, i) => (
                <ListItem
                  key={`history-${i}-${cmd}`}
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
                      onClick={(e: React.MouseEvent) => {
                        e.stopPropagation();
                        setCommand(cmd);
                        // Create a synthetic form event
                        const formEvent = {
                          preventDefault: () => {},
                        } as React.FormEvent;
                        handleSubmit(formEvent);
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
            {EXAMPLE_COMMANDS.map((cmd, i) => (
              <Chip
                key={`suggestion-${i}-${cmd}`}
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
