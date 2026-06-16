from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from jarvis.app.firebase_sync import FirebaseSync
from jarvis.app.sync_queue import SyncQueue


def main() -> None:
    queue = SyncQueue()
    firebase = FirebaseSync()

    print("Firebase status:")
    print(firebase.get_status())
    print()

    queued = queue.enqueue_record(
        kind="chat_event",
        user_id="test_user",
        payload={
            "title": "Firebase test upload",
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "messages": [
                {
                    "role": "user",
                    "text": "test upload",
                    "created_at": datetime.now().isoformat(timespec="seconds"),
                },
                {
                    "role": "assistant",
                    "text": "Firebase upload test successful.",
                    "created_at": datetime.now().isoformat(timespec="seconds"),
                },
            ],
        },
    )

    print("Queued:")
    print(queued["data"]["file_path"])
    print()

    result = firebase.upload_pending(queue, limit=10)

    print("Upload result:")
    print(result)
    print()

    print("Queue status:")
    print(queue.get_status())


if __name__ == "__main__":
    main()
