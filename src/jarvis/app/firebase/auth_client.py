from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv


load_dotenv()


class FirebaseAuthError(RuntimeError):
    """Raised when Firebase Authentication rejects a request."""


@dataclass(frozen=True)
class FirebaseSession:
    uid: str
    email: str
    id_token: str
    refresh_token: str
    expires_at: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "uid": self.uid,
            "email": self.email,
            "id_token": self.id_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.expires_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FirebaseSession":
        return cls(
            uid=str(data["uid"]),
            email=str(data["email"]),
            id_token=str(data["id_token"]),
            refresh_token=str(data["refresh_token"]),
            expires_at=int(data["expires_at"]),
        )


class FirebaseAuthClient:
    """Firebase Auth REST client for Jarvis desktop auth.

    This is safe for normal client-side email/password login because it uses
    Firebase Auth REST endpoints with the Web API key. It must not contain the
    Admin SDK service account.
    """

    AUTH_BASE_URL = "https://identitytoolkit.googleapis.com/v1"
    TOKEN_URL = "https://securetoken.googleapis.com/v1/token"

    def __init__(
        self,
        api_key: str | None = None,
        session_path: str | Path = "data/auth/session.json",
        timeout_seconds: int = 20,
    ) -> None:
        self.api_key = api_key or os.getenv("FIREBASE_WEB_API_KEY", "").strip()
        if not self.api_key:
            raise FirebaseAuthError(
                "Missing FIREBASE_WEB_API_KEY. Put it in .env or pass api_key manually."
            )

        self.session_path = Path(session_path)
        self.timeout_seconds = timeout_seconds

    def sign_up(self, email: str, password: str, display_name: str | None = None) -> FirebaseSession:
        email = self._clean_email(email)
        self._validate_password(password)

        payload: dict[str, Any] = {
            "email": email,
            "password": password,
            "returnSecureToken": True,
        }

        data = self._post("accounts:signUp", payload)
        session = self._session_from_auth_response(data, fallback_email=email)

        if display_name:
            self.update_profile(session.id_token, display_name=display_name)

        self.save_session(session)
        return session

    def sign_in(self, email: str, password: str) -> FirebaseSession:
        email = self._clean_email(email)
        self._validate_password(password)

        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True,
        }

        data = self._post("accounts:signInWithPassword", payload)
        session = self._session_from_auth_response(data, fallback_email=email)
        self.save_session(session)
        return session

    def refresh_session(self, session: FirebaseSession) -> FirebaseSession:
        url = f"{self.TOKEN_URL}?key={self.api_key}"
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": session.refresh_token,
        }

        response = requests.post(url, data=payload, timeout=self.timeout_seconds)
        data = self._parse_response(response)

        refreshed = FirebaseSession(
            uid=str(data["user_id"]),
            email=session.email,
            id_token=str(data["id_token"]),
            refresh_token=str(data["refresh_token"]),
            expires_at=int(time.time()) + int(data.get("expires_in", 3600)),
        )
        self.save_session(refreshed)
        return refreshed

    def get_valid_session(self) -> FirebaseSession | None:
        session = self.load_session()
        if session is None:
            return None

        if session.expires_at - int(time.time()) > 60:
            return session

        return self.refresh_session(session)

    def load_session(self) -> FirebaseSession | None:
        if not self.session_path.exists():
            return None

        try:
            data = json.loads(self.session_path.read_text(encoding="utf-8"))
            return FirebaseSession.from_dict(data)
        except Exception:
            return None

    def save_session(self, session: FirebaseSession) -> None:
        self.session_path.parent.mkdir(parents=True, exist_ok=True)
        self.session_path.write_text(
            json.dumps(session.to_dict(), indent=2),
            encoding="utf-8",
        )

    def save_external_session(
        self,
        uid: str,
        email: str,
        id_token: str,
        refresh_token: str = "",
        display_name: str = "",
        email_verified: bool = True,
    ) -> None:
        expires_at = time.time() + 55 * 60

        session = FirebaseSession(
            uid=uid,
            email=email,
            id_token=id_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
            display_name=display_name,
            email_verified=email_verified,
        )

        self._save_session(session)

    def logout(self) -> None:
        if self.session_path.exists():
            self.session_path.unlink()

    def update_profile(self, id_token: str, display_name: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "idToken": id_token,
            "returnSecureToken": True,
        }

        if display_name is not None:
            payload["displayName"] = display_name

        return self._post("accounts:update", payload)

    def send_password_reset_email(self, email: str) -> dict[str, Any]:
        payload = {
            "requestType": "PASSWORD_RESET",
            "email": self._clean_email(email),
        }
        return self._post("accounts:sendOobCode", payload)

    def _post(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.AUTH_BASE_URL}/{endpoint}?key={self.api_key}"
        response = requests.post(url, json=payload, timeout=self.timeout_seconds)
        return self._parse_response(response)

    @staticmethod
    def _parse_response(response: requests.Response) -> dict[str, Any]:
        try:
            data = response.json()
        except ValueError as exc:
            raise FirebaseAuthError(f"Firebase returned non-JSON response: {response.status_code}") from exc

        if response.ok:
            return data

        error = data.get("error", {})
        message = error.get("message", "UNKNOWN_FIREBASE_AUTH_ERROR")
        raise FirebaseAuthError(str(message))

    @staticmethod
    def _session_from_auth_response(data: dict[str, Any], fallback_email: str) -> FirebaseSession:
        return FirebaseSession(
            uid=str(data["localId"]),
            email=str(data.get("email") or fallback_email),
            id_token=str(data["idToken"]),
            refresh_token=str(data["refreshToken"]),
            expires_at=int(time.time()) + int(data.get("expiresIn", 3600)),
        )

    @staticmethod
    def _clean_email(email: str) -> str:
        cleaned = email.strip().lower()
        if "@" not in cleaned or "." not in cleaned:
            raise FirebaseAuthError("Invalid email address.")
        return cleaned

    @staticmethod
    def _validate_password(password: str) -> None:
        if len(password) < 6:
            raise FirebaseAuthError("Password must be at least 6 characters for Firebase Auth.")
