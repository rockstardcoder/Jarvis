import json
import os
import platform
import re
import shutil
import time
import traceback
import zipfile
from datetime import datetime
from pathlib import Path


TRAINING_DATA_DIR = Path(
    "Training_Data"
)

SESSIONS_DIR = TRAINING_DATA_DIR / "sessions"
ERRORS_DIR = TRAINING_DATA_DIR / "errors"
AI_ROUTES_DIR = TRAINING_DATA_DIR / "ai_routes"
TOOL_RESULTS_DIR = TRAINING_DATA_DIR / "tool_results"
MEMORY_CHANGES_DIR = TRAINING_DATA_DIR / "memory_changes"
VOICE_DIR = TRAINING_DATA_DIR / "voice"
EXPORTS_DIR = TRAINING_DATA_DIR / "exports"
PRIVACY_DIR = Path(
    "data/privacy"
)

PRIVACY_POLICY_FILE = PRIVACY_DIR / "diagnostics_privacy_policy.txt"


DEFAULT_PRIVACY_POLICY = """
Jarvis Diagnostics and Training Data Policy

Diagnostics and Training_Data uploads are optional and disabled by default.

If you choose to enable diagnostics upload, Jarvis may send selected logs to the developer for debugging, product improvement, command routing improvement, and assistant quality improvements.

The data may include:
- Chat commands typed into Jarvis
- Jarvis responses
- Tool routes selected by Jarvis
- Tool results
- Error messages and tracebacks
- Voice recognition raw and corrected text
- Timing and performance data
- Local app settings snapshots
- Basic system/environment information

The data should not intentionally include passwords, API keys, private documents, tokens, or confidential files. Jarvis attempts to redact sensitive-looking values before export or upload, but users should still review diagnostics before sharing.

Diagnostics upload can be disabled at any time. Local logs can be exported or deleted by the user.

By enabling diagnostics upload, you confirm that you understand what diagnostic data may contain and that you consent to sending it for development and debugging purposes.

The developer is not responsible for issues caused by user-provided commands, third-party software, operating system behavior, hardware faults, network issues, or misuse of the application. Jarvis is provided as an assistant tool and should be used responsibly.
""".strip()


SENSITIVE_PATTERNS = [
    (
        re.compile(
            r"(?i)(api[_-]?key|secret|token|password|passwd|pwd)\s*[:=]\s*['\"]?[^,'\"\s}]+"
        ),
        r"\1=[REDACTED]"
    ),
    (
        re.compile(
            r"(?i)bearer\s+[a-z0-9._\-]+"
        ),
        "Bearer [REDACTED]"
    ),
    (
        re.compile(
            r"(?i)(sk-[a-z0-9_\-]{12,})"
        ),
        "[REDACTED_API_KEY]"
    ),
    (
        re.compile(
            r"[\w\.-]+@[\w\.-]+\.\w+"
        ),
        "[REDACTED_EMAIL]"
    ),
    (
        re.compile(
            r"\b\d{10,13}\b"
        ),
        "[REDACTED_NUMBER]"
    )
]


class TrainingLogger:

    def __init__(
        self
    ):
        self.session_id = datetime.now().strftime(
            "%Y-%m-%d_%H-%M-%S"
        )

        self.ensure_folders()
        self.ensure_privacy_policy()

        self.session_jsonl = (
            SESSIONS_DIR
            / f"session_{self.session_id}.jsonl"
        )

        self.session_txt = (
            SESSIONS_DIR
            / f"session_{self.session_id}.txt"
        )

    def ensure_folders(
        self
    ):
        for folder in [
            TRAINING_DATA_DIR,
            SESSIONS_DIR,
            ERRORS_DIR,
            AI_ROUTES_DIR,
            TOOL_RESULTS_DIR,
            MEMORY_CHANGES_DIR,
            VOICE_DIR,
            EXPORTS_DIR,
            PRIVACY_DIR
        ]:
            folder.mkdir(
                parents=True,
                exist_ok=True
            )

    def ensure_privacy_policy(
        self
    ):
        PRIVACY_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        if not PRIVACY_POLICY_FILE.exists():
            with open(
                PRIVACY_POLICY_FILE,
                "w",
                encoding="utf-8"
            ) as f:
                f.write(
                    DEFAULT_PRIVACY_POLICY
                )

    def now(
        self
    ) -> str:
        return datetime.now().isoformat(
            timespec="seconds"
        )

    def redact_text(
        self,
        text: str
    ) -> str:
        text = str(
            text
        )

        for pattern, replacement in SENSITIVE_PATTERNS:
            text = pattern.sub(
                replacement,
                text
            )

        return text

    def redact_data(
        self,
        data
    ):
        if isinstance(
            data,
            dict
        ):
            clean = {}

            for key, value in data.items():
                key_text = str(
                    key
                )

                if key_text.lower() in [
                    "api_key",
                    "apikey",
                    "token",
                    "password",
                    "secret",
                    "access_token",
                    "refresh_token"
                ]:
                    clean[key_text] = "[REDACTED]"
                    continue

                clean[key_text] = self.redact_data(
                    value
                )

            return clean

        if isinstance(
            data,
            list
        ):
            return [
                self.redact_data(
                    item
                )
                for item in data
            ]

        if isinstance(
            data,
            str
        ):
            return self.redact_text(
                data
            )

        return data

    def append_jsonl(
        self,
        path: Path,
        payload: dict
    ):
        payload = dict(
            payload
        )

        payload.setdefault(
            "timestamp",
            self.now()
        )

        payload.setdefault(
            "session_id",
            self.session_id
        )

        payload = self.redact_data(
            payload
        )

        with open(
            path,
            "a",
            encoding="utf-8"
        ) as f:
            f.write(
                json.dumps(
                    payload,
                    ensure_ascii=False
                )
                + "\n"
            )

    def append_text(
        self,
        text: str
    ):
        text = self.redact_text(
            text
        )

        with open(
            self.session_txt,
            "a",
            encoding="utf-8"
        ) as f:
            f.write(
                str(
                    text
                )
                + "\n"
            )

    def read_json_file(
        self,
        path: Path
    ):
        try:
            if not path.exists():
                return None

            with open(
                path,
                "r",
                encoding="utf-8"
            ) as f:
                return json.load(
                    f
                )

        except Exception as e:
            return {
                "error": str(
                    e
                )
            }

    def collect_settings_snapshot(
        self
    ) -> dict:
        settings = {}

        settings_root = Path(
            "data/settings"
        )

        if settings_root.exists():
            for path in settings_root.glob(
                "*.json"
            ):
                settings[path.name] = self.read_json_file(
                    path
                )

        return self.redact_data(
            settings
        )

    def collect_memory_snapshot(
        self
    ) -> dict:
        memory = {}

        memory_root = Path(
            "data/memory"
        )

        if memory_root.exists():
            for path in memory_root.glob(
                "*.json"
            ):
                memory[path.name] = self.read_json_file(
                    path
                )

        return self.redact_data(
            memory
        )

    def collect_environment_snapshot(
        self
    ) -> dict:
        snapshot = {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "cwd": str(
                Path.cwd()
            ),
            "pid": os.getpid()
        }

        try:
            import psutil

            memory = psutil.virtual_memory()

            snapshot["ram_total_gb"] = round(
                memory.total / (
                    1024 ** 3
                ),
                2
            )

            snapshot["ram_used_percent"] = memory.percent

            snapshot["cpu_count_logical"] = psutil.cpu_count(
                logical=True
            )

            snapshot["cpu_count_physical"] = psutil.cpu_count(
                logical=False
            )

        except Exception as e:
            snapshot["psutil_error"] = str(
                e
            )

        return self.redact_data(
            snapshot
        )

    def log_startup_snapshot(
        self,
        extra: dict | None = None
    ):
        payload = {
            "event": "startup_snapshot",
            "environment": self.collect_environment_snapshot(),
            "settings": self.collect_settings_snapshot(),
            "memory": self.collect_memory_snapshot(),
            "extra": extra or {}
        }

        self.append_jsonl(
            self.session_jsonl,
            payload
        )

        self.append_text(
            "=== Jarvis Session Started ==="
        )

        self.append_text(
            f"Session ID: {self.session_id}"
        )

        self.append_text(
            f"Started: {self.now()}"
        )

        self.append_text(
            ""
        )

    def log_chat(
        self,
        user_input: str,
        jarvis_response: str,
        source: str = ""
    ):
        payload = {
            "event": "chat",
            "user_input": user_input,
            "jarvis_response": jarvis_response,
            "source": source
        }

        self.append_jsonl(
            self.session_jsonl,
            payload
        )

        self.append_text(
            f"You: {user_input}"
        )

        self.append_text(
            f"Jarvis: {jarvis_response}"
        )

        if source:
            self.append_text(
                f"Source: {source}"
            )

        self.append_text(
            ""
        )

    def log_command_timing(
        self,
        user_input: str,
        start_time: float,
        end_time: float | None = None,
        source: str = "main_loop",
        should_exit: bool | None = None
    ):
        end_time = (
            end_time
            if end_time is not None
            else time.perf_counter()
        )

        duration_ms = round(
            (
                end_time - start_time
            )
            * 1000,
            2
        )

        self.append_jsonl(
            self.session_jsonl,
            {
                "event": "command_timing",
                "user_input": user_input,
                "source": source,
                "duration_ms": duration_ms,
                "should_exit": should_exit
            }
        )

    def log_ai_plan(
        self,
        user_input: str,
        result: dict,
        memory_context: str = ""
    ):
        self.append_jsonl(
            AI_ROUTES_DIR / f"ai_routes_{self.session_id}.jsonl",
            {
                "event": "ai_plan",
                "user_input": user_input,
                "success": result.get(
                    "success"
                ),
                "message": result.get(
                    "message"
                ),
                "routes": result.get(
                    "routes"
                ),
                "raw": result.get(
                    "raw"
                ),
                "memory_context": memory_context
            }
        )

    def log_ai_failure(
        self,
        user_input: str,
        result: dict,
        memory_context: str = ""
    ):
        self.append_jsonl(
            ERRORS_DIR / f"errors_{self.session_id}.jsonl",
            {
                "event": "ai_route_failure",
                "user_input": user_input,
                "message": result.get(
                    "message"
                ),
                "raw": result.get(
                    "raw"
                ),
                "memory_context": memory_context
            }
        )

    def log_tool_result(
        self,
        user_input: str,
        route: dict,
        result: str
    ):
        self.append_jsonl(
            TOOL_RESULTS_DIR / f"tool_results_{self.session_id}.jsonl",
            {
                "event": "tool_result",
                "user_input": user_input,
                "route": route,
                "result": result
            }
        )

    def log_memory_change(
        self,
        user_input: str,
        change_type: str,
        result: str,
        memory_snapshot: dict | None = None
    ):
        self.append_jsonl(
            MEMORY_CHANGES_DIR / f"memory_changes_{self.session_id}.jsonl",
            {
                "event": "memory_change",
                "user_input": user_input,
                "change_type": change_type,
                "result": result,
                "memory_snapshot": memory_snapshot or self.collect_memory_snapshot()
            }
        )

    def log_voice_event(
        self,
        raw_text: str,
        corrected_text: str,
        success: bool = True,
        message: str = "",
        mode: str = ""
    ):
        self.append_jsonl(
            VOICE_DIR / f"voice_{self.session_id}.jsonl",
            {
                "event": "voice",
                "raw_text": raw_text,
                "corrected_text": corrected_text,
                "success": success,
                "message": message,
                "mode": mode
            }
        )

    def log_error(
        self,
        location: str,
        error: Exception,
        extra: dict | None = None
    ):
        self.append_jsonl(
            ERRORS_DIR / f"errors_{self.session_id}.jsonl",
            {
                "event": "exception",
                "location": location,
                "error": str(
                    error
                ),
                "traceback": traceback.format_exc(),
                "extra": extra or {}
            }
        )

    def export_logs(
        self
    ) -> str:
        self.ensure_folders()

        export_path = EXPORTS_DIR / f"training_data_export_{self.session_id}.zip"

        with zipfile.ZipFile(
            export_path,
            "w",
            compression=zipfile.ZIP_DEFLATED
        ) as zip_file:
            for path in TRAINING_DATA_DIR.rglob(
                "*"
            ):
                if path.is_dir():
                    continue

                if EXPORTS_DIR in path.parents:
                    continue

                zip_file.write(
                    path,
                    path.relative_to(
                        TRAINING_DATA_DIR
                    )
                )

            if PRIVACY_POLICY_FILE.exists():
                zip_file.write(
                    PRIVACY_POLICY_FILE,
                    Path(
                        "privacy/diagnostics_privacy_policy.txt"
                    )
                )

        return str(
            export_path
        )

    def delete_logs(
        self
    ) -> str:
        deleted_count = 0

        for folder in [
            SESSIONS_DIR,
            ERRORS_DIR,
            AI_ROUTES_DIR,
            TOOL_RESULTS_DIR,
            MEMORY_CHANGES_DIR,
            VOICE_DIR,
            EXPORTS_DIR
        ]:
            if not folder.exists():
                continue

            for path in folder.iterdir():
                try:
                    if path.is_file():
                        path.unlink()
                        deleted_count += 1

                    elif path.is_dir():
                        shutil.rmtree(
                            path
                        )
                        deleted_count += 1

                except Exception:
                    continue

        return f"Deleted {deleted_count} Training_Data log item(s)."