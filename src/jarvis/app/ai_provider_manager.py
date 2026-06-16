from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jarvis.app.local_secret_store import LocalSecretStore


ROOT_DIR = Path(__file__).resolve().parents[3]
SETTINGS_DIR = ROOT_DIR / "data" / "settings"
PROVIDER_SETTINGS_FILE = SETTINGS_DIR / "ai_provider_settings.json"


DEFAULT_PROVIDER_SETTINGS: dict[str, Any] = {
    "active_provider": "llama",
    "providers": {
        "llama": {
            "label": "Local Llama / Ollama",
            "enabled": True,
            "base_url": "http://localhost:11434",
            "model": "llama3.1:8b",
            "requires_api_key": False,
        },
        "gemini": {
            "label": "Google Gemini",
            "enabled": False,
            "model": "gemini-2.5-flash",
            "requires_api_key": True,
        },
        "openai": {
            "label": "ChatGPT / OpenAI",
            "enabled": False,
            "model": "gpt-4.1-mini",
            "requires_api_key": True,
        },
    },
}


class AIProviderManager:
    """
    Stores AI provider settings.

    Providers:
    - llama: local Ollama
    - gemini: Google Gemini API
    - openai: ChatGPT/OpenAI API

    API keys are not stored here directly.
    They are stored through LocalSecretStore.
    """

    def __init__(self) -> None:
        SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
        self.secrets = LocalSecretStore()
        self.settings = self._load()

    def get_settings(self) -> dict[str, Any]:
        public = json.loads(json.dumps(self.settings))

        for provider_id, provider in public.get("providers", {}).items():
            provider["api_key_set"] = self.secrets.has_secret(self._secret_key(provider_id))
            provider.pop("api_key", None)

        return public

    def set_active_provider(self, provider_id: str) -> dict[str, Any]:
        provider_id = self._clean_provider(provider_id)

        if provider_id not in self.settings["providers"]:
            return self._fail(f"Unknown provider: {provider_id}")

        provider = self.settings["providers"][provider_id]

        if provider.get("requires_api_key") and not self.secrets.has_secret(self._secret_key(provider_id)):
            return self._fail(f"{provider['label']} requires an API key first.")

        self.settings["active_provider"] = provider_id
        self.settings["providers"][provider_id]["enabled"] = True
        self._save()

        return self._ok(
            "AI provider selected.",
            {
                "settings": self.get_settings(),
            },
        )

    def update_provider_config(
        self,
        provider_id: str,
        model: str | None = None,
        base_url: str | None = None,
    ) -> dict[str, Any]:
        provider_id = self._clean_provider(provider_id)

        if provider_id not in self.settings["providers"]:
            return self._fail(f"Unknown provider: {provider_id}")

        if model is not None:
            self.settings["providers"][provider_id]["model"] = str(model).strip()

        if base_url is not None:
            self.settings["providers"][provider_id]["base_url"] = str(base_url).strip()

        self._save()

        return self._ok(
            "Provider config saved.",
            {
                "settings": self.get_settings(),
            },
        )

    def set_api_key(self, provider_id: str, api_key: str) -> dict[str, Any]:
        provider_id = self._clean_provider(provider_id)
        api_key = str(api_key or "").strip()

        if provider_id not in self.settings["providers"]:
            return self._fail(f"Unknown provider: {provider_id}")

        if not api_key:
            return self._fail("API key is required.")

        self.secrets.set_secret(self._secret_key(provider_id), api_key)
        self.settings["providers"][provider_id]["enabled"] = True
        self._save()

        return self._ok(
            "API key saved locally.",
            {
                "settings": self.get_settings(),
            },
        )

    def clear_api_key(self, provider_id: str) -> dict[str, Any]:
        provider_id = self._clean_provider(provider_id)

        if provider_id not in self.settings["providers"]:
            return self._fail(f"Unknown provider: {provider_id}")

        self.secrets.delete_secret(self._secret_key(provider_id))

        if self.settings["active_provider"] == provider_id:
            self.settings["active_provider"] = "llama"

        self._save()

        return self._ok(
            "API key cleared.",
            {
                "settings": self.get_settings(),
            },
        )

    def _secret_key(self, provider_id: str) -> str:
        return f"ai_provider.{provider_id}.api_key"

    def _clean_provider(self, provider_id: str) -> str:
        provider_id = str(provider_id or "").strip().lower()

        aliases = {
            "chatgpt": "openai",
            "gpt": "openai",
            "openai": "openai",
            "gemini": "gemini",
            "google": "gemini",
            "llama": "llama",
            "ollama": "llama",
            "local": "llama",
        }

        return aliases.get(provider_id, provider_id)

    def _load(self) -> dict[str, Any]:
        if not PROVIDER_SETTINGS_FILE.exists():
            self._save_json(PROVIDER_SETTINGS_FILE, DEFAULT_PROVIDER_SETTINGS)
            return json.loads(json.dumps(DEFAULT_PROVIDER_SETTINGS))

        try:
            loaded = json.loads(PROVIDER_SETTINGS_FILE.read_text(encoding="utf-8"))
        except Exception:
            loaded = {}

        merged = json.loads(json.dumps(DEFAULT_PROVIDER_SETTINGS))

        if isinstance(loaded, dict):
            merged["active_provider"] = loaded.get("active_provider", merged["active_provider"])

            loaded_providers = loaded.get("providers", {})
            if isinstance(loaded_providers, dict):
                for provider_id, provider_config in loaded_providers.items():
                    if provider_id in merged["providers"] and isinstance(provider_config, dict):
                        merged["providers"][provider_id].update(provider_config)

        self._save_json(PROVIDER_SETTINGS_FILE, merged)
        return merged

    def _save(self) -> None:
        self._save_json(PROVIDER_SETTINGS_FILE, self.settings)

    def _save_json(self, path: Path, data: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(data, indent=2),
            encoding="utf-8",
        )

    def _ok(self, message: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        return {
            "ok": True,
            "message": message,
            "data": data or {},
        }

    def _fail(self, message: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        return {
            "ok": False,
            "message": message,
            "data": data or {},
        }