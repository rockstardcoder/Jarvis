from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import firebase_admin
from firebase_admin import credentials, firestore


class FirebaseAdminConfigError(RuntimeError):
    """Raised when Firebase Admin SDK cannot be initialized."""


def initialize_firebase_admin() -> firebase_admin.App:
    """Initialize Firebase Admin SDK once.

    Looks for either:
    - FIREBASE_SERVICE_ACCOUNT_PATH
    - FIREBASE_SERVICE_ACCOUNT_JSON

    Never commit the service account JSON file.
    """
    try:
        return firebase_admin.get_app()
    except ValueError:
        pass

    service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "").strip()
    service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "").strip()

    if service_account_json:
        try:
            cert_data: dict[str, Any] = json.loads(service_account_json)
        except json.JSONDecodeError as exc:
            raise FirebaseAdminConfigError("FIREBASE_SERVICE_ACCOUNT_JSON is not valid JSON.") from exc

        cred = credentials.Certificate(cert_data)
        return firebase_admin.initialize_app(cred)

    if service_account_path:
        path = Path(service_account_path)
        if not path.exists():
            raise FirebaseAdminConfigError(f"Service account file not found: {path}")

        cred = credentials.Certificate(str(path))
        return firebase_admin.initialize_app(cred)

    raise FirebaseAdminConfigError(
        "Missing Firebase Admin credentials. Set FIREBASE_SERVICE_ACCOUNT_PATH in .env."
    )


def get_firestore_client():
    initialize_firebase_admin()
    return firestore.client()
