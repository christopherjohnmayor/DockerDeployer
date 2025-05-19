import React, { useEffect, useState } from "react";
import {
  Box,
  Paper,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Button,
  Stack,
  Alert,
  IconButton,
  Divider,
  Tooltip,
} from "@mui/material";
import AddCircleOutlineIcon from "@mui/icons-material/AddCircleOutline";
import DeleteIcon from "@mui/icons-material/Delete";
import { fetchSettings, saveSettings, Settings, LLMProvider } from "../api/settings";

const SettingsPage: React.FC = () => {
  const [llmProvider, setLlmProvider] = useState<LLMProvider>("ollama");
  const [liteLLMApiUrl, setLiteLLMApiUrl] = useState("");
  const [liteLLMApiKey, setLiteLLMApiKey] = useState("");
  const [openRouterApiUrl, setOpenRouterApiUrl] = useState("https://openrouter.ai/api/v1/chat/completions");
  const [openRouterApiKey, setOpenRouterApiKey] = useState("");
  const [secrets, setSecrets] = useState<{ key: string; value: string }[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    const loadSettings = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchSettings();
        // Ensure provider is always valid
        let provider: LLMProvider = (data.llm_provider as LLMProvider) || "ollama";
        if (!["ollama", "litellm", "openrouter"].includes(provider)) {
          provider = "ollama";
        }
        setLlmProvider(provider);
        // Map API URLs/keys for each provider
        if (provider === "openrouter") {
          setOpenRouterApiUrl(data.openrouter_api_url || "https://openrouter.ai/api/v1/chat/completions");
          setOpenRouterApiKey(data.openrouter_api_key || "");
          setLiteLLMApiUrl("");
          setLiteLLMApiKey("");
        } else {
          setLiteLLMApiUrl(data.llm_api_url || "");
          setLiteLLMApiKey(data.llm_api_key || "");
          setOpenRouterApiUrl("https://openrouter.ai/api/v1/chat/completions"); // Default for when not selected
          setOpenRouterApiKey("");
        }
        setSecrets(
          data.secrets
            ? Object.entries(data.secrets).map(([key, value]) => ({ key, value }))
            : []
        );
      } catch (err: any) {
        setError(
          err?.response?.data?.detail ||
            err?.message ||
            "Failed to load settings."
        );
      } finally {
        setLoading(false);
      }
    };
    loadSettings();
  }, []);

  const handleSecretChange = (idx: number, field: "key" | "value", value: string) => {
    setSecrets((prev) =>
      prev.map((s, i) => (i === idx ? { ...s, [field]: value } : s))
    );
  };

  const handleAddSecret = () => {
    setSecrets((prev) => [...prev, { key: "", value: "" }]);
  };

  const handleRemoveSecret = (idx: number) => {
    setSecrets((prev) => prev.filter((_, i) => i !== idx));
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      // Prepare settings object with correct fields for each provider
      let settingsPayload: Settings = {
        llm_provider: llmProvider,
        llm_api_url: "", // Default to empty string
        llm_api_key: "", // Default to empty string
        openrouter_api_url: "",
        openrouter_api_key: "",
        secrets: secrets.reduce((acc, s) => {
          if (s.key.trim()) acc[s.key.trim()] = s.value;
          return acc;
        }, {} as Record<string, string>),
      };

      if (llmProvider === "ollama") {
        settingsPayload.llm_api_url = liteLLMApiUrl;
      } else if (llmProvider === "litellm") {
        settingsPayload.llm_api_url = liteLLMApiUrl;
        settingsPayload.llm_api_key = liteLLMApiKey;
      } else if (llmProvider === "openrouter") {
        settingsPayload.openrouter_api_url = openRouterApiUrl || "https://openrouter.ai/api/v1/chat/completions";
        settingsPayload.openrouter_api_key = openRouterApiKey;
      }

      await saveSettings(settingsPayload);
      setSuccess("Settings saved successfully!");
    } catch (err: any) {
      setError(
        err?.response?.data?.detail ||
          err?.message ||
          "Failed to save settings."
      );
    } finally {
      setSaving(false);
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Paper elevation={2} sx={{ p: 4, maxWidth: 600, mx: "auto" }}>
        <Typography variant="h4" gutterBottom>
          Settings
        </Typography>
        <form onSubmit={handleSave}>
          <Stack spacing={3}>
            <FormControl fullWidth>
              <InputLabel id="llm-provider-label">LLM Provider</InputLabel>
              <Select
                labelId="llm-provider-label"
                value={llmProvider}
                label="LLM Provider"
                onChange={(e) => {
                  const val = e.target.value as LLMProvider;
                  // Always set to a valid value
                  if (["ollama", "litellm", "openrouter"].includes(val)) {
                    setLlmProvider(val);
                  } else {
                    setLlmProvider("ollama");
                  }
                }}
                disabled={loading}
              >
                <MenuItem value="ollama">Ollama (Local)</MenuItem>
                <MenuItem value="litellm">LiteLLM (API)</MenuItem>
                <MenuItem value="openrouter">OpenRouter</MenuItem>
              </Select>
            </FormControl>
            {llmProvider === "litellm" && (
              <>
                <TextField
                  label="LiteLLM API URL"
                  value={liteLLMApiUrl}
                  onChange={(e) => setLiteLLMApiUrl(e.target.value)}
                  fullWidth
                  required
                  disabled={loading}
                />
                <TextField
                  label="LiteLLM API Key"
                  value={liteLLMApiKey}
                  onChange={(e) => setLiteLLMApiKey(e.target.value)}
                  fullWidth
                  type="password"
                  autoComplete="off"
                  disabled={loading}
                />
              </>
            )}
            {llmProvider === "openrouter" && (
              <>
                <TextField
                  label="OpenRouter API URL"
                  value={openRouterApiUrl}
                  onChange={(e) => setOpenRouterApiUrl(e.target.value)}
                  fullWidth
                  required
                  disabled={loading}
                  placeholder="https://openrouter.ai/api/v1/chat/completions"
                />
                <TextField
                  label="OpenRouter API Key"
                  value={openRouterApiKey}
                  onChange={(e) => setOpenRouterApiKey(e.target.value)}
                  fullWidth
                  type="password"
                  autoComplete="off"
                  required
                  disabled={loading}
                />
              </>
            )}
            {llmProvider === "ollama" && (
              <TextField
                label="Ollama API URL"
                value={liteLLMApiUrl}
                onChange={(e) => setLiteLLMApiUrl(e.target.value)}
                fullWidth
                required
                disabled={loading}
                placeholder="http://localhost:11434/api/generate"
              />
            )}
            <Divider />
            <Typography variant="h6" gutterBottom>
              Secrets (Environment Variables)
            </Typography>
            <Stack spacing={2}>
              {secrets.map((s, idx) => (
                <Stack direction="row" spacing={1} key={idx} alignItems="center">
                  <TextField
                    label="Key"
                    value={s.key}
                    onChange={(e) => handleSecretChange(idx, "key", e.target.value)}
                    size="small"
                    sx={{ flex: 2 }}
                    disabled={loading}
                  />
                  <TextField
                    label="Value"
                    value={s.value}
                    onChange={(e) => handleSecretChange(idx, "value", e.target.value)}
                    size="small"
                    sx={{ flex: 3 }}
                    disabled={loading}
                  />
                  <Tooltip title="Remove">
                    <span>
                      <IconButton
                        onClick={() => handleRemoveSecret(idx)}
                        color="error"
                        size="small"
                        disabled={loading}
                      >
                        <DeleteIcon />
                      </IconButton>
                    </span>
                  </Tooltip>
                </Stack>
              ))}
              <Button
                startIcon={<AddCircleOutlineIcon />}
                onClick={handleAddSecret}
                disabled={loading}
                variant="outlined"
                size="small"
              >
                Add Secret
              </Button>
            </Stack>
            {error && <Alert severity="error">{error}</Alert>}
            {success && <Alert severity="success">{success}</Alert>}
            <Button
              type="submit"
              variant="contained"
              color="primary"
              disabled={saving || loading}
              sx={{ mt: 2 }}
            >
              {saving ? "Saving..." : "Save Settings"}
            </Button>
          </Stack>
        </form>
      </Paper>
    </Box>
  );
};

export default SettingsPage;
