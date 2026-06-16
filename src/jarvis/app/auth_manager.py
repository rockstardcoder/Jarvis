from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from jarvis.app.email_sender import EmailSender


ROOT_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT_DIR / "data"
AUTH_DIR = DATA_DIR / "auth"

USERS_FILE = AUTH_DIR / "users.json"
SESSION_FILE = AUTH_DIR / "session.json"
CODES_FILE = AUTH_DIR / "verification_codes.json"

CODE_TTL_SECONDS = 10 * 60


class AuthManager:
    def __init__(self) -> None:
        AUTH_DIR.mkdir(parents=True, exist_ok=True)

        self.email_sender = EmailSender()

        self.users = self._load_users()
        self.codes = self._load_codes()

    def get_current_user(self) -> dict[str, Any]:
        session = self._read_json(SESSION_FILE, {})

        email = str(session.get("email", "")).strip().lower()

        if not email:
            return self._fail("No user signed in.", meta="AUTH / NOT SIGNED IN")

        user = self.users.get(email)

        if not user:
            return self._fail("Signed-in user does not exist.", meta="AUTH / INVALID SESSION")

        return self._ok(
            "Current user loaded.",
            {
                "user": self._public_user(user),
            },
        )

    def start_signup(self, name: str, email: str, password: str) -> dict[str, Any]:
        name = str(name or "").strip()
        email = self._normalize_email(email)
        password = str(password or "")

        if not name:
            return self._fail("Name is required.", meta="AUTH / SIGNUP FAILED")

        if not self._valid_email(email):
            return self._fail("Valid email is required.", meta="AUTH / SIGNUP FAILED")

        if len(password) < 6:
            return self._fail("Password must be at least 6 characters.", meta="AUTH / SIGNUP FAILED")

        existing = self.users.get(email)

        if existing and existing.get("email_verified"):
            return self._fail("An account with this email already exists.", meta="AUTH / SIGNUP FAILED")

        user = existing or {
            "id": str(uuid.uuid4()),
            "name": name,
            "email": email,
            "password_hash": "",
            "email_verified": False,
            "role": "user",
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "last_login_at": "",
        }

        user["name"] = name
        user["password_hash"] = self._hash_password(password)
        user["updated_at"] = datetime.now().isoformat(timespec="seconds")

        self.users[email] = user
        self._save_users()

        code = self._create_code(
            email=email,
            purpose="signup",
            extra={},
        )

        return self._ok(
    f"Verification code is: {code}",
    {
        "reply": f"Verification code is: {code}",
        "meta": "AUTH / SIGNUP DEV CODE",
        "email": email,
        "verification_code": code,
    },
)

    def verify_signup(self, email: str, code: str) -> dict[str, Any]:
        email = self._normalize_email(email)
        code = str(code or "").strip()

        check = self._verify_code(email=email, code=code, purpose="signup")

        if not check["ok"]:
            return check

        user = self.users.get(email)

        if not user:
            return self._fail("User not found.", meta="AUTH / VERIFY FAILED")

        user["email_verified"] = True
        user["verified_at"] = datetime.now().isoformat(timespec="seconds")
        self.users[email] = user
        self._save_users()

        self._delete_code(email=email, purpose="signup")
        self._save_session(email)

        return self._ok(
            "Account verified and signed in.",
            {
                "reply": "Account verified and signed in.",
                "meta": "AUTH / VERIFIED",
                "user": self._public_user(user),
            },
        )

    def login(self, email: str, password: str) -> dict[str, Any]:
        email = self._normalize_email(email)
        password = str(password or "")

        user = self.users.get(email)

        if not user:
            return self._fail("Invalid email or password.", meta="AUTH / LOGIN FAILED")

        if not self._verify_password(password, user.get("password_hash", "")):
            return self._fail("Invalid email or password.", meta="AUTH / LOGIN FAILED")

        if not user.get("email_verified"):
            return self._fail("Please verify your email before logging in.", meta="AUTH / EMAIL NOT VERIFIED")

        user["last_login_at"] = datetime.now().isoformat(timespec="seconds")
        self.users[email] = user
        self._save_users()
        self._save_session(email)

        return self._ok(
            "Logged in.",
            {
                "reply": "Logged in.",
                "meta": "AUTH / LOGIN",
                "user": self._public_user(user),
            },
        )

    def logout(self) -> dict[str, Any]:
        self._write_json(SESSION_FILE, {})

        return self._ok(
            "Logged out.",
            {
                "reply": "Logged out.",
                "meta": "AUTH / LOGOUT",
            },
        )

    def update_name(self, name: str) -> dict[str, Any]:
        current = self.get_current_user()

        if not current["ok"]:
            return current

        name = str(name or "").strip()

        if not name:
            return self._fail("Name is required.", meta="AUTH / UPDATE NAME FAILED")

        email = current["data"]["user"]["email"]
        user = self.users[email]
        user["name"] = name
        user["updated_at"] = datetime.now().isoformat(timespec="seconds")

        self.users[email] = user
        self._save_users()

        return self._ok(
            "Name updated.",
            {
                "reply": "Name updated.",
                "meta": "AUTH / UPDATE NAME",
                "user": self._public_user(user),
            },
        )

    def start_change_email(self, new_email: str, password: str) -> dict[str, Any]:
        current = self.get_current_user()

        if not current["ok"]:
            return current

        old_email = current["data"]["user"]["email"]
        user = self.users[old_email]

        new_email = self._normalize_email(new_email)
        password = str(password or "")

        if not self._valid_email(new_email):
            return self._fail("Valid new email is required.", meta="AUTH / CHANGE EMAIL FAILED")

        if new_email in self.users:
            return self._fail("That email is already in use.", meta="AUTH / CHANGE EMAIL FAILED")

        if not self._verify_password(password, user.get("password_hash", "")):
            return self._fail("Password is incorrect.", meta="AUTH / CHANGE EMAIL FAILED")

        code = self._create_code(
            email=new_email,
            purpose="change_email",
            extra={
                "old_email": old_email,
            },
        )

        email_result = self.email_sender.send_change_email_code(
            to_email=new_email,
            code=code,
            name=user.get("name", "there"),
        )

        if not email_result.get("ok"):
            return {
                "ok": False,
                "message": email_result.get("message", "Could not send change-email code."),
                "data": {
                    "reply": email_result.get("message", "Could not send change-email code."),
                    "meta": "AUTH / EMAIL FAILED",
                },
            }

        return self._ok(
            "Email-change code sent to your new email.",
            {
                "reply": "Email-change code sent to your new email.",
                "meta": "AUTH / CHANGE EMAIL CODE SENT",
                "new_email": new_email,
            },
        )

    def verify_change_email(self, new_email: str, code: str) -> dict[str, Any]:
        new_email = self._normalize_email(new_email)
        code = str(code or "").strip()

        check = self._verify_code(email=new_email, code=code, purpose="change_email")

        if not check["ok"]:
            return check

        old_email = check["data"].get("extra", {}).get("old_email")

        if not old_email or old_email not in self.users:
            return self._fail("Original account not found.", meta="AUTH / CHANGE EMAIL FAILED")

        user = self.users.pop(old_email)
        user["email"] = new_email
        user["updated_at"] = datetime.now().isoformat(timespec="seconds")

        self.users[new_email] = user
        self._save_users()

        self._delete_code(email=new_email, purpose="change_email")
        self._save_session(new_email)

        return self._ok(
            "Email changed.",
            {
                "reply": "Email changed.",
                "meta": "AUTH / CHANGE EMAIL",
                "user": self._public_user(user),
            },
        )

    def change_password(self, current_password: str, new_password: str) -> dict[str, Any]:
        current = self.get_current_user()

        if not current["ok"]:
            return current

        email = current["data"]["user"]["email"]
        user = self.users[email]

        current_password = str(current_password or "")
        new_password = str(new_password or "")

        if not self._verify_password(current_password, user.get("password_hash", "")):
            return self._fail("Current password is incorrect.", meta="AUTH / CHANGE PASSWORD FAILED")

        if len(new_password) < 6:
            return self._fail("New password must be at least 6 characters.", meta="AUTH / CHANGE PASSWORD FAILED")

        user["password_hash"] = self._hash_password(new_password)
        user["updated_at"] = datetime.now().isoformat(timespec="seconds")

        self.users[email] = user
        self._save_users()

        return self._ok(
            "Password changed.",
            {
                "reply": "Password changed.",
                "meta": "AUTH / CHANGE PASSWORD",
            },
        )

    def start_forgot_password(self, email: str) -> dict[str, Any]:
        email = self._normalize_email(email)
        user = self.users.get(email)

        if not user:
            return self._ok(
                "If the email exists, a reset code has been sent.",
                {
                    "reply": "If the email exists, a reset code has been sent.",
                    "meta": "AUTH / PASSWORD RESET PRIVACY",
                    "email": email,
                },
            )

        code = self._create_code(
            email=email,
            purpose="forgot_password",
            extra={},
        )

        email_result = self.email_sender.send_password_reset_email(
            to_email=email,
            code=code,
            name=user.get("name", "there"),
        )

        if not email_result.get("ok"):
            return {
                "ok": False,
                "message": email_result.get("message", "Could not send password reset email."),
                "data": {
                    "reply": email_result.get("message", "Could not send password reset email."),
                    "meta": "AUTH / EMAIL FAILED",
                },
            }

        return self._ok(
            "Password reset code sent to your email.",
            {
                "reply": "Password reset code sent to your email.",
                "meta": "AUTH / PASSWORD RESET CODE SENT",
                "email": email,
            },
        )

    def reset_password_with_code(self, email: str, code: str, new_password: str) -> dict[str, Any]:
        email = self._normalize_email(email)
        code = str(code or "").strip()
        new_password = str(new_password or "")

        if len(new_password) < 6:
            return self._fail("New password must be at least 6 characters.", meta="AUTH / RESET PASSWORD FAILED")

        check = self._verify_code(email=email, code=code, purpose="forgot_password")

        if not check["ok"]:
            return check

        user = self.users.get(email)

        if not user:
            return self._fail("User not found.", meta="AUTH / RESET PASSWORD FAILED")

        user["password_hash"] = self._hash_password(new_password)
        user["updated_at"] = datetime.now().isoformat(timespec="seconds")

        self.users[email] = user
        self._save_users()

        self._delete_code(email=email, purpose="forgot_password")

        return self._ok(
            "Password reset complete.",
            {
                "reply": "Password reset complete.",
                "meta": "AUTH / PASSWORD RESET COMPLETE",
            },
        )

    def _create_code(self, email: str, purpose: str, extra: dict[str, Any]) -> str:
        email = self._normalize_email(email)
        code = f"{secrets.randbelow(1_000_000):06d}"

        key = self._code_key(email, purpose)

        self.codes[key] = {
            "email": email,
            "purpose": purpose,
            "code": code,
            "created_at": time.time(),
            "expires_at": time.time() + CODE_TTL_SECONDS,
            "extra": extra,
        }

        self._save_codes()

        return code

    def _verify_code(self, email: str, code: str, purpose: str) -> dict[str, Any]:
        email = self._normalize_email(email)
        key = self._code_key(email, purpose)

        record = self.codes.get(key)

        if not record:
            return self._fail("Verification code not found.", meta="AUTH / CODE FAILED")

        if time.time() > float(record.get("expires_at", 0)):
            self._delete_code(email=email, purpose=purpose)
            return self._fail("Verification code expired.", meta="AUTH / CODE EXPIRED")

        saved_code = str(record.get("code", ""))

        if not hmac.compare_digest(saved_code, str(code)):
            return self._fail("Invalid verification code.", meta="AUTH / CODE FAILED")

        return self._ok(
            "Verification code accepted.",
            {
                "extra": record.get("extra", {}),
            },
        )

    def _delete_code(self, email: str, purpose: str) -> None:
        key = self._code_key(email, purpose)
        self.codes.pop(key, None)
        self._save_codes()

    def _code_key(self, email: str, purpose: str) -> str:
        return f"{purpose}:{self._normalize_email(email)}"

    def _hash_password(self, password: str) -> str:
        salt = secrets.token_hex(16)
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            120_000,
        ).hex()

        return f"pbkdf2_sha256${salt}${digest}"

    def _verify_password(self, password: str, password_hash: str) -> bool:
        try:
            algorithm, salt, saved_digest = password_hash.split("$", 2)
        except ValueError:
            return False

        if algorithm != "pbkdf2_sha256":
            return False

        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            120_000,
        ).hex()

        return hmac.compare_digest(digest, saved_digest)

    def _public_user(self, user: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": user.get("id", ""),
            "name": user.get("name", ""),
            "email": user.get("email", ""),
            "email_verified": bool(user.get("email_verified", False)),
            "role": user.get("role", "user"),
            "created_at": user.get("created_at", ""),
            "last_login_at": user.get("last_login_at", ""),
        }

    def _save_session(self, email: str) -> None:
        self._write_json(
            SESSION_FILE,
            {
                "email": self._normalize_email(email),
                "signed_in_at": datetime.now().isoformat(timespec="seconds"),
            },
        )

    def _normalize_email(self, email: str) -> str:
        return str(email or "").strip().lower()

    def _valid_email(self, email: str) -> bool:
        return bool(email and "@" in email and "." in email.split("@")[-1])

    def _load_users(self) -> dict[str, Any]:
        data = self._read_json(USERS_FILE, {})

        if isinstance(data, dict) and "users" in data and isinstance(data["users"], dict):
            return data["users"]

        if isinstance(data, dict):
            return data

        return {}

    def _save_users(self) -> None:
        self._write_json(USERS_FILE, self.users)

    def _load_codes(self) -> dict[str, Any]:
        data = self._read_json(CODES_FILE, {})

        if isinstance(data, dict):
            return data

        return {}

    def _save_codes(self) -> None:
        self._write_json(CODES_FILE, self.codes)

    def _read_json(self, path: Path, default: Any) -> Any:
        if not path.exists():
            return default

        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return default

    def _write_json(self, path: Path, data: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _ok(self, message: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        return {
            "ok": True,
            "message": message,
            "data": data or {},
        }

    def _fail(self, message: str, meta: str = "AUTH / FAILED") -> dict[str, Any]:
        return {
            "ok": False,
            "message": message,
            "data": {
                "reply": message,
                "meta": meta,
            },
        }