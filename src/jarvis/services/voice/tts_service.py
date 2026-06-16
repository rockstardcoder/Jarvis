import queue
import re
import threading
import time

import pythoncom
import win32com.client

from jarvis.services.voice.voice_config import VoiceConfig


class TTSService:

    def __init__(self):
        self.config = VoiceConfig()
        self.speech_queue = queue.Queue()
        self.stop_event = threading.Event()

        self.worker_thread = threading.Thread(
            target=self.worker_loop,
            daemon=True
        )

        self.worker_thread.start()

    def clean_text(
        self,
        text: str
    ) -> str:
        text = str(text).strip()

        replacements = {
            "✅": "",
            "❌": "",
            "⚠️": "",
            "->": " to ",
            "_": " ",
            "\\": " ",
            "/": " ",
        }

        for old, new in replacements.items():
            text = text.replace(
                old,
                new
            )

        text = re.sub(
            r"\s+",
            " ",
            text
        )

        max_length = 220

        if len(text) > max_length:
            text = text[:max_length] + "."

        return text.strip()

    def find_voice_token(
        self,
        speaker,
        preferred_voice: str
    ):
        preferred_voice = preferred_voice.lower().strip()

        try:
            voices = speaker.GetVoices()
        except BaseException:
            return None

        fallback = None

        for index in range(voices.Count):
            try:
                voice = voices.Item(index)
                description = voice.GetDescription()

                if fallback is None:
                    fallback = voice

                if preferred_voice in description.lower():
                    return voice

            except BaseException:
                continue

        return fallback

    def configure_speaker(
        self,
        speaker
    ):
        voice_token = self.find_voice_token(
            speaker,
            self.config.get_voice_name()
        )

        if voice_token is not None:
            speaker.Voice = voice_token

        speaker.Rate = min(
            10,
            self.config.get_sapi_rate() + 2
        )
        speaker.Volume = self.config.get_sapi_volume()

    def worker_loop(self):
        initialized = False

        try:
            pythoncom.CoInitialize()
            initialized = True

            speaker = win32com.client.Dispatch(
                "SAPI.SpVoice"
            )

            self.configure_speaker(
                speaker
            )

            while not self.stop_event.is_set():
                try:
                    text = self.speech_queue.get(
                        timeout=0.2
                    )

                except queue.Empty:
                    continue

                if text is None:
                    self.speech_queue.task_done()
                    break

                try:
                    self.configure_speaker(
                        speaker
                    )

                    # SVSFlagsAsync = 1
                    # This prevents SAPI from blocking the TTS worker while the UI waits for backend return.
                    speaker.Speak(
                        text,
                        1
                    )

                except BaseException:
                    pass

                finally:
                    try:
                        self.speech_queue.task_done()
                    except BaseException:
                        pass

        except BaseException:
            pass

        finally:
            if initialized:
                try:
                    pythoncom.CoUninitialize()
                except BaseException:
                    pass

    def should_skip_speech(
        self,
        text: str
    ) -> bool:
        text = str(
            text
        ).lower().strip()

        blocked_phrases = [
            "error:",
            "failed",
            "traceback",
            "exception",
            "not found",
            "unavailable",
            "could not understand",
            "timed out",
            "no pdfs found",
            "no active window was found",
            "no speech was detected",
            "microphone error",
            "speech recognition service error"
        ]

        return any(
            phrase in text
            for phrase in blocked_phrases
        )




    def speak(
        self,
        text: str,
        wait: bool = False
    ) -> bool:
        if not self.config.is_enabled():
            return False

        cleaned_text = self.clean_text(
            text
        )

        if not cleaned_text:
            return False
        
        if self.should_skip_speech(
            cleaned_text
        ):
            return False

        # If speech is backed up, drop old queued speech.
        # UI text must never wait behind voice output.
        try:
            while self.speech_queue.qsize() > 0:
                try:
                    self.speech_queue.get_nowait()
                    self.speech_queue.task_done()
                except BaseException:
                    break
        except BaseException:
            pass

        try:
            self.speech_queue.put_nowait(
                cleaned_text
            )

            # For desktop UI responsiveness, never block waiting for TTS.
            # Even if caller passes wait=True, voice should not delay text output.
            return True

        except BaseException:
            return False

    def wait_until_done(
        self,
        timeout: float = 10
    ) -> bool:
        start_time = time.time()

        while time.time() - start_time < timeout:
            if self.speech_queue.unfinished_tasks == 0:
                return True

            time.sleep(
                0.05
            )

        return False

    def shutdown(
        self,
        wait: bool = True
    ):
        try:
            self.stop_event.set()
            self.speech_queue.put(
                None
            )

            if wait:
                self.worker_thread.join(
                    timeout=5
                )

        except BaseException:
            pass