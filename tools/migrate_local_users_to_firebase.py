from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from firebase_admin import auth

from jarvis.app.firebase.admin_app import initialize_firebase_admin
from jarvis.app.firebase.user_profile_store import upsert_user_profile


load_dotenv()


def load_local_users(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Local users file not found: {path}")

    data = json.loads(path.read_text(encoding="utf-8"))

    if isinstance(data, list):
        return [record for record in data if isinstance(record, dict)]

    if isinstance(data, dict):
        if isinstance(data.get("users"), list):
            return [record for record in data["users"] if isinstance(record, dict)]

        users: list[dict[str, Any]] = []
        for key, value in data.items():
            if isinstance(value, dict):
                record = dict(value)
                record.setdefault("username", key)
                users.append(record)
        return users

    raise ValueError("Unsupported users.json format. Expected list or object.")


def get_email(record: dict[str, Any]) -> str | None:
    email = record.get("email") or record.get("user_email") or record.get("username")
    if not isinstance(email, str):
        return None

    email = email.strip().lower()
    if "@" not in email:
        return None

    return email


def get_plain_password(record: dict[str, Any]) -> str | None:
    for key in ("password", "plain_password", "temp_password"):
        value = record.get(key)
        if isinstance(value, str) and len(value) >= 6:
            return value

    return None


def get_display_name(record: dict[str, Any], email: str) -> str:
    for key in ("display_name", "name", "username"):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    return email.split("@", 1)[0]


def migrate_user(record: dict[str, Any], dry_run: bool = False) -> str:
    email = get_email(record)
    if not email:
        return "SKIP_NO_VALID_EMAIL"

    password = get_plain_password(record)
    if not password:
        return f"SKIP_NO_PLAINTEXT_PASSWORD:{email}"

    display_name = get_display_name(record, email)

    if dry_run:
        return f"DRY_RUN_WOULD_CREATE:{email}"

    try:
        user = auth.create_user(
            email=email,
            password=password,
            display_name=display_name,
            disabled=False,
        )
        status = "CREATED"
    except Exception as exc:
        message = str(exc)
        if "EMAIL_EXISTS" in message or "already exists" in message.lower():
            user = auth.get_user_by_email(email)
            status = "EXISTS"
        else:
            return f"ERROR:{email}:{message}"

    upsert_user_profile(
        uid=user.uid,
        email=email,
        display_name=display_name,
        extra={
            "migration_source": "local_users_json",
            "role": record.get("role", "user"),
            "plan": record.get("plan", "free"),
        },
    )

    return f"{status}:{email}:{user.uid}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate local Jarvis users to Firebase Auth.")
    parser.add_argument(
        "--users-file",
        default="data/auth/users.json",
        help="Path to old local users.json file.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Check what would migrate without creating Firebase users.",
    )

    args = parser.parse_args()

    initialize_firebase_admin()

    users = load_local_users(Path(args.users_file))
    print(f"Loaded {len(users)} local user record(s).")

    for record in users:
        print(migrate_user(record, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
