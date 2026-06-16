from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any

try:
    import win32crypt
except Exception:
    win32crypt = None


ROOT_DIR = Path(__file__).resolve().parents[3]
SECRETS_DIR = ROOT_DIR / "data" / "secrets"
SECRETS_FILE = SECRETS_DIR / "local_secrets.json"


class LocalSecretStore:
    """
    Windows-local secret storage.

    Used for:
    - Gemini API key
    - OpenAI / ChatGPT API key

    Uses Windows DPAPI through pywin32 when available.
    """

    def __init__(self) -> None:
        SECRETS_DIR.mkdir(parents=True, exist_ok=True)
        self.data = self._load()

    def set_secret(self, key: str, value: str) -> None:
        key = self._clean_key(key)
        value = str(value or "").strip()

        if not value:
            self.delete_secret(key)
            return

        self.data[key] = {
            "encrypted": self._protect(value),
            "dpapi": win32crypt is not None,
        }
        self._save()

    def get_secret(self, key: str) -> str:
        key = self._clean_key(key)
        item = self.data.get(key)

        if not item:
            return ""

        try:
            return self._unprotect(
                encrypted=str(item.get("encrypted", "")),
                dpapi=bool(item.get("dpapi", False)),
            )
        except Exception:
            return ""

    def delete_secret(self, key: str) -> None:
        key = self._clean_key(key)

        if key in self.data:
            del self.data[key]
            self._save()

    def has_secret(self, key: str) -> bool:
        return bool(self.get_secret(key))

    def _protect(self, value: str) -> str:
        raw = value.encode("utf-8")

        if win32crypt is None:
            return base64.b64encode(raw).decode("ascii")

        encrypted = win32crypt.CryptProtectData(raw, None, None, None, None, 0)
        return base64.b64encode(encrypted).decode("ascii")

    def _unprotect(self, encrypted: str, dpapi: bool) -> str:
        raw = base64.b64decode(encrypted.encode("ascii"))

        if not dpapi or win32crypt is None:
            return raw.decode("utf-8")

        decrypted = win32crypt.CryptUnprotectData(raw, None, None, None, 0)[1]
        return decrypted.decode("utf-8")

    def _load(self) -> dict[str, Any]:
        if not SECRETS_FILE.exists():
            return {}

        try:
            return json.loads(SECRETS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save(self) -> None:
        SECRETS_DIR.mkdir(parents=True, exist_ok=True)
        SECRETS_FILE.write_text(
            json.dumps(self.data, indent=2),
            encoding="utf-8",
        )

    def _clean_key(self, key: str) -> str:
        return str(key or "").strip().lower()