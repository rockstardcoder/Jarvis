from __future__ import annotations

import getpass

from dotenv import load_dotenv
from firebase_admin import auth

from jarvis.app.firebase.admin_app import initialize_firebase_admin
from jarvis.app.firebase.user_profile_store import upsert_user_profile


load_dotenv()


def main() -> None:
    initialize_firebase_admin()

    email = input("Email: ").strip().lower()
    display_name = input("Display name: ").strip()
    password = getpass.getpass("Password: ")

    if not email or "@" not in email:
        raise SystemExit("Invalid email.")

    if len(password) < 6:
        raise SystemExit("Firebase Auth password must be at least 6 characters.")

    user = auth.create_user(
        email=email,
        password=password,
        display_name=display_name or None,
        disabled=False,
    )

    upsert_user_profile(
        uid=user.uid,
        email=email,
        display_name=display_name or email.split("@", 1)[0],
        extra={"created_from": "tools/create_firebase_test_user.py"},
    )

    print(f"Created Firebase user: {email} -> {user.uid}")


if __name__ == "__main__":
    main()
