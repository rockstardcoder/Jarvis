import json
import re
from pathlib import Path


try:
    import speech_recognition as sr
except Exception:
    sr = None


VOICE_INPUT_SETTINGS_FILE = Path(
    "data/settings/voice_input_settings.json"
)

VOICE_CORRECTIONS_FILE = Path(
    "data/settings/voice_command_corrections.json"
)


DEFAULT_SETTINGS = {
    "voice_input_enabled": True,
    "language": "en-IN",
    "timeout": 5,
    "phrase_time_limit": 7,
    "ambient_duration": 0.5,
    "microphone_index": None,
    "wake_words": [
        "wake up jarvis",
        "hey jarvis",
        "jarvis"
    ]
}


DEFAULT_CORRECTIONS = {
    "open ed": "open edge",
    "close ed": "close edge",
    "open xcel": "open excel",
    "close xcel": "close excel",
    "open XL": "open excel",
    "close XL": "close excel",
    "open power point": "open powerpoint",
    "close power point": "close powerpoint",
    "open note pad": "open notepad",
    "close note pad": "close notepad"
}


class STTService:

    def __init__(
        self
    ):
        self.settings = DEFAULT_SETTINGS.copy()
        self.corrections = {}
        self.load()
        self.load_corrections()

    def normalize_text(
        self,
        text: str
    ) -> str:
        text = str(
            text
        ).lower().strip()

        text = re.sub(
            r"[^a-z0-9\s]+",
            " ",
            text
        )

        text = re.sub(
            r"\s+",
            " ",
            text
        ).strip()

        return text

    def load(
        self
    ):
        VOICE_INPUT_SETTINGS_FILE.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        if not VOICE_INPUT_SETTINGS_FILE.exists():
            self.save()
            return self.settings

        try:
            with open(
                VOICE_INPUT_SETTINGS_FILE,
                "r",
                encoding="utf-8"
            ) as f:
                data = json.load(
                    f
                )

            if isinstance(
                data,
                dict
            ):
                self.settings.update(
                    data
                )

        except Exception:
            self.settings = DEFAULT_SETTINGS.copy()
            self.save()

        return self.settings

    def save(
        self
    ):
        VOICE_INPUT_SETTINGS_FILE.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(
            VOICE_INPUT_SETTINGS_FILE,
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                self.settings,
                f,
                indent=4
            )

    def load_corrections(
        self
    ):
        VOICE_CORRECTIONS_FILE.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        if not VOICE_CORRECTIONS_FILE.exists():
            self.save_corrections()
            return self.corrections

        try:
            with open(
                VOICE_CORRECTIONS_FILE,
                "r",
                encoding="utf-8"
            ) as f:
                data = json.load(
                    f
                )

            if isinstance(
                data,
                dict
            ):
                self.corrections = {
                    self.normalize_text(key): str(value).strip()
                    for key, value in data.items()
                    if str(key).strip() and str(value).strip()
                }

        except Exception:
            self.corrections = {}
            self.save_corrections()

        return self.corrections

    def save_corrections(
        self
    ):
        VOICE_CORRECTIONS_FILE.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(
            VOICE_CORRECTIONS_FILE,
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                self.corrections,
                f,
                indent=4
            )

    def get_all_corrections(
        self
    ) -> dict:
        corrections = {
            self.normalize_text(key): value
            for key, value in DEFAULT_CORRECTIONS.items()
        }

        corrections.update(
            self.corrections
        )

        return corrections

    def add_correction(
        self,
        wrong_phrase: str,
        correct_command: str
    ) -> str:
        wrong_phrase = self.normalize_text(
            wrong_phrase
        )

        correct_command = str(
            correct_command
        ).strip()

        if not wrong_phrase:
            return "No wrong phrase was provided."

        if not correct_command:
            return "No correct command was provided."

        self.corrections[wrong_phrase] = correct_command
        self.save_corrections()

        return (
            f"Voice correction saved: "
            f"'{wrong_phrase}' means '{correct_command}'."
        )

    def correct_text(
        self,
        text: str
    ) -> str:
        original = str(
            text
        ).strip()

        normalized = self.normalize_text(
            original
        )

        corrections = self.get_all_corrections()

        if normalized in corrections:
            return corrections[normalized]

        return original

    def list_corrections(
        self
    ) -> str:
        corrections = self.get_all_corrections()

        if not corrections:
            return "No voice corrections are saved."

        lines = [
            "Voice corrections:"
        ]

        for wrong, correct in sorted(
            corrections.items()
        ):
            lines.append(
                f"- {wrong} -> {correct}"
            )

        return "\n".join(
            lines
        )

    def is_available(
        self
    ) -> bool:
        return sr is not None

    def is_enabled(
        self
    ) -> bool:
        return bool(
            self.settings.get(
                "voice_input_enabled",
                True
            )
        )

    def set_enabled(
        self,
        enabled: bool
    ):
        self.settings["voice_input_enabled"] = bool(
            enabled
        )
        self.save()

    def get_language(
        self
    ) -> str:
        return str(
            self.settings.get(
                "language",
                "en-IN"
            )
        )

    def get_timeout(
        self
    ) -> int:
        return int(
            self.settings.get(
                "timeout",
                5
            )
        )

    def get_phrase_time_limit(
        self
    ) -> int:
        return int(
            self.settings.get(
                "phrase_time_limit",
                7
            )
        )

    def get_ambient_duration(
        self
    ) -> float:
        return float(
            self.settings.get(
                "ambient_duration",
                0.5
            )
        )

    def get_microphone_index(
        self
    ):
        value = self.settings.get(
            "microphone_index",
            None
        )

        if value is None:
            return None

        try:
            return int(
                value
            )

        except Exception:
            return None

    def set_microphone_index(
        self,
        index
    ):
        if index is None:
            self.settings["microphone_index"] = None
        else:
            self.settings["microphone_index"] = int(
                index
            )

        self.save()

    def get_wake_words(
        self
    ) -> list[str]:
        wake_words = self.settings.get(
            "wake_words",
            DEFAULT_SETTINGS["wake_words"]
        )

        if not isinstance(
            wake_words,
            list
        ):
            wake_words = DEFAULT_SETTINGS["wake_words"]

        return [
            str(word).lower().strip()
            for word in wake_words
            if str(word).strip()
        ]

    def list_microphones(
        self
    ) -> str:
        if not self.is_available():
            return (
                "SpeechRecognition is not installed. "
                "Run: uv add SpeechRecognition PyAudio"
            )

        try:
            names = sr.Microphone.list_microphone_names()

            if not names:
                return "No microphones were found."

            lines = [
                "Available microphones:"
            ]

            for index, name in enumerate(
                names
            ):
                lines.append(
                    f"{index}: {name}"
                )

            return "\n".join(
                lines
            )

        except Exception as e:
            return f"Failed to list microphones: {e}"

    def extract_wake_command(
        self,
        text: str
    ):
        original_text = str(
            text
        ).strip()

        lower_text = original_text.lower().strip()

        for wake_word in self.get_wake_words():
            if lower_text == wake_word:
                return ""

            prefix = wake_word + " "

            if lower_text.startswith(
                prefix
            ):
                return original_text[
                    len(prefix):
                ].strip()

        return None

    def listen_once(
        self
    ) -> dict:
        if not self.is_available():
            return {
                "success": False,
                "raw_text": "",
                "text": "",
                "message": (
                    "SpeechRecognition is not installed. "
                    "Run: uv add SpeechRecognition PyAudio"
                )
            }

        if not self.is_enabled():
            return {
                "success": False,
                "raw_text": "",
                "text": "",
                "message": "Voice input is disabled."
            }

        recognizer = sr.Recognizer()
        recognizer.dynamic_energy_threshold = True

        microphone_index = self.get_microphone_index()

        try:
            with sr.Microphone(
                device_index=microphone_index
            ) as source:
                recognizer.adjust_for_ambient_noise(
                    source,
                    duration=self.get_ambient_duration()
                )

                audio = recognizer.listen(
                    source,
                    timeout=self.get_timeout(),
                    phrase_time_limit=self.get_phrase_time_limit()
                )

            raw_text = recognizer.recognize_google(
                audio,
                language=self.get_language()
            )

            raw_text = str(
                raw_text
            ).strip()

            if not raw_text:
                return {
                    "success": False,
                    "raw_text": "",
                    "text": "",
                    "message": "No speech was detected."
                }

            corrected_text = self.correct_text(
                raw_text
            )

            if corrected_text != raw_text:
                message = (
                    f"Heard: {raw_text} "
                    f"-> corrected to: {corrected_text}"
                )
            else:
                message = f"Heard: {raw_text}"

            return {
                "success": True,
                "raw_text": raw_text,
                "text": corrected_text,
                "message": message
            }

        except sr.WaitTimeoutError:
            return {
                "success": False,
                "raw_text": "",
                "text": "",
                "message": "Listening timed out. I did not hear anything."
            }

        except sr.UnknownValueError:
            return {
                "success": False,
                "raw_text": "",
                "text": "",
                "message": "I heard audio, but could not understand it."
            }

        except sr.RequestError as e:
            return {
                "success": False,
                "raw_text": "",
                "text": "",
                "message": f"Speech recognition service error: {e}"
            }

        except OSError as e:
            return {
                "success": False,
                "raw_text": "",
                "text": "",
                "message": f"Microphone error: {e}"
            }

        except Exception as e:
            return {
                "success": False,
                "raw_text": "",
                "text": "",
                "message": f"Voice input failed: {e}"
            }