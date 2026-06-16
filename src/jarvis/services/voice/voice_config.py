import json
from pathlib import Path


VOICE_SETTINGS_FILE = Path(
    "data/settings/voice_settings.json"
)


DEFAULT_SETTINGS = {
    "voice_enabled": True,
    "voice_name": "Microsoft David",
    "sapi_rate": 0,
    "sapi_volume": 100
}


AVAILABLE_VOICES = {
    "Microsoft David": "Microsoft David",
    "Microsoft Zira": "Microsoft Zira",
    "Microsoft Mark": "Microsoft Mark"
}


class VoiceConfig:

    def __init__(self):
        self.settings = DEFAULT_SETTINGS.copy()
        self.load()

    def load(self):
        VOICE_SETTINGS_FILE.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        if not VOICE_SETTINGS_FILE.exists():
            self.save()
            return self.settings

        try:
            with open(
                VOICE_SETTINGS_FILE,
                "r",
                encoding="utf-8"
            ) as f:
                data = json.load(f)

            if isinstance(data, dict):
                self.settings.update(data)

            current_voice = str(
                self.settings.get(
                    "voice_name",
                    ""
                )
            )

            if (
                current_voice.startswith("en-")
                or "Neural" in current_voice
            ):
                self.settings["voice_name"] = DEFAULT_SETTINGS["voice_name"]
                self.save()

        except Exception:
            self.settings = DEFAULT_SETTINGS.copy()
            self.save()

        return self.settings

    def save(self):
        VOICE_SETTINGS_FILE.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(
            VOICE_SETTINGS_FILE,
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                self.settings,
                f,
                indent=4
            )

    def is_enabled(self) -> bool:
        return bool(
            self.settings.get(
                "voice_enabled",
                True
            )
        )

    def set_enabled(self, enabled: bool):
        self.settings["voice_enabled"] = enabled
        self.save()

    def get_voice_name(self) -> str:
        return str(
            self.settings.get(
                "voice_name",
                DEFAULT_SETTINGS["voice_name"]
            )
        )

    def set_voice_name(self, voice_name: str):
        self.settings["voice_name"] = voice_name
        self.save()

    def get_sapi_rate(self) -> int:
        return int(
            self.settings.get(
                "sapi_rate",
                DEFAULT_SETTINGS["sapi_rate"]
            )
        )

    def set_sapi_rate(self, rate: int):
        rate = max(
            -10,
            min(
                10,
                int(rate)
            )
        )

        self.settings["sapi_rate"] = rate
        self.save()

    def get_sapi_volume(self) -> int:
        return int(
            self.settings.get(
                "sapi_volume",
                DEFAULT_SETTINGS["sapi_volume"]
            )
        )

    def set_sapi_volume(self, volume: int):
        volume = max(
            0,
            min(
                100,
                int(volume)
            )
        )

        self.settings["sapi_volume"] = volume
        self.save()

    def get_available_voices(self) -> dict:
        return AVAILABLE_VOICES.copy()