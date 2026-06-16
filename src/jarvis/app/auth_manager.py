from __future__ import annotations

import json
import secrets
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jarvis.app.firebase.auth_client import FirebaseAuthClient, FirebaseAuthError
from jarvis.app.firebase.admin_app import get_firestore_client
from firebase_admin import auth as firebase_admin_auth


ROOT_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT_DIR / "data"
AUTH_DIR = DATA_DIR / "auth"
CODES_FILE = AUTH_DIR / "verification_codes.json"

CODE_TTL_SECONDS = 10 * 60


class AuthManager:
    """
    Firebase-backed auth manager.

    Keeps the same public method names used by WebviewBridge:
    - get_current_user
    - start_signup
    - verify_signup
    - login
    - logout
    - update_name
    - change_password
    - start_forgot_password
    - reset_password_with_code

    Passwords are handled by Firebase Authentication, not local users.json.
    User profile data is stored in Firestore users/{uid}.
    """

    def __init__(self) -> None:
        AUTH_DIR.mkdir(parents=True, exist_ok=True)
        self.auth = FirebaseAuthClient()
        self.codes = self._load_codes()

    def get_current_user(self) -> dict[str, Any]:
        try:
            session = self.auth.get_valid_session()

            if session is None:
                return self._fail(
                    "No user signed in.",
                    meta="AUTH / NOT SIGNED IN",
                    authenticated=False,
                )

            profile = self._get_or_create_profile(
                uid=session.uid,
                email=session.email,
                display_name="",
            )

            return self._ok(
                "Current user loaded.",
                {
                    "authenticated": True,
                    "user": self._public_user(profile),
                },
            )

        except Exception as exc:
            return self._fail(
                f"Could not load current user: {exc}",
                meta="AUTH / CURRENT USER FAILED",
                authenticated=False,
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

        try:
            session = self.auth.sign_up(
                email=email,
                password=password,
                display_name=name,
            )

            self._upsert_profile(
                uid=session.uid,
                email=session.email,
                display_name=name,
                extra={
                    "email_verified": False,
                    "app_verified": False,
                    "auth_provider": "password",
                    "role": "user",
                    "plan": "free",
                    "pending_verification": True,
                    "last_signup_at": self._now_iso(),
                },
            )

            code = self._create_code(
                email=session.email,
                purpose="signup",
                extra={
                    "uid": session.uid,
                    "email": session.email,
                    "name": name,
                },
            )

            return self._ok(
                f"Verification code is: {code}",
                {
                    "reply": f"Verification code is: {code}",
                    "meta": "AUTH / FIREBASE SIGNUP DEV CODE",
                    "authenticated": False,
                    "email": session.email,
                    "dev_code": code,
                    "verification_code": code,
                },
            )

        except FirebaseAuthError as exc:
            return self._fail(
                self._friendly_firebase_error(str(exc)),
                meta="AUTH / FIREBASE SIGNUP FAILED",
            )
        except Exception as exc:
            return self._fail(
                f"Signup failed: {exc}",
                meta="AUTH / SIGNUP ERROR",
            )

    def verify_signup(self, email: str, code: str) -> dict[str, Any]:
        email = self._normalize_email(email)
        code = str(code or "").strip()

        check = self._verify_code(email=email, code=code, purpose="signup")

        if not check["ok"]:
            return check

        extra = check["data"].get("extra", {})
        uid = str(extra.get("uid", "")).strip()
        name = str(extra.get("name", "")).strip()

        session = self.auth.get_valid_session()

        if session is None:
            return self._fail(
                "Session expired. Please log in again.",
                meta="AUTH / VERIFY SESSION EXPIRED",
                authenticated=False,
            )

        if session.email.lower() != email:
            return self._fail(
                "Verification session does not match this email.",
                meta="AUTH / VERIFY EMAIL MISMATCH",
                authenticated=False,
            )

        uid = uid or session.uid

        profile = self._upsert_profile(
            uid=uid,
            email=email,
            display_name=name,
            extra={
                "app_verified": True,
                "email_verified": True,
                "pending_verification": False,
                "verified_at": self._now_iso(),
                "last_login_at": self._now_iso(),
            },
        )

        self._delete_code(email=email, purpose="signup")

        return self._ok(
            "Account verified and signed in.",
            {
                "reply": "Account verified and signed in.",
                "meta": "AUTH / FIREBASE VERIFIED",
                "authenticated": True,
                "user": self._public_user(profile),
            },
        )

    def login(self, email: str, password: str) -> dict[str, Any]:
        email = self._normalize_email(email)
        password = str(password or "")

        if not self._valid_email(email):
            return self._fail("Valid email is required.", meta="AUTH / LOGIN FAILED")

        if not password:
            return self._fail("Password is required.", meta="AUTH / LOGIN FAILED")

        try:
            session = self.auth.sign_in(email=email, password=password)

            profile = self._get_or_create_profile(
                uid=session.uid,
                email=session.email,
                display_name="",
            )

            if not bool(profile.get("app_verified", profile.get("email_verified", False))):
                code = self._create_code(
                    email=session.email,
                    purpose="signup",
                    extra={
                        "uid": session.uid,
                        "email": session.email,
                        "name": profile.get("display_name") or profile.get("name") or "",
                    },
                )

                return self._ok(
                    f"Verification code is: {code}",
                    {
                        "reply": f"Verification code is: {code}",
                        "meta": "AUTH / FIREBASE LOGIN NEEDS VERIFICATION",
                        "authenticated": False,
                        "email": session.email,
                        "dev_code": code,
                        "verification_code": code,
                        "needs_verification": True,
                    },
                )

            profile = self._upsert_profile(
                uid=session.uid,
                email=session.email,
                display_name="",
                extra={
                    "auth_provider": "password",
                    "last_login_at": self._now_iso(),
                },
            )

            return self._ok(
                "Logged in.",
                {
                    "reply": "Logged in.",
                    "meta": "AUTH / FIREBASE LOGIN",
                    "authenticated": True,
                    "user": self._public_user(profile),
                },
            )

        except FirebaseAuthError as exc:
            return self._fail(
                self._friendly_firebase_error(str(exc)),
                meta="AUTH / FIREBASE LOGIN FAILED",
            )
        except Exception as exc:
            return self._fail(
                f"Login failed: {exc}",
                meta="AUTH / LOGIN ERROR",
            )

    def login_google(
        self,
        id_token: str,
        provider: str = "google",
        email: str = "",
        name: str = "",
        photo_url: str = "",
    ) -> dict[str, Any]:
        id_token = str(id_token or "").strip()

        if not id_token:
            return self._fail(
                "Missing Google sign-in token.",
                meta="AUTH / GOOGLE TOKEN MISSING",
                authenticated=False,
            )

        try:
            decoded = firebase_admin_auth.verify_id_token(id_token)

            uid = str(decoded.get("uid", "")).strip()
            token_email = self._normalize_email(decoded.get("email") or email)
            token_name = str(decoded.get("name") or name or "").strip()
            picture = str(decoded.get("picture") or photo_url or "").strip()
            firebase_provider = str(decoded.get("firebase", {}).get("sign_in_provider", provider))

            if not uid:
                return self._fail(
                    "Google sign-in token did not contain a Firebase UID.",
                    meta="AUTH / GOOGLE UID MISSING",
                    authenticated=False,
                )

            if not token_email:
                return self._fail(
                    "Google account did not provide an email address.",
                    meta="AUTH / GOOGLE EMAIL MISSING",
                    authenticated=False,
                )

            profile = self._upsert_profile(
                uid=uid,
                email=token_email,
                display_name=token_name or token_email.split("@", 1)[0],
                extra={
                    "email_verified": bool(decoded.get("email_verified", True)),
                    "app_verified": True,
                    "pending_verification": False,
                    "auth_provider": firebase_provider,
                    "oauth_provider": "google",
                    "photo_url": picture,
                    "last_login_at": self._now_iso(),
                },
            )

            try:
                self.auth.save_external_session(
                    uid=uid,
                    email=token_email,
                    id_token=id_token,
                    refresh_token="",
                    display_name=profile.get("display_name") or profile.get("name") or "",
                    email_verified=bool(decoded.get("email_verified", True)),
                )
            except Exception:
                pass

            return self._ok(
                "Signed in with Google.",
                {
                    "reply": "Signed in with Google.",
                    "meta": "AUTH / GOOGLE LOGIN",
                    "authenticated": True,
                    "user": self._public_user(profile),
                },
            )

        except Exception as exc:
            return self._fail(
                f"Google sign-in failed: {exc}",
                meta="AUTH / GOOGLE LOGIN FAILED",
                authenticated=False,
            )

    def logout(self) -> dict[str, Any]:
        self.auth.logout()

        return self._ok(
            "Logged out.",
            {
                "reply": "Logged out.",
                "meta": "AUTH / LOGOUT",
                "authenticated": False,
            },
        )

    def update_name(self, name: str) -> dict[str, Any]:
        name = str(name or "").strip()

        if not name:
            return self._fail("Name is required.", meta="AUTH / UPDATE NAME FAILED")

        try:
            session = self.auth.get_valid_session()

            if session is None:
                return self._fail("No user signed in.", meta="AUTH / NOT SIGNED IN")

            self.auth.update_profile(session.id_token, display_name=name)

            profile = self._upsert_profile(
                uid=session.uid,
                email=session.email,
                display_name=name,
                extra={
                    "updated_at": self._now_iso(),
                },
            )

            return self._ok(
                "Name updated.",
                {
                    "reply": "Name updated.",
                    "meta": "AUTH / UPDATE NAME",
                    "authenticated": True,
                    "user": self._public_user(profile),
                },
            )

        except Exception as exc:
            return self._fail(
                f"Name update failed: {exc}",
                meta="AUTH / UPDATE NAME FAILED",
            )

    def start_change_email(self, new_email: str, password: str) -> dict[str, Any]:
        return self._fail(
            "Email change is not implemented yet for Firebase Auth.",
            meta="AUTH / CHANGE EMAIL NOT IMPLEMENTED",
        )

    def verify_change_email(self, new_email: str, code: str) -> dict[str, Any]:
        return self._fail(
            "Email change verification is not implemented yet for Firebase Auth.",
            meta="AUTH / CHANGE EMAIL NOT IMPLEMENTED",
        )

    def change_password(self, current_password: str, new_password: str) -> dict[str, Any]:
        """
        Firebase password change from desktop app requires extra account update flow.

        For now, use password reset email. This is safer than keeping local password-change logic.
        """
        current = self.get_current_user()

        if not current.get("ok"):
            return current

        email = current["data"]["user"]["email"]
        return self.start_forgot_password(email)

    def start_forgot_password(self, email: str) -> dict[str, Any]:
        email = self._normalize_email(email)

        if not self._valid_email(email):
            return self._fail("Valid email is required.", meta="AUTH / PASSWORD RESET FAILED")

        try:
            self.auth.send_password_reset_email(email)

            return self._ok(
                "Password reset email sent if the account exists.",
                {
                    "reply": "Password reset email sent if the account exists.",
                    "meta": "AUTH / FIREBASE PASSWORD RESET",
                    "email": email,
                },
            )

        except FirebaseAuthError as exc:
            return self._fail(
                self._friendly_firebase_error(str(exc)),
                meta="AUTH / FIREBASE PASSWORD RESET FAILED",
            )
        except Exception as exc:
            return self._fail(
                f"Password reset failed: {exc}",
                meta="AUTH / PASSWORD RESET ERROR",
            )

    def reset_password_with_code(self, email: str, code: str, new_password: str) -> dict[str, Any]:
        return self._fail(
            "Manual reset code flow is no longer used. Use Firebase password reset email.",
            meta="AUTH / RESET CODE DISABLED",
        )

    def _get_or_create_profile(self, uid: str, email: str, display_name: str = "") -> dict[str, Any]:
        db = get_firestore_client()
        ref = db.collection("users").document(uid)
        snapshot = ref.get()

        if snapshot.exists:
            data = snapshot.to_dict() or {}
            data.setdefault("uid", uid)
            data.setdefault("id", uid)
            data.setdefault("email", email)
            return data

        return self._upsert_profile(uid=uid, email=email, display_name=display_name)

    def _upsert_profile(
        self,
        uid: str,
        email: str,
        display_name: str = "",
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        db = get_firestore_client()
        ref = db.collection("users").document(uid)

        existing = {}
        snapshot = ref.get()
        if snapshot.exists:
            existing = snapshot.to_dict() or {}

        clean_name = display_name or existing.get("display_name") or existing.get("name") or email.split("@", 1)[0]

        profile = {
            "uid": uid,
            "id": uid,
            "email": email,
            "display_name": clean_name,
            "name": clean_name,
            "role": existing.get("role", "user"),
            "plan": existing.get("plan", "free"),
            "source": "jarvis_desktop",
            "updated_at": self._now_iso(),
        }

        if not existing.get("created_at"):
            profile["created_at"] = self._now_iso()

        if extra:
            blocked = {
                "password",
                "password_hash",
                "id_token",
                "refresh_token",
                "session",
            }
            profile.update({k: v for k, v in extra.items() if k not in blocked})

        ref.set(profile, merge=True)

        merged = {**existing, **profile}
        return merged

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

        if saved_code != str(code):
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

    def _load_codes(self) -> dict[str, Any]:
        if not CODES_FILE.exists():
            return {}

        try:
            data = json.loads(CODES_FILE.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _save_codes(self) -> None:
        CODES_FILE.parent.mkdir(parents=True, exist_ok=True)
        CODES_FILE.write_text(
            json.dumps(self.codes, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _public_user(self, user: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": user.get("uid") or user.get("id", ""),
            "uid": user.get("uid") or user.get("id", ""),
            "name": user.get("display_name") or user.get("name", ""),
            "display_name": user.get("display_name") or user.get("name", ""),
            "email": user.get("email", ""),
            "email_verified": bool(user.get("email_verified", False)),
            "role": user.get("role", "user"),
            "plan": user.get("plan", "free"),
            "created_at": user.get("created_at", ""),
            "last_login_at": user.get("last_login_at", ""),
        }

    def _normalize_email(self, email: str) -> str:
        return str(email or "").strip().lower()

    def _valid_email(self, email: str) -> bool:
        return bool(email and "@" in email and "." in email.split("@")[-1])

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    def _friendly_firebase_error(self, message: str) -> str:
        lookup = {
            "EMAIL_EXISTS": "An account with this email already exists.",
            "EMAIL_NOT_FOUND": "Invalid email or password.",
            "INVALID_PASSWORD": "Invalid email or password.",
            "INVALID_LOGIN_CREDENTIALS": "Invalid email or password.",
            "USER_DISABLED": "This account is disabled.",
            "WEAK_PASSWORD": "Password is too weak.",
            "INVALID_EMAIL": "Invalid email address.",
            "MISSING_PASSWORD": "Password is required.",
        }

        upper = message.upper()
        for key, friendly in lookup.items():
            if key in upper:
                return friendly

        return message

    def _ok(self, message: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        return {
            "ok": True,
            "message": message,
            "data": data or {},
        }

    def _fail(
        self,
        message: str,
        meta: str = "AUTH / FAILED",
        authenticated: bool | None = None,
    ) -> dict[str, Any]:
        data: dict[str, Any] = {
            "reply": message,
            "meta": meta,
        }

        if authenticated is not None:
            data["authenticated"] = authenticated

        return {
            "ok": False,
            "message": message,
            "data": data,
        }
