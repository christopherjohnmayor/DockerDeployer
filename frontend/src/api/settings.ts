import axios from "axios";

export type LLMProvider = "ollama" | "litellm" | "openrouter";

export interface Settings {
  llm_provider: LLMProvider;
  llm_api_url: string;
  llm_api_key: string;
  openrouter_api_url?: string;
  openrouter_api_key?: string;
  secrets: Record<string, string>;
}

export async function fetchSettings(): Promise<Settings> {
  const res = await axios.get<Settings>("/api/settings");
  return res.data;
}

export async function saveSettings(settings: Settings): Promise<void> {
  await axios.post("/api/settings", settings);
}
