from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

from jarvis.app.auth_manager import AuthManager


ROOT_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT_DIR / "data"
USERS_DIR = DATA_DIR / "users"


class ChatFileStore:
    """
    Local file-backed chat storage.

    Folder structure:
        data/users/<user_id>/
            profile.json
            chats/
                <chat_id>.json

    This prepares Jarvis for:
    - real chat history
    - per-user chat separation
    - future cloud upload/sync
    - future website admin dashboard
    """

    def __init__(self, auth: AuthManager) -> None:
        self.auth = auth
        USERS_DIR.mkdir(parents=True, exist_ok=True)

    def create_chat(self, title: str = "New Chat") -> dict[str, Any]:
        user_result = self._require_user()
        if not user_result["ok"]:
            return user_result

        user = user_result["data"]["user"]
        user_dir = self._user_dir(user["id"])
        chats_dir = user_dir / "chats"
        chats_dir.mkdir(parents=True, exist_ok=True)

        now = int(time.time())
        chat_id = f"chat_{now}_{self._safe_id(title)[:24]}"

        chat = {
            "id": chat_id,
            "title": self._clean_title(title),
            "user_id": user["id"],
            "user_email": user.get("email", ""),
            "created_at": now,
            "updated_at": now,
            "messages": [],
            "meta": {
                "source": "jarvis_desktop",
                "sync_status": "local_only",
                "uploaded_at": 0,
            },
        }

        self._write_json(chats_dir / f"{chat_id}.json", chat)
        self._write_profile(user)

        return self._ok("Chat created.", {"chat": self._chat_summary(chat)})

    def list_chats(self) -> dict[str, Any]:
        user_result = self._require_user()
        if not user_result["ok"]:
            return user_result

        user = user_result["data"]["user"]
        chats_dir = self._user_dir(user["id"]) / "chats"
        chats_dir.mkdir(parents=True, exist_ok=True)

        chats: list[dict[str, Any]] = []

        for path in chats_dir.glob("*.json"):
            try:
                chat = json.loads(path.read_text(encoding="utf-8"))
                chats.append(self._chat_summary(chat))
            except Exception:
                continue

        chats.sort(key=lambda item: int(item.get("updated_at", 0)), reverse=True)

        return self._ok("Chats loaded.", {"chats": chats})

    def load_chat(self, chat_id: str) -> dict[str, Any]:
        user_result = self._require_user()
        if not user_result["ok"]:
            return user_result

        user = user_result["data"]["user"]
        chat_path = self._chat_path(user["id"], chat_id)

        if not chat_path.exists():
            return self._fail("Chat not found.")

        try:
            chat = json.loads(chat_path.read_text(encoding="utf-8"))
        except Exception:
            return self._fail("Chat file is damaged or unreadable.")

        return self._ok("Chat loaded.", {"chat": chat})

    def save_chat(
        self,
        chat_id: str,
        title: str,
        messages: list[dict[str, Any]],
        model: str = "",
    ) -> dict[str, Any]:
        user_result = self._require_user()
        if not user_result["ok"]:
            return user_result

        user = user_result["data"]["user"]

        if not chat_id:
            create_result = self.create_chat(title)
            if not create_result["ok"]:
                return create_result
            chat_id = create_result["data"]["chat"]["id"]

        chat_path = self._chat_path(user["id"], chat_id)
        chat_path.parent.mkdir(parents=True, exist_ok=True)

        now = int(time.time())

        existing: dict[str, Any] = {}

        if chat_path.exists():
            try:
                existing = json.loads(chat_path.read_text(encoding="utf-8"))
            except Exception:
                existing = {}

        chat = {
            "id": chat_id,
            "title": self._clean_title(title),
            "user_id": user["id"],
            "user_email": user.get("email", ""),
            "created_at": int(existing.get("created_at", now)),
            "updated_at": now,
            "messages": self._clean_messages(messages),
            "meta": {
                **existing.get("meta", {}),
                "source": "jarvis_desktop",
                "last_model": model,
                "sync_status": existing.get("meta", {}).get("sync_status", "local_only"),
                "uploaded_at": int(existing.get("meta", {}).get("uploaded_at", 0)),
            },
        }

        self._write_json(chat_path, chat)
        self._write_profile(user)

        return self._ok("Chat saved.", {"chat": self._chat_summary(chat)})

    def delete_chat(self, chat_id: str) -> dict[str, Any]:
        user_result = self._require_user()
        if not user_result["ok"]:
            return user_result

        user = user_result["data"]["user"]
        chat_path = self._chat_path(user["id"], chat_id)

        if chat_path.exists():
            chat_path.unlink()

        return self._ok("Chat deleted.", {"chat_id": chat_id})

    def _require_user(self) -> dict[str, Any]:
        result = self.auth.get_current_user()

        if not result.get("ok"):
            return self._fail("You must be logged in to use chat storage.")

        return result

    def _write_profile(self, user: dict[str, Any]) -> None:
        user_dir = self._user_dir(user["id"])
        user_dir.mkdir(parents=True, exist_ok=True)

        profile = {
            "id": user.get("id", ""),
            "name": user.get("name", ""),
            "email": user.get("email", ""),
            "email_verified": bool(user.get("email_verified", False)),
            "updated_at": int(time.time()),
        }

        self._write_json(user_dir / "profile.json", profile)

    def _user_dir(self, user_id: str) -> Path:
        safe_user_id = self._safe_id(user_id)
        return USERS_DIR / safe_user_id

    def _chat_path(self, user_id: str, chat_id: str) -> Path:
        safe_chat_id = self._safe_id(chat_id)
        return self._user_dir(user_id) / "chats" / f"{safe_chat_id}.json"

    def _chat_summary(self, chat: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": chat.get("id", ""),
            "title": chat.get("title", "New Chat"),
            "time": self._format_time(int(chat.get("updated_at", 0))),
            "created_at": int(chat.get("created_at", 0)),
            "updated_at": int(chat.get("updated_at", 0)),
            "message_count": len(chat.get("messages", [])),
            "sync_status": chat.get("meta", {}).get("sync_status", "local_only"),
        }

    def _clean_messages(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        cleaned: list[dict[str, Any]] = []

        for message in messages:
            if not isinstance(message, dict):
                continue

            role = str(message.get("role", "")).strip()
            text = str(message.get("text", "")).strip()
            meta = str(message.get("meta", "")).strip()

            if not role or not text:
                continue

            cleaned.append(
                {
                    "id": message.get("id", f"msg_{int(time.time() * 1000)}"),
                    "role": role,
                    "text": text,
                    "meta": meta,
                    "created_at": int(message.get("created_at", time.time())),
                }
            )

        return cleaned

    def _clean_title(self, title: str) -> str:
        title = " ".join(str(title or "").strip().split())

        if not title:
            return "New Chat"

        return title[:80]

    def _safe_id(self, value: str) -> str:
        value = str(value or "").strip()

        if not value:
            return f"id_{int(time.time())}"

        value = re.sub(r"[^a-zA-Z0-9_\-]+", "_", value)
        value = value.strip("_")

        return value or f"id_{int(time.time())}"

    def _format_time(self, timestamp: int) -> str:
        if not timestamp:
            return "Unknown"

        now = int(time.time())
        diff = now - timestamp

        if diff < 60:
            return "Now"

        if diff < 3600:
            return f"{diff // 60}m ago"

        if diff < 86400:
            return f"{diff // 3600}h ago"

        return time.strftime("%d %b", time.localtime(timestamp))

    def _write_json(self, path: Path, data: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _ok(self, message: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        return {"ok": True, "message": message, "data": data or {}}

    def _fail(self, message: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        return {
            "ok": False,
            "message": message,
            "data": {
                "reply": message,
                "meta": "CHAT FILE STORE / FAILED",
                **(data or {}),
            },
        }