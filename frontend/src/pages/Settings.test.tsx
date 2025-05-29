import React from "react";
import {
  render,
  screen,
  fireEvent,
  waitFor,
  act,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ThemeProvider } from "@mui/material/styles";
import { createTheme } from "@mui/material/styles";
import axios from "axios";
import SettingsPage from "./Settings";
import { Settings, LLMProvider } from "../api/settings";

// Mock axios
jest.mock("axios");
const mockedAxios = axios as jest.Mocked<typeof axios>;

// Mock Material-UI theme
const theme = createTheme();

// Test wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ThemeProvider theme={theme}>{children}</ThemeProvider>
);

describe("Settings Component", () => {
  const mockSettings: Settings = {
    llm_provider: "openrouter" as LLMProvider,
    llm_api_url: "http://localhost:11434/api/generate",
    llm_api_key: "test-api-key",
    llm_model: "meta-llama/llama-3.2-3b-instruct:free",
    openrouter_api_url: "https://openrouter.ai/api/v1/chat/completions",
    openrouter_api_key: "test-openrouter-key",
    secrets: {
      TEST_SECRET: "test-value",
      ANOTHER_SECRET: "another-value",
    },
  };

  beforeEach(() => {
    jest.clearAllMocks();
    // Mock successful settings fetch by default
    mockedAxios.get.mockResolvedValue({ data: mockSettings });
    mockedAxios.post.mockResolvedValue({ data: {} });
  });

  afterEach(() => {
    jest.clearAllTimers();
  });

  describe("Component Rendering", () => {
    it("renders settings page with correct title", async () => {
      await act(async () => {
        render(
          <TestWrapper>
            <SettingsPage />
          </TestWrapper>
        );
      });

      expect(screen.getByText("Settings")).toBeInTheDocument();
    });

    it("renders all form sections", async () => {
      await act(async () => {
        render(
          <TestWrapper>
            <SettingsPage />
          </TestWrapper>
        );
      });

      await waitFor(() => {
        expect(screen.getByLabelText("LLM Provider")).toBeInTheDocument();
        expect(screen.getByLabelText("Model")).toBeInTheDocument();
        expect(
          screen.getByText("Secrets (Environment Variables)")
        ).toBeInTheDocument();
        expect(
          screen.getByRole("button", { name: /save settings/i })
        ).toBeInTheDocument();
      });
    });

    it("renders provider-specific fields based on selection", async () => {
      await act(async () => {
        render(
          <TestWrapper>
            <SettingsPage />
          </TestWrapper>
        );
      });

      await waitFor(() => {
        // Should show OpenRouter fields since mockSettings has openrouter provider
        expect(screen.getByLabelText("OpenRouter API URL")).toBeInTheDocument();
        expect(screen.getByLabelText("OpenRouter API Key")).toBeInTheDocument();
      });
    });
  });

  describe("Settings Loading", () => {
    it("loads settings on component mount", async () => {
      await act(async () => {
        render(
          <TestWrapper>
            <SettingsPage />
          </TestWrapper>
        );
      });

      await waitFor(() => {
        expect(mockedAxios.get).toHaveBeenCalledWith("/api/settings");
      });
    });

    it("displays loaded settings correctly", async () => {
      await act(async () => {
        render(
          <TestWrapper>
            <SettingsPage />
          </TestWrapper>
        );
      });

      await waitFor(() => {
        const modelInput = screen.getByDisplayValue(
          "meta-llama/llama-3.2-3b-instruct:free"
        );
        expect(modelInput).toBeInTheDocument();

        const openrouterUrlInput = screen.getByDisplayValue(
          "https://openrouter.ai/api/v1/chat/completions"
        );
        expect(openrouterUrlInput).toBeInTheDocument();

        const openrouterKeyInput = screen.getByDisplayValue(
          "test-openrouter-key"
        );
        expect(openrouterKeyInput).toBeInTheDocument();
      });
    });

    it("handles settings loading error", async () => {
      const errorMessage = "Failed to load settings";
      mockedAxios.get.mockRejectedValue({
        response: { data: { detail: errorMessage } },
      });

      await act(async () => {
        render(
          <TestWrapper>
            <SettingsPage />
          </TestWrapper>
        );
      });

      await waitFor(() => {
        expect(screen.getByText(errorMessage)).toBeInTheDocument();
      });
    });

    it("handles network error during loading", async () => {
      mockedAxios.get.mockRejectedValue(new Error("Network error"));

      await act(async () => {
        render(
          <TestWrapper>
            <SettingsPage />
          </TestWrapper>
        );
      });

      await waitFor(() => {
        expect(screen.getByText("Network error")).toBeInTheDocument();
      });
    });

    it("handles malformed response during loading", async () => {
      mockedAxios.get.mockRejectedValue({});

      await act(async () => {
        render(
          <TestWrapper>
            <SettingsPage />
          </TestWrapper>
        );
      });

      await waitFor(() => {
        expect(
          screen.getByText("Failed to load settings.")
        ).toBeInTheDocument();
      });
    });
  });

  describe("LLM Provider Selection", () => {
    it("defaults to llama4 maverick :free model", async () => {
      const settingsWithoutModel = { ...mockSettings };
      delete (settingsWithoutModel as any).llm_model;
      mockedAxios.get.mockResolvedValue({ data: settingsWithoutModel });

      await act(async () => {
        render(
          <TestWrapper>
            <SettingsPage />
          </TestWrapper>
        );
      });

      await waitFor(() => {
        const modelInput = screen.getByDisplayValue(
          "meta-llama/llama-3.2-3b-instruct:free"
        );
        expect(modelInput).toBeInTheDocument();
      });
    });

    it("changes provider selection correctly", async () => {
      const user = userEvent.setup();

      await act(async () => {
        render(
          <TestWrapper>
            <SettingsPage />
          </TestWrapper>
        );
      });

      await waitFor(() => {
        expect(screen.getByLabelText("LLM Provider")).toBeInTheDocument();
      });

      // Click on the provider select
      const providerSelect = screen.getByLabelText("LLM Provider");
      await act(async () => {
        await user.click(providerSelect);
      });

      // Select ollama option
      await act(async () => {
        const ollamaOption = screen.getByText("Ollama (Local)");
        await user.click(ollamaOption);
      });

      await waitFor(() => {
        // Should now show Ollama API URL field
        expect(screen.getByLabelText("Ollama API URL")).toBeInTheDocument();
      });
    });

    it("handles invalid provider gracefully", async () => {
      const invalidSettings = {
        ...mockSettings,
        llm_provider: "invalid-provider" as LLMProvider,
      };
      mockedAxios.get.mockResolvedValue({ data: invalidSettings });

      await act(async () => {
        render(
          <TestWrapper>
            <SettingsPage />
          </TestWrapper>
        );
      });

      await waitFor(() => {
        // Should default to ollama for invalid provider
        const providerSelect = screen.getByLabelText("LLM Provider");
        expect(providerSelect).toHaveValue("ollama");
      });
    });

    it("shows correct fields for ollama provider", async () => {
      const ollamaSettings = {
        ...mockSettings,
        llm_provider: "ollama" as LLMProvider,
      };
      mockedAxios.get.mockResolvedValue({ data: ollamaSettings });

      await act(async () => {
        render(
          <TestWrapper>
            <SettingsPage />
          </TestWrapper>
        );
      });

      await waitFor(() => {
        expect(screen.getByLabelText("Ollama API URL")).toBeInTheDocument();
        expect(
          screen.queryByLabelText("LiteLLM API Key")
        ).not.toBeInTheDocument();
        expect(
          screen.queryByLabelText("OpenRouter API URL")
        ).not.toBeInTheDocument();
      });
    });

    it("shows correct fields for litellm provider", async () => {
      const litellmSettings = {
        ...mockSettings,
        llm_provider: "litellm" as LLMProvider,
      };
      mockedAxios.get.mockResolvedValue({ data: litellmSettings });

      await act(async () => {
        render(
          <TestWrapper>
            <SettingsPage />
          </TestWrapper>
        );
      });

      await waitFor(() => {
        expect(screen.getByLabelText("LiteLLM API URL")).toBeInTheDocument();
        expect(screen.getByLabelText("LiteLLM API Key")).toBeInTheDocument();
        expect(
          screen.queryByLabelText("OpenRouter API URL")
        ).not.toBeInTheDocument();
      });
    });

    it("shows correct fields for openrouter provider", async () => {
      await act(async () => {
        render(
          <TestWrapper>
            <SettingsPage />
          </TestWrapper>
        );
      });

      await waitFor(() => {
        expect(screen.getByLabelText("OpenRouter API URL")).toBeInTheDocument();
        expect(screen.getByLabelText("OpenRouter API Key")).toBeInTheDocument();
        expect(
          screen.queryByLabelText("LiteLLM API Key")
        ).not.toBeInTheDocument();
      });
    });
  });

  describe("Secrets Management", () => {
    it("displays existing secrets correctly", async () => {
      await act(async () => {
        render(
          <TestWrapper>
            <SettingsPage />
          </TestWrapper>
        );
      });

      await waitFor(() => {
        expect(screen.getByDisplayValue("TEST_SECRET")).toBeInTheDocument();
        expect(screen.getByDisplayValue("test-value")).toBeInTheDocument();
        expect(screen.getByDisplayValue("ANOTHER_SECRET")).toBeInTheDocument();
        expect(screen.getByDisplayValue("another-value")).toBeInTheDocument();
      });
    });

    it("adds new secret when Add Secret button is clicked", async () => {
      const user = userEvent.setup();

      await act(async () => {
        render(
          <TestWrapper>
            <SettingsPage />
          </TestWrapper>
        );
      });

      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: /add secret/i })
        ).toBeInTheDocument();
      });

      const addButton = screen.getByRole("button", { name: /add secret/i });
      await act(async () => {
        await user.click(addButton);
      });

      await waitFor(() => {
        const keyInputs = screen.getAllByLabelText("Key");
        const valueInputs = screen.getAllByLabelText("Value");
        // Should have 3 secrets now (2 existing + 1 new)
        expect(keyInputs).toHaveLength(3);
        expect(valueInputs).toHaveLength(3);
      });
    });

    it("removes secret when delete button is clicked", async () => {
      const user = userEvent.setup();

      await act(async () => {
        render(
          <TestWrapper>
            <SettingsPage />
          </TestWrapper>
        );
      });

      await waitFor(() => {
        const deleteButtons = screen.getAllByTestId("DeleteIcon");
        expect(deleteButtons).toHaveLength(2);
      });

      const deleteButtons = screen.getAllByTestId("DeleteIcon");
      await act(async () => {
        await user.click(deleteButtons[0].closest("button")!);
      });

      await waitFor(() => {
        const remainingDeleteButtons = screen.getAllByTestId("DeleteIcon");
        expect(remainingDeleteButtons).toHaveLength(1);
        // First secret should be removed
        expect(
          screen.queryByDisplayValue("TEST_SECRET")
        ).not.toBeInTheDocument();
      });
    });

    it("updates secret key when input changes", async () => {
      const user = userEvent.setup();

      await act(async () => {
        render(
          <TestWrapper>
            <SettingsPage />
          </TestWrapper>
        );
      });

      await waitFor(() => {
        expect(screen.getByDisplayValue("TEST_SECRET")).toBeInTheDocument();
      });

      const keyInput = screen.getByDisplayValue("TEST_SECRET");
      await act(async () => {
        await user.clear(keyInput);
        await user.type(keyInput, "UPDATED_SECRET");
      });

      await waitFor(() => {
        expect(screen.getByDisplayValue("UPDATED_SECRET")).toBeInTheDocument();
      });
    });

    it("updates secret value when input changes", async () => {
      const user = userEvent.setup();

      await act(async () => {
        render(
          <TestWrapper>
            <SettingsPage />
          </TestWrapper>
        );
      });

      await waitFor(() => {
        expect(screen.getByDisplayValue("test-value")).toBeInTheDocument();
      });

      const valueInput = screen.getByDisplayValue("test-value");
      await act(async () => {
        await user.clear(valueInput);
        await user.type(valueInput, "updated-value");
      });

      await waitFor(() => {
        expect(screen.getByDisplayValue("updated-value")).toBeInTheDocument();
      });
    });

    it("handles empty secrets array", async () => {
      const settingsWithoutSecrets = {
        ...mockSettings,
        secrets: {},
      };
      mockedAxios.get.mockResolvedValue({ data: settingsWithoutSecrets });

      await act(async () => {
        render(
          <TestWrapper>
            <SettingsPage />
          </TestWrapper>
        );
      });

      await waitFor(() => {
        const keyInputs = screen.queryAllByLabelText("Key");
        expect(keyInputs).toHaveLength(0);
        expect(
          screen.getByRole("button", { name: /add secret/i })
        ).toBeInTheDocument();
      });
    });
  });

  describe("Form Submission", () => {
    it("saves settings successfully", async () => {
      const user = userEvent.setup();

      await act(async () => {
        render(
          <TestWrapper>
            <SettingsPage />
          </TestWrapper>
        );
      });

      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: /save settings/i })
        ).toBeInTheDocument();
      });

      const saveButton = screen.getByRole("button", { name: /save settings/i });
      await act(async () => {
        await user.click(saveButton);
      });

      await waitFor(() => {
        expect(mockedAxios.post).toHaveBeenCalledWith(
          "/api/settings",
          expect.objectContaining({
            llm_provider: "openrouter",
            llm_model: "meta-llama/llama-3.2-3b-instruct:free",
            openrouter_api_url: "https://openrouter.ai/api/v1/chat/completions",
            openrouter_api_key: "test-openrouter-key",
            secrets: {
              TEST_SECRET: "test-value",
              ANOTHER_SECRET: "another-value",
            },
          })
        );
      });

      await waitFor(() => {
        expect(
          screen.getByText("Settings saved successfully!")
        ).toBeInTheDocument();
      });
    });

    it("handles save error", async () => {
      const user = userEvent.setup();
      const errorMessage = "Failed to save settings";
      mockedAxios.post.mockRejectedValue({
        response: { data: { detail: errorMessage } },
      });

      await act(async () => {
        render(
          <TestWrapper>
            <SettingsPage />
          </TestWrapper>
        );
      });

      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: /save settings/i })
        ).toBeInTheDocument();
      });

      const saveButton = screen.getByRole("button", { name: /save settings/i });
      await act(async () => {
        await user.click(saveButton);
      });

      await waitFor(() => {
        expect(screen.getByText(errorMessage)).toBeInTheDocument();
      });
    });

    it("shows saving state during submission", async () => {
      const user = userEvent.setup();
      // Mock a delayed response
      mockedAxios.post.mockImplementation(
        () =>
          new Promise((resolve) => setTimeout(() => resolve({ data: {} }), 100))
      );

      await act(async () => {
        render(
          <TestWrapper>
            <SettingsPage />
          </TestWrapper>
        );
      });

      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: /save settings/i })
        ).toBeInTheDocument();
      });

      const saveButton = screen.getByRole("button", { name: /save settings/i });
      await act(async () => {
        await user.click(saveButton);
      });

      // Should show saving state
      expect(screen.getByText("Saving...")).toBeInTheDocument();
      expect(saveButton).toBeDisabled();

      // Wait for completion
      await waitFor(
        () => {
          expect(
            screen.getByText("Settings saved successfully!")
          ).toBeInTheDocument();
        },
        { timeout: 200 }
      );
    });

    it("filters out empty secret keys during save", async () => {
      const user = userEvent.setup();

      await act(async () => {
        render(
          <TestWrapper>
            <SettingsPage />
          </TestWrapper>
        );
      });

      // Add a new secret with empty key
      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: /add secret/i })
        ).toBeInTheDocument();
      });

      const addButton = screen.getByRole("button", { name: /add secret/i });
      await act(async () => {
        await user.click(addButton);
      });

      // Save without filling the new secret
      const saveButton = screen.getByRole("button", { name: /save settings/i });
      await act(async () => {
        await user.click(saveButton);
      });

      await waitFor(() => {
        expect(mockedAxios.post).toHaveBeenCalledWith(
          "/api/settings",
          expect.objectContaining({
            secrets: {
              TEST_SECRET: "test-value",
              ANOTHER_SECRET: "another-value",
              // Empty key should be filtered out
            },
          })
        );
      });
    });

    it("prepares correct payload for ollama provider", async () => {
      const user = userEvent.setup();
      const ollamaSettings = {
        ...mockSettings,
        llm_provider: "ollama" as LLMProvider,
      };
      mockedAxios.get.mockResolvedValue({ data: ollamaSettings });

      await act(async () => {
        render(
          <TestWrapper>
            <SettingsPage />
          </TestWrapper>
        );
      });

      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: /save settings/i })
        ).toBeInTheDocument();
      });

      const saveButton = screen.getByRole("button", { name: /save settings/i });
      await act(async () => {
        await user.click(saveButton);
      });

      await waitFor(() => {
        expect(mockedAxios.post).toHaveBeenCalledWith(
          "/api/settings",
          expect.objectContaining({
            llm_provider: "ollama",
            llm_api_url: "http://localhost:11434/api/generate",
            llm_api_key: "",
            openrouter_api_url: "",
            openrouter_api_key: "",
          })
        );
      });
    });

    it("prepares correct payload for litellm provider", async () => {
      const user = userEvent.setup();
      const litellmSettings = {
        ...mockSettings,
        llm_provider: "litellm" as LLMProvider,
      };
      mockedAxios.get.mockResolvedValue({ data: litellmSettings });

      await act(async () => {
        render(
          <TestWrapper>
            <SettingsPage />
          </TestWrapper>
        );
      });

      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: /save settings/i })
        ).toBeInTheDocument();
      });

      const saveButton = screen.getByRole("button", { name: /save settings/i });
      await act(async () => {
        await user.click(saveButton);
      });

      await waitFor(() => {
        expect(mockedAxios.post).toHaveBeenCalledWith(
          "/api/settings",
          expect.objectContaining({
            llm_provider: "litellm",
            llm_api_url: "http://localhost:11434/api/generate",
            llm_api_key: "test-api-key",
            openrouter_api_url: "",
            openrouter_api_key: "",
          })
        );
      });
    });
  });

  describe("Form Validation and Edge Cases", () => {
    it("disables form during loading", async () => {
      // Mock a delayed response
      mockedAxios.get.mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(() => resolve({ data: mockSettings }), 100)
          )
      );

      await act(async () => {
        render(
          <TestWrapper>
            <SettingsPage />
          </TestWrapper>
        );
      });

      // Form should be disabled during loading
      const saveButton = screen.getByRole("button", { name: /save settings/i });
      expect(saveButton).toBeDisabled();

      // Wait for loading to complete
      await waitFor(
        () => {
          expect(saveButton).not.toBeDisabled();
        },
        { timeout: 200 }
      );
    });

    it("handles form submission with network error", async () => {
      const user = userEvent.setup();
      mockedAxios.post.mockRejectedValue(new Error("Network error"));

      await act(async () => {
        render(
          <TestWrapper>
            <SettingsPage />
          </TestWrapper>
        );
      });

      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: /save settings/i })
        ).toBeInTheDocument();
      });

      const saveButton = screen.getByRole("button", { name: /save settings/i });
      await act(async () => {
        await user.click(saveButton);
      });

      await waitFor(() => {
        expect(screen.getByText("Network error")).toBeInTheDocument();
      });
    });

    it("handles form submission with malformed error", async () => {
      const user = userEvent.setup();
      mockedAxios.post.mockRejectedValue({});

      await act(async () => {
        render(
          <TestWrapper>
            <SettingsPage />
          </TestWrapper>
        );
      });

      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: /save settings/i })
        ).toBeInTheDocument();
      });

      const saveButton = screen.getByRole("button", { name: /save settings/i });
      await act(async () => {
        await user.click(saveButton);
      });

      await waitFor(() => {
        expect(
          screen.getByText("Failed to save settings.")
        ).toBeInTheDocument();
      });
    });

    it("clears success message when starting new save", async () => {
      const user = userEvent.setup();

      await act(async () => {
        render(
          <TestWrapper>
            <SettingsPage />
          </TestWrapper>
        );
      });

      // First successful save
      const saveButton = screen.getByRole("button", { name: /save settings/i });
      await act(async () => {
        await user.click(saveButton);
      });

      await waitFor(() => {
        expect(
          screen.getByText("Settings saved successfully!")
        ).toBeInTheDocument();
      });

      // Second save should clear success message
      await act(async () => {
        await user.click(saveButton);
      });

      // Wait for success message to be cleared during saving
      await waitFor(() => {
        expect(
          screen.queryByText("Settings saved successfully!")
        ).not.toBeInTheDocument();
      });
    });

    it("clears error message when starting new save", async () => {
      const user = userEvent.setup();
      mockedAxios.post.mockRejectedValueOnce(new Error("First error"));

      await act(async () => {
        render(
          <TestWrapper>
            <SettingsPage />
          </TestWrapper>
        );
      });

      // First failed save
      const saveButton = screen.getByRole("button", { name: /save settings/i });
      await act(async () => {
        await user.click(saveButton);
      });

      await waitFor(() => {
        expect(screen.getByText("First error")).toBeInTheDocument();
      });

      // Second save should clear error message
      mockedAxios.post.mockResolvedValueOnce({ data: {} });
      await act(async () => {
        await user.click(saveButton);
      });

      // Error message should be cleared during saving
      expect(screen.queryByText("First error")).not.toBeInTheDocument();
    });
  });
});
