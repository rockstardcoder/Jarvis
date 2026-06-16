from __future__ import annotations

import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

import firebase_admin
from firebase_admin import credentials, firestore

from jarvis.app.sync_queue import SyncQueue


ROOT_DIR = Path(__file__).resolve().parents[3]
SERVICE_ACCOUNT_FILE = ROOT_DIR / "data" / "firebase" / "firebase_service_account.json"


class FirebaseSync:
    def __init__(self) -> None:
        self.initialized = False
        self.error = ""
        self.db = None

        self._initialize()

    def _initialize(self) -> None:
        if not SERVICE_ACCOUNT_FILE.exists():
            self.initialized = False
            self.error = f"Firebase service account missing: {SERVICE_ACCOUNT_FILE}"
            return

        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate(str(SERVICE_ACCOUNT_FILE))
                firebase_admin.initialize_app(cred)

            self.db = firestore.client()
            self.initialized = True
            self.error = ""

        except Exception as exc:
            self.initialized = False
            self.error = f"Firebase initialization failed: {exc}"

    def get_status(self) -> dict[str, Any]:
        return {
            "initialized": self.initialized,
            "error": self.error,
            "service_account_file": str(SERVICE_ACCOUNT_FILE),
        }

    def upload_pending(
        self,
        queue: SyncQueue,
        limit: int = 20,
    ) -> dict[str, Any]:
        if not self.initialized or self.db is None:
            return {
                "ok": False,
                "message": self.error or "Firebase is not initialized.",
                "data": {
                    "uploaded": [],
                    "failed": [],
                    "status": self.get_status(),
                },
            }

        uploaded: list[dict[str, Any]] = []
        failed: list[dict[str, Any]] = []

        pending_files = queue.list_pending_files()[:limit]

        for file_path in pending_files:
            result = self.upload_record_file(file_path)

            if result["ok"]:
                queue.mark_uploaded(
                    file_path=file_path,
                    cloud_ref=result["data"]["cloud_ref"],
                )
                uploaded.append(result["data"])
            else:
                queue.mark_failed(
                    file_path=file_path,
                    error=result["message"],
                    keep_pending=True,
                )
                failed.append(
                    {
                        "file_path": str(file_path),
                        "error": result["message"],
                    }
                )

        return {
            "ok": len(failed) == 0,
            "message": f"Uploaded {len(uploaded)} file(s), failed {len(failed)} file(s).",
            "data": {
                "uploaded": uploaded,
                "failed": failed,
                "queue_status": queue.get_status(),
            },
        }

    def upload_record_file(self, file_path: Path) -> dict[str, Any]:
        file_path = Path(file_path)

        try:
            record = json.loads(file_path.read_text(encoding="utf-8"))

            upload_id = str(record.get("upload_id", file_path.stem))
            kind = str(record.get("kind", "record"))
            user_id = str(record.get("user_id", "guest_user"))

            record["cloud_uploaded_at"] = datetime.now().isoformat(timespec="seconds")

            # Main upload collection: easy to inspect all uploads.
            upload_doc_ref = self.db.collection("development_uploads").document(upload_id)
            upload_doc_ref.set(record)

            # User profile doc.
            user_doc_ref = self.db.collection("users").document(user_id)
            user_doc_ref.set(
                {
                    "user_id": user_id,
                    "last_seen_at": datetime.now().isoformat(timespec="seconds"),
                    "source": "jarvis_desktop",
                },
                merge=True,
            )

            # User-specific subcollection.
            if kind == "chat_event":
                user_sub_doc_ref = (
                    self.db.collection("users")
                    .document(user_id)
                    .collection("chat_events")
                    .document(upload_id)
                )
            else:
                user_sub_doc_ref = (
                    self.db.collection("users")
                    .document(user_id)
                    .collection("development_files")
                    .document(upload_id)
                )

            user_sub_doc_ref.set(record)

            return {
                "ok": True,
                "message": "Uploaded to Firebase.",
                "data": {
                    "upload_id": upload_id,
                    "kind": kind,
                    "user_id": user_id,
                    "cloud_ref": {
                        "development_uploads": f"development_uploads/{upload_id}",
                        "user_doc": f"users/{user_id}",
                        "user_sub_doc": user_sub_doc_ref.path,
                    },
                },
            }

        except Exception as exc:
            return {
                "ok": False,
                "message": f"Firebase upload failed: {exc}",
                "data": {
                    "file_path": str(file_path),
                    "error": traceback.format_exc(),
                },
            }