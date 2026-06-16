from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from firebase_admin import firestore

from jarvis.app.firebase.admin_app import get_firestore_client


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def upsert_user_profile(
    uid: str,
    email: str,
    display_name: str | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    db = get_firestore_client()

    profile: dict[str, Any] = {
        "uid": uid,
        "email": email,
        "display_name": display_name or "",
        "updated_at": utc_now_iso(),
    }

    if extra:
        blocked_keys = {"password", "password_hash", "id_token", "refresh_token", "session"}
        safe_extra = {key: value for key, value in extra.items() if key not in blocked_keys}
        profile.update(safe_extra)

    doc_ref = db.collection("users").document(uid)
    doc_ref.set(
        {
            **profile,
            "created_at": firestore.SERVER_TIMESTAMP,
        },
        merge=True,
    )
