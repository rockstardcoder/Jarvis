from __future__ import annotations

import json
import smtplib
import ssl
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path
from typing import Any

from jarvis.app.local_secret_store import LocalSecretStore


ROOT_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT_DIR / "data"
SETTINGS_DIR = DATA_DIR / "settings"
DEV_MAILBOX_DIR = DATA_DIR / "dev_mailbox"

EMAIL_SETTINGS_FILE = SETTINGS_DIR / "email_settings.json"


DEFAULT_EMAIL_SETTINGS: dict[str, Any] = {
    "enabled": True,
    "mode": "dev_mailbox",  # dev_mailbox now, smtp later
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_security": "starttls",
    "smtp_username": "",
    "sender_email": "dev@jarvis.local",
    "sender_name": "Jarvis Core",
}


class EmailSender:
    def __init__(self) -> None:
        SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
        DEV_MAILBOX_DIR.mkdir(parents=True, exist_ok=True)

        self.secret_store = LocalSecretStore()
        self.settings = self._load_settings()

    def get_public_settings(self) -> dict[str, Any]:
        return {
            **self.settings,
            "smtp_password_saved": self.secret_store.has_secret("email.smtp_password"),
            "dev_mailbox_dir": str(DEV_MAILBOX_DIR),
        }

    def update_settings(
        self,
        enabled: bool | None = None,
        mode: str | None = None,
        smtp_host: str | None = None,
        smtp_port: int | str | None = None,
        smtp_security: str | None = None,
        smtp_username: str | None = None,
        sender_email: str | None = None,
        sender_name: str | None = None,
    ) -> dict[str, Any]:
        if enabled is not None:
            self.settings["enabled"] = bool(enabled)

        if mode is not None:
            clean_mode = str(mode).strip().lower()
            if clean_mode not in {"dev_mailbox", "smtp"}:
                return self._fail("Email mode must be dev_mailbox or smtp.")
            self.settings["mode"] = clean_mode

        if smtp_host is not None:
            self.settings["smtp_host"] = str(smtp_host).strip()

        if smtp_port is not None:
            try:
                self.settings["smtp_port"] = int(smtp_port)
            except ValueError:
                return self._fail("SMTP port must be a number.")

        if smtp_security is not None:
            security = str(smtp_security).strip().lower()
            if security not in {"starttls", "ssl", "none"}:
                return self._fail("SMTP security must be starttls, ssl, or none.")
            self.settings["smtp_security"] = security

        if smtp_username is not None:
            self.settings["smtp_username"] = str(smtp_username).strip()

        if sender_email is not None:
            self.settings["sender_email"] = str(sender_email).strip()

        if sender_name is not None:
            self.settings["sender_name"] = str(sender_name).strip() or "Jarvis Core"

        self._save_settings()

        return self._ok("Email settings saved.", self.get_public_settings())

    def set_smtp_password(self, password: str) -> dict[str, Any]:
        password = str(password or "").strip()

        if not password:
            return self._fail("SMTP password cannot be empty.")

        self.secret_store.set_secret("email.smtp_password", password)

        return self._ok("SMTP password saved.", self.get_public_settings())

    def clear_smtp_password(self) -> dict[str, Any]:
        self.secret_store.delete_secret("email.smtp_password")

        return self._ok("SMTP password cleared.", self.get_public_settings())

    def send_test_email(self, to_email: str) -> dict[str, Any]:
        to_email = str(to_email or "").strip()

        if not to_email:
            return self._fail("Test email address is required.")

        return self.send_email(
            to_email=to_email,
            subject="Jarvis Core email test",
            text_body=(
                "Your Jarvis Core email system is working.\n\n"
                "This is a test email from your local Jarvis app."
            ),
            html_body=self._basic_email_html(
                title="Jarvis Core email test",
                message="Your Jarvis Core email system is working.",
                footer="This is a test email from your local Jarvis app.",
            ),
            meta="EMAIL / TEST",
        )

    def send_verification_email(
        self,
        to_email: str,
        code: str,
        name: str = "there",
    ) -> dict[str, Any]:
        subject = "Your Jarvis Core verification code"

        text_body = (
            f"Hi {name},\n\n"
            f"Your Jarvis Core verification code is: {code}\n\n"
            "This code expires soon. If you did not request this, you can ignore this email.\n\n"
            "Jarvis Core"
        )

        html_body = self._code_email_html(
            title="Verify your Jarvis Core account",
            greeting=f"Hi {name},",
            message="Use this verification code to finish creating your Jarvis Core account.",
            code=code,
            footer="If you did not request this, you can ignore this email.",
        )

        return self.send_email(
            to_email=to_email,
            subject=subject,
            text_body=text_body,
            html_body=html_body,
            meta="EMAIL / SIGNUP CODE",
        )

    def send_password_reset_email(
        self,
        to_email: str,
        code: str,
        name: str = "there",
    ) -> dict[str, Any]:
        subject = "Reset your Jarvis Core password"

        text_body = (
            f"Hi {name},\n\n"
            f"Your Jarvis Core password reset code is: {code}\n\n"
            "If you did not request this, ignore this email.\n\n"
            "Jarvis Core"
        )

        html_body = self._code_email_html(
            title="Reset your Jarvis Core password",
            greeting=f"Hi {name},",
            message="Use this code to reset your Jarvis Core password.",
            code=code,
            footer="If you did not request this, ignore this email.",
        )

        return self.send_email(
            to_email=to_email,
            subject=subject,
            text_body=text_body,
            html_body=html_body,
            meta="EMAIL / PASSWORD RESET CODE",
        )

    def send_change_email_code(
        self,
        to_email: str,
        code: str,
        name: str = "there",
    ) -> dict[str, Any]:
        subject = "Confirm your new Jarvis Core email"

        text_body = (
            f"Hi {name},\n\n"
            f"Your Jarvis Core email-change code is: {code}\n\n"
            "If you did not request this, ignore this email.\n\n"
            "Jarvis Core"
        )

        html_body = self._code_email_html(
            title="Confirm your new email",
            greeting=f"Hi {name},",
            message="Use this code to confirm your new Jarvis Core email address.",
            code=code,
            footer="If you did not request this, ignore this email.",
        )

        return self.send_email(
            to_email=to_email,
            subject=subject,
            text_body=text_body,
            html_body=html_body,
            meta="EMAIL / CHANGE EMAIL CODE",
        )

    def send_email(
        self,
        to_email: str,
        subject: str,
        text_body: str,
        html_body: str,
        meta: str = "EMAIL / SEND",
    ) -> dict[str, Any]:
        to_email = str(to_email or "").strip()

        if not to_email or "@" not in to_email:
            return self._fail("Valid recipient email is required.")

        mode = self.settings.get("mode", "dev_mailbox")

        if mode == "dev_mailbox":
            return self._send_to_dev_mailbox(
                to_email=to_email,
                subject=subject,
                text_body=text_body,
                html_body=html_body,
                meta=meta,
            )

        validation = self._validate_smtp_ready()

        if not validation["ok"]:
            return validation

        password = self.secret_store.get_secret("email.smtp_password")

        if not password:
            return self._fail("SMTP password is not saved.")

        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = f"{self.settings['sender_name']} <{self.settings['sender_email']}>"
        message["To"] = to_email
        message.set_content(text_body)
        message.add_alternative(html_body, subtype="html")

        host = self.settings["smtp_host"]
        port = int(self.settings["smtp_port"])
        security = self.settings["smtp_security"]
        username = self.settings["smtp_username"]

        try:
            if security == "ssl":
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(host, port, context=context, timeout=25) as server:
                    server.login(username, password)
                    server.send_message(message)
            else:
                with smtplib.SMTP(host, port, timeout=25) as server:
                    server.ehlo()

                    if security == "starttls":
                        context = ssl.create_default_context()
                        server.starttls(context=context)
                        server.ehlo()

                    server.login(username, password)
                    server.send_message(message)

            return self._ok(
                "Email sent.",
                {
                    "reply": "Email sent.",
                    "meta": meta,
                    "to_email": to_email,
                },
            )

        except smtplib.SMTPAuthenticationError:
            return self._fail(
                "SMTP login failed. Use a Google App Password, not your normal Gmail password."
            )
        except Exception as exc:
            return self._fail(f"Email send failed: {exc}")

    def _send_to_dev_mailbox(
        self,
        to_email: str,
        subject: str,
        text_body: str,
        html_body: str,
        meta: str,
    ) -> dict[str, Any]:
        DEV_MAILBOX_DIR.mkdir(parents=True, exist_ok=True)

        latest_html = DEV_MAILBOX_DIR / "latest_email.html"
        latest_txt = DEV_MAILBOX_DIR / "latest_email.txt"
        jsonl_file = DEV_MAILBOX_DIR / "emails.jsonl"

        email_record = {
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "to_email": to_email,
            "subject": subject,
            "text_body": text_body,
            "html_file": str(latest_html),
            "text_file": str(latest_txt),
            "meta": meta,
        }

        latest_html.write_text(html_body, encoding="utf-8")
        latest_txt.write_text(text_body, encoding="utf-8")

        with jsonl_file.open("a", encoding="utf-8") as file:
            file.write(json.dumps(email_record, ensure_ascii=False) + "\n")

        return self._ok(
            "Verification email saved to dev mailbox.",
            {
                "reply": "Verification code sent to your email.",
                "meta": meta,
                "to_email": to_email,
                "dev_mailbox": str(DEV_MAILBOX_DIR),
                "latest_email_html": str(latest_html),
                "latest_email_txt": str(latest_txt),
            },
        )

    def _validate_smtp_ready(self) -> dict[str, Any]:
        if not self.settings.get("enabled"):
            return self._fail("Email sending is disabled in settings.")

        required = [
            "smtp_host",
            "smtp_port",
            "smtp_username",
            "sender_email",
            "sender_name",
        ]

        missing = [key for key in required if not str(self.settings.get(key, "")).strip()]

        if missing:
            return self._fail(f"Missing email settings: {', '.join(missing)}")

        return self._ok("Email sender ready.")

    def _basic_email_html(self, title: str, message: str, footer: str) -> str:
        return f"""
        <div style="margin:0;padding:0;background:#070b12;font-family:Arial,sans-serif;">
          <div style="max-width:620px;margin:0 auto;padding:36px 18px;">
            <div style="background:linear-gradient(145deg,#0b111b,#101a2a);border:1px solid rgba(34,211,238,.18);border-radius:24px;padding:30px;color:#f4f8ff;">
              <div style="display:inline-block;padding:8px 12px;border-radius:999px;background:rgba(34,211,238,.12);color:#22d3ee;font-size:12px;font-weight:700;letter-spacing:.18em;text-transform:uppercase;">
                Jarvis Core
              </div>
              <h1 style="margin:22px 0 10px;font-size:26px;line-height:1.2;color:#f4f8ff;">{title}</h1>
              <p style="margin:0 0 22px;color:#aab7c8;font-size:15px;line-height:1.6;">{message}</p>
              <p style="margin:0;color:#6f7f95;font-size:13px;line-height:1.6;">{footer}</p>
            </div>
          </div>
        </div>
        """

    def _code_email_html(
        self,
        title: str,
        greeting: str,
        message: str,
        code: str,
        footer: str,
    ) -> str:
        safe_code = str(code)

        return f"""
        <div style="margin:0;padding:0;background:#070b12;font-family:Arial,sans-serif;">
          <div style="max-width:620px;margin:0 auto;padding:36px 18px;">
            <div style="background:linear-gradient(145deg,#0b111b,#101a2a);border:1px solid rgba(34,211,238,.18);border-radius:24px;padding:30px;color:#f4f8ff;box-shadow:0 20px 70px rgba(0,0,0,.35);">
              <div style="display:inline-block;padding:8px 12px;border-radius:999px;background:rgba(34,211,238,.12);color:#22d3ee;font-size:12px;font-weight:700;letter-spacing:.18em;text-transform:uppercase;">
                Jarvis Core
              </div>

              <h1 style="margin:22px 0 10px;font-size:26px;line-height:1.2;color:#f4f8ff;">
                {title}
              </h1>

              <p style="margin:0 0 14px;color:#aab7c8;font-size:15px;line-height:1.6;">
                {greeting}
              </p>

              <p style="margin:0 0 22px;color:#aab7c8;font-size:15px;line-height:1.6;">
                {message}
              </p>

              <div style="margin:26px 0;padding:20px;border-radius:18px;background:rgba(34,211,238,.08);border:1px solid rgba(34,211,238,.20);text-align:center;">
                <div style="font-size:13px;color:#6f7f95;text-transform:uppercase;letter-spacing:.18em;margin-bottom:10px;">
                  Verification code
                </div>

                <div style="font-size:36px;font-weight:800;letter-spacing:.22em;color:#22d3ee;text-shadow:0 0 22px rgba(34,211,238,.35);">
                  {safe_code}
                </div>
              </div>

              <p style="margin:0;color:#6f7f95;font-size:13px;line-height:1.6;">
                {footer}
              </p>
            </div>

            <p style="text-align:center;margin:18px 0 0;color:#6f7f95;font-size:12px;">
              Sent by Jarvis Core
            </p>
          </div>
        </div>
        """

    def _load_settings(self) -> dict[str, Any]:
        if not EMAIL_SETTINGS_FILE.exists():
            self._write_json(EMAIL_SETTINGS_FILE, DEFAULT_EMAIL_SETTINGS)
            return json.loads(json.dumps(DEFAULT_EMAIL_SETTINGS))

        try:
            loaded = json.loads(EMAIL_SETTINGS_FILE.read_text(encoding="utf-8"))
        except Exception:
            loaded = {}

        merged = json.loads(json.dumps(DEFAULT_EMAIL_SETTINGS))
        merged.update(loaded)

        if "mode" not in merged:
            merged["mode"] = "dev_mailbox"

        return merged

    def _save_settings(self) -> None:
        self._write_json(EMAIL_SETTINGS_FILE, self.settings)

    def _write_json(self, path: Path, data: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _ok(self, message: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        return {
            "ok": True,
            "message": message,
            "data": data or {},
        }

    def _fail(self, message: str) -> dict[str, Any]:
        return {
            "ok": False,
            "message": message,
            "data": {
                "reply": message,
                "meta": "EMAIL / FAILED",
            },
        }