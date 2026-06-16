from __future__ import annotations

import io
import re
import threading
import traceback
from contextlib import redirect_stdout
from typing import Any

from chat import process_command
from jarvis.core.router import Router
from jarvis.llm.manager import LLMManager
from jarvis.services.voice.stt_service import STTService
from jarvis.services.voice.tts_service import TTSService
from jarvis.tools.tool_manager import ToolManager


class JarvisRuntime:
    """
    Shared Jarvis engine for the desktop UI.

    This wraps your existing terminal command pipeline so the React UI can use:
        chat.send -> JarvisRuntime.send_command(...)
    """

    def __init__(self) -> None:
        self.lock = threading.RLock()

        self.router = Router()
        self.tool_manager = ToolManager()
        self.tts = TTSService()
        self.stt = STTService()

        try:
            self.llm = LLMManager()
            self.llm_ready = True
            self.llm_error = ""
        except Exception as exc:
            self.llm = None
            self.llm_ready = False
            self.llm_error = str(exc)

        self.state: dict[str, Any] = {
            "pending_power_action": None,
            "pending_power_time": 0,
            "pending_delete_training_data": False,
            "pending_diagnostics_consent": False,
            "last_voice_raw": "",
            "last_voice_command": "",
            "ai_debug": False,
        }

    def send_command(self, text: str, model: str = "llama3.1:8b") -> dict[str, Any]:
        text = str(text or "").strip()

        if not text:
            return {
                "ok": False,
                "reply": "Empty command.",
                "meta": "RUNTIME / EMPTY",
                "raw_output": "",
            }

        with self.lock:
            buffer = io.StringIO()

            try:
                with redirect_stdout(buffer):
                    should_exit = process_command(
                        text,
                        self.router,
                        self.tool_manager,
                        self.llm,
                        self.tts,
                        self.stt,
                        self.state,
                    )

                raw_output = buffer.getvalue()
                reply = self._extract_jarvis_reply(raw_output)

                if should_exit:
                    reply = reply or "Exit requested from UI. Desktop app remains open."
                    meta = "JARVIS RUNTIME / EXIT REQUEST"
                else:
                    meta = "JARVIS RUNTIME / CONNECTED"

                return {
                    "ok": True,
                    "reply": reply or "Command completed.",
                    "meta": meta,
                    "raw_output": raw_output,
                    "model": model,
                    "should_exit": bool(should_exit),
                }

            except Exception:
                return {
                    "ok": False,
                    "reply": "Jarvis runtime error.",
                    "meta": "JARVIS RUNTIME / ERROR",
                    "raw_output": buffer.getvalue(),
                    "error": traceback.format_exc(),
                }

    def get_status(self) -> dict[str, Any]:
        return {
            "ok": True,
            "llm_ready": self.llm_ready,
            "llm_error": self.llm_error,
            "voice_output_enabled": True,
            "voice_input_ready": True,
        }

    def shutdown(self) -> None:
        try:
            self.tts.shutdown(wait=False)
        except Exception:
            pass

    def _extract_jarvis_reply(self, raw_output: str) -> str:
        text = raw_output.strip()

        if not text:
            return ""

        matches = re.findall(
            r"Jarvis:\s*(.*?)(?=\n[A-Za-z ]+:|\Z)",
            text,
            flags=re.DOTALL,
        )

        if matches:
            return matches[-1].strip()

        return text.strip()