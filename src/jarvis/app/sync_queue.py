from __future__ import annotations

import json
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT_DIR / "data"

SYNC_DIR = DATA_DIR / "sync"
PENDING_DIR = SYNC_DIR / "pending"
UPLOADED_DIR = SYNC_DIR / "uploaded"
FAILED_DIR = SYNC_DIR / "failed"


class SyncQueue:
    def __init__(self) -> None:
        PENDING_DIR.mkdir(parents=True, exist_ok=True)
        UPLOADED_DIR.mkdir(parents=True, exist_ok=True)
        FAILED_DIR.mkdir(parents=True, exist_ok=True)

    def enqueue_record(
        self,
        kind: str,
        user_id: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        upload_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:10]}"
        safe_kind = self._safe_name(kind or "record")
        safe_user = self._safe_name(user_id or "guest_user")

        record = {
            "upload_id": upload_id,
            "kind": safe_kind,
            "user_id": safe_user,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "source": "jarvis_desktop",
            "sync_status": "pending",
            "sync_attempts": 0,
            "payload": payload,
        }

        file_path = PENDING_DIR / f"{safe_kind}_{safe_user}_{upload_id}.json"
        self._write_json(file_path, record)

        return {
            "ok": True,
            "message": "Record queued for upload.",
            "data": {
                "upload_id": upload_id,
                "file_path": str(file_path),
                "record": record,
            },
        }

    def list_pending_files(self) -> list[Path]:
        PENDING_DIR.mkdir(parents=True, exist_ok=True)
        return sorted(PENDING_DIR.glob("*.json"))

    def mark_uploaded(
        self,
        file_path: Path,
        cloud_ref: dict[str, Any],
    ) -> dict[str, Any]:
        file_path = Path(file_path)

        if not file_path.exists():
            return {
                "ok": False,
                "message": f"Pending file not found: {file_path}",
                "data": {},
            }

        record = self._read_json(file_path, {})
        record["sync_status"] = "uploaded"
        record["uploaded_at"] = datetime.now().isoformat(timespec="seconds")
        record["cloud_ref"] = cloud_ref

        uploaded_path = UPLOADED_DIR / file_path.name
        self._write_json(uploaded_path, record)
        file_path.unlink(missing_ok=True)

        return {
            "ok": True,
            "message": "Record marked uploaded.",
            "data": {
                "uploaded_path": str(uploaded_path),
                "cloud_ref": cloud_ref,
            },
        }

    def mark_failed(
        self,
        file_path: Path,
        error: str,
        keep_pending: bool = True,
    ) -> dict[str, Any]:
        file_path = Path(file_path)

        if not file_path.exists():
            return {
                "ok": False,
                "message": f"Pending file not found: {file_path}",
                "data": {},
            }

        record = self._read_json(file_path, {})
        record["sync_status"] = "failed"
        record["last_error"] = str(error)
        record["last_failed_at"] = datetime.now().isoformat(timespec="seconds")
        record["sync_attempts"] = int(record.get("sync_attempts", 0)) + 1

        if keep_pending:
            record["sync_status"] = "pending_retry"
            self._write_json(file_path, record)

            return {
                "ok": False,
                "message": "Upload failed. File kept in pending for retry.",
                "data": {
                    "file_path": str(file_path),
                    "error": str(error),
                },
            }

        failed_path = FAILED_DIR / file_path.name
        self._write_json(failed_path, record)
        file_path.unlink(missing_ok=True)

        return {
            "ok": False,
            "message": "Upload failed. File moved to failed.",
            "data": {
                "failed_path": str(failed_path),
                "error": str(error),
            },
        }

    def get_status(self) -> dict[str, Any]:
        return {
            "pending_count": len(list(PENDING_DIR.glob("*.json"))),
            "uploaded_count": len(list(UPLOADED_DIR.glob("*.json"))),
            "failed_count": len(list(FAILED_DIR.glob("*.json"))),
            "pending_dir": str(PENDING_DIR),
            "uploaded_dir": str(UPLOADED_DIR),
            "failed_dir": str(FAILED_DIR),
        }

    def _safe_name(self, value: str) -> str:
        clean = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in str(value))
        return clean.strip("_") or "unknown"

    def _read_json(self, path: Path, default: Any) -> Any:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return default

    def _write_json(self, path: Path, data: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )