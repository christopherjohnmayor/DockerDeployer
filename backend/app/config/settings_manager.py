import os
import yaml
from typing import Optional, Dict, Any
from threading import Lock

class SettingsManager:
    """
    Manages loading and saving of application settings (LLM provider, API URL/key, secrets) to a YAML file.
    Thread-safe for basic use.
    """
    DEFAULT_PATH = os.path.abspath(
        os.getenv("DOCKERDEPLOYER_SETTINGS_PATH", os.path.join(os.path.dirname(__file__), "../../../config_repo/settings.yaml"))
    )

    def __init__(self, path: Optional[str] = None):
        self.path = path or self.DEFAULT_PATH
        self._lock = Lock()
        self._settings = None  # type: Optional[Dict[str, Any]]

    def load(self) -> Dict[str, Any]:
        with self._lock:
            if self._settings is not None:
                return self._settings
            if not os.path.exists(self.path):
                self._settings = self.default_settings()
                return self._settings
            with open(self.path, "r") as f:
                loaded = yaml.safe_load(f)
                if loaded is None:
                    self._settings = self.default_settings()
                else:
                    self._settings = loaded
            return self._settings

    def save(self, settings: Dict[str, Any]) -> None:
        with self._lock:
            print(f"DEBUG: Saving settings to {self.path}: {settings}")
            self._settings = settings
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, "w") as f:
                yaml.safe_dump(settings, f, default_flow_style=False)

    def get(self, key: str, default: Any = None) -> Any:
        settings = self.load()
        return settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        settings = self.load()
        settings[key] = value
        # Synchronize keys for OpenRouter and generic LLM
        if key == "openrouter_api_key":
            settings["llm_api_key"] = value
        elif key == "llm_api_key":
            settings["openrouter_api_key"] = value
        # Optionally, add logic for docker_context if needed in future
        self.save(settings)

    @staticmethod
    def default_settings() -> Dict[str, Any]:
        return {
            "llm_provider": "ollama",  # "ollama", "litellm", or "openrouter"
            "llm_api_url": "http://localhost:11434/api/generate",  # Default Ollama endpoint
            "llm_api_key": "",
            "openrouter_api_url": "https://openrouter.ai/api/v1/chat/completions",
            "openrouter_api_key": "",
            "docker_context": "default",
            "secrets": {}
        }
