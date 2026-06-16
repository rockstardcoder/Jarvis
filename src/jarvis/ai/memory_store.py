import json
import re
from pathlib import Path
from datetime import datetime


MEMORY_DIR = Path(
    "data/memory"
)

USER_PROFILE_FILE = MEMORY_DIR / "user_profile.json"
SYSTEM_PROFILE_FILE = MEMORY_DIR / "system_profile.json"
PREFERENCES_FILE = MEMORY_DIR / "preferences.json"
COMMAND_CONTEXT_FILE = MEMORY_DIR / "command_context.json"


DEFAULT_USER_PROFILE = {
    "facts": [],
    "name": "",
    "notes": []
}


DEFAULT_SYSTEM_PROFILE = {
    "gpu": "",
    "cpu": "",
    "ram": "",
    "storage": "",
    "os": "",
    "confirmed_by_user": {}
}


DEFAULT_PREFERENCES = {
    "response_style": "concise",
    "truth_mode": True,
    "assistant_name": "Jarvis"
}


DEFAULT_COMMAND_CONTEXT = {
    "last_user_command": "",
    "last_routes": [],
    "last_result": "",
    "pending_followup": None
}


BLOCKED_SYSTEM_MEMORY_WORDS = [
    "usage",
    "status",
    "temperature",
    "thermal",
    "fan",
    "speed",
    "percent",
    "percentage",
    "current",
    "what",
    "which",
    "show",
    "check",
    "tell",
    "?"
]


class MemoryStore:

    def __init__(
        self
    ):
        MEMORY_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        self.user_profile = self.load_json(
            USER_PROFILE_FILE,
            DEFAULT_USER_PROFILE
        )

        self.system_profile = self.load_json(
            SYSTEM_PROFILE_FILE,
            DEFAULT_SYSTEM_PROFILE
        )

        self.preferences = self.load_json(
            PREFERENCES_FILE,
            DEFAULT_PREFERENCES
        )

        self.command_context = self.load_json(
            COMMAND_CONTEXT_FILE,
            DEFAULT_COMMAND_CONTEXT
        )

    def load_json(
        self,
        path: Path,
        default: dict
    ) -> dict:
        if not path.exists():
            self.save_json(
                path,
                default
            )
            return default.copy()

        try:
            with open(
                path,
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
                merged = default.copy()
                merged.update(
                    data
                )
                return merged

        except Exception:
            pass

        self.save_json(
            path,
            default
        )

        return default.copy()

    def save_json(
        self,
        path: Path,
        data: dict
    ):
        path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(
            path,
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                data,
                f,
                indent=4
            )

    def save_all(
        self
    ):
        self.save_json(
            USER_PROFILE_FILE,
            self.user_profile
        )

        self.save_json(
            SYSTEM_PROFILE_FILE,
            self.system_profile
        )

        self.save_json(
            PREFERENCES_FILE,
            self.preferences
        )

        self.save_json(
            COMMAND_CONTEXT_FILE,
            self.command_context
        )

    def is_bad_system_value(
        self,
        value: str
    ) -> bool:
        value = str(
            value
        ).lower().strip()

        if not value:
            return True

        if len(
            value
        ) < 2:
            return True

        return any(
            word in value.split()
            or value == word
            for word in BLOCKED_SYSTEM_MEMORY_WORDS
        )

    def normalize_cpu(
        self,
        value: str
    ) -> str:
        value = value.strip()

        compact = value.lower().replace(
            " ",
            ""
        ).replace(
            "-",
            ""
        )

        replacements = {
            "154600k": "i5-14600K",
            "i514600k": "i5-14600K",
            "i514600": "i5-14600",
            "i514600kf": "i5-14600KF"
        }

        return replacements.get(
            compact,
            value
        )

    def normalize_gpu(
        self,
        value: str
    ) -> str:
        value = value.strip()

        compact = value.lower().replace(
            " ",
            ""
        ).replace(
            "-",
            ""
        )

        if compact in [
            "4060",
            "rtx4060",
            "nvidiartx4060",
            "geforcertx4060",
            "nvidiageforcertx4060"
        ]:
            return "NVIDIA GeForce RTX 4060"

        return value

    def normalize_ram(
        self,
        value: str
    ) -> str:
        value = value.strip()

        match = re.search(
            r"(?P<size>[0-9]+(?:\.[0-9]+)?)\s*(?P<unit>gb|g|tb|t)",
            value,
            re.IGNORECASE
        )

        if not match:
            return value

        size = match.group(
            "size"
        )

        unit = match.group(
            "unit"
        ).upper()

        if unit == "G":
            unit = "GB"

        if unit == "T":
            unit = "TB"

        extra = ""

        if "ddr5" in value.lower():
            extra = " DDR5"

        elif "ddr4" in value.lower():
            extra = " DDR4"

        return f"{size}{unit}{extra}"

    def set_system_fact(
        self,
        key: str,
        value: str,
        source: str = "user"
    ):
        key = key.lower().strip()
        value = str(
            value
        ).strip()

        if self.is_bad_system_value(
            value
        ):
            return

        if key == "cpu":
            value = self.normalize_cpu(
                value
            )

        if key == "gpu":
            value = self.normalize_gpu(
                value
            )

        if key == "ram":
            value = self.normalize_ram(
                value
            )

        self.system_profile[key] = value

        confirmed = self.system_profile.get(
            "confirmed_by_user",
            {}
        )

        confirmed[key] = {
            "value": value,
            "source": source,
            "updated_at": datetime.now().isoformat(
                timespec="seconds"
            )
        }

        self.system_profile["confirmed_by_user"] = confirmed

        self.save_json(
            SYSTEM_PROFILE_FILE,
            self.system_profile
        )

    def forget_system_fact(
        self,
        key: str
    ) -> str:
        key = key.lower().strip()

        if key not in [
            "gpu",
            "cpu",
            "ram",
            "storage",
            "os"
        ]:
            return f"Unknown system memory key: {key}"

        self.system_profile[key] = ""

        confirmed = self.system_profile.get(
            "confirmed_by_user",
            {}
        )

        confirmed.pop(
            key,
            None
        )

        self.system_profile["confirmed_by_user"] = confirmed

        self.save_json(
            SYSTEM_PROFILE_FILE,
            self.system_profile
        )

        return f"Forgot saved {key.upper()} memory."

    def clear_system_memory(
        self
    ) -> str:
        self.system_profile = DEFAULT_SYSTEM_PROFILE.copy()

        self.save_json(
            SYSTEM_PROFILE_FILE,
            self.system_profile
        )

        return "Cleared saved system memory."

    def get_system_fact(
        self,
        key: str
    ) -> str:
        return str(
            self.system_profile.get(
                key,
                ""
            )
        ).strip()

    def get_system_memory_text(
        self
    ) -> str:
        lines = [
            "Saved PC memory:"
        ]

        found = False

        labels = {
            "gpu": "GPU",
            "cpu": "CPU",
            "ram": "RAM",
            "storage": "Storage",
            "os": "OS"
        }

        for key, label in labels.items():
            value = self.get_system_fact(
                key
            )

            if value:
                lines.append(
                    f"- {label}: {value}"
                )
                found = True

        if not found:
            return "No saved PC memory yet."

        return "\n".join(
            lines
        )

    def add_user_fact(
        self,
        fact: str
    ):
        fact = str(
            fact
        ).strip()

        if not fact:
            return

        facts = self.user_profile.get(
            "facts",
            []
        )

        if fact not in facts:
            facts.append(
                fact
            )

        self.user_profile["facts"] = facts

        self.save_json(
            USER_PROFILE_FILE,
            self.user_profile
        )

    def extract_fact_value(
        self,
        text: str,
        names: list[str]
    ) -> str:
        joined_names = "|".join(
            re.escape(
                name
            )
            for name in names
        )

        next_keys = (
            r"(?:gpu|graphics card|cpu|processor|ram|memory|storage|os)"
        )

        pattern = re.compile(
            rf"(?:set\s+)?(?:my\s+)?(?:{joined_names})\s*"
            rf"(?:to|is|=|:)\s*"
            rf"(?P<value>.+?)"
            rf"(?=\s+(?:and\s+)?{next_keys}\s*(?:to|is|=|:)\b|[,.;]|$)",
            re.IGNORECASE
        )

        match = pattern.search(
            text
        )

        if not match:
            return ""

        return match.group(
            "value"
        ).strip()

    def extract_direct_set_value(
        self,
        text: str,
        names: list[str]
    ) -> str:
        joined_names = "|".join(
            re.escape(
                name
            )
            for name in names
        )

        pattern = re.compile(
            rf"set\s+my\s+(?:{joined_names})\s+(?P<value>.+)$",
            re.IGNORECASE
        )

        match = pattern.search(
            text
        )

        if not match:
            return ""

        return match.group(
            "value"
        ).strip()

    def extract_and_store_system_profile(
        self,
        user_input: str
    ) -> str | None:
        text = str(
            user_input
        ).strip()

        lowered = text.lower().strip()

        if not text:
            return None

        blocked_question_starts = [
            "what is",
            "what's",
            "show",
            "check",
            "tell me",
            "do you know"
        ]

        if any(
            lowered.startswith(
                item
            )
            for item in blocked_question_starts
        ):
            if not lowered.startswith(
                "set my"
            ):
                return None

        found = []

        gpu = (
            self.extract_direct_set_value(
                text,
                [
                    "gpu",
                    "graphics card"
                ]
            )
            or self.extract_fact_value(
                text,
                [
                    "gpu",
                    "graphics card"
                ]
            )
        )

        cpu = (
            self.extract_direct_set_value(
                text,
                [
                    "cpu",
                    "processor"
                ]
            )
            or self.extract_fact_value(
                text,
                [
                    "cpu",
                    "processor"
                ]
            )
        )

        ram = (
            self.extract_direct_set_value(
                text,
                [
                    "ram",
                    "memory"
                ]
            )
            or self.extract_fact_value(
                text,
                [
                    "ram",
                    "memory"
                ]
            )
        )

        if gpu and not self.is_bad_system_value(
            gpu
        ):
            self.set_system_fact(
                "gpu",
                gpu,
                "user"
            )

            found.append(
                f"GPU: {self.get_system_fact('gpu')}"
            )

        if cpu and not self.is_bad_system_value(
            cpu
        ):
            self.set_system_fact(
                "cpu",
                cpu,
                "user"
            )

            found.append(
                f"CPU: {self.get_system_fact('cpu')}"
            )

        if ram and not self.is_bad_system_value(
            ram
        ):
            self.set_system_fact(
                "ram",
                ram,
                "user"
            )

            found.append(
                f"RAM: {self.get_system_fact('ram')}"
            )

        if not found:
            return None

        return (
            "Saved to local Jarvis memory:\n"
            + "\n".join(
                f"- {item}"
                for item in found
            )
            + "\nThis is memory/context, not model fine-tuning."
        )

    def remember_from_text(
        self,
        user_input: str
    ) -> str | None:
        text = str(
            user_input
        ).strip()

        lowered = text.lower()

        memory_prefixes = [
            "remember that ",
            "remember ",
            "note that ",
            "from now on ",
            "from now "
        ]

        for prefix in memory_prefixes:
            if lowered.startswith(
                prefix
            ):
                fact = text[
                    len(prefix):
                ].strip()

                if fact:
                    self.add_user_fact(
                        fact
                    )

                    return (
                        "Saved to local Jarvis memory."
                    )

        return None

    def update_command_context(
        self,
        user_command: str,
        routes: list | None = None,
        result: str = "",
        pending_followup=None
    ):
        self.command_context["last_user_command"] = str(
            user_command
        )

        self.command_context["last_routes"] = routes or []

        self.command_context["last_result"] = str(
            result
        )

        self.command_context["pending_followup"] = pending_followup

        self.save_json(
            COMMAND_CONTEXT_FILE,
            self.command_context
        )

    def get_last_routes(
        self
    ) -> list:
        routes = self.command_context.get(
            "last_routes",
            []
        )

        if isinstance(
            routes,
            list
        ):
            return routes

        return []

    def get_context_text(
        self
    ) -> str:
        lines = []

        system_lines = []

        for key in [
            "gpu",
            "cpu",
            "ram",
            "storage",
            "os"
        ]:
            value = self.get_system_fact(
                key
            )

            if value:
                system_lines.append(
                    f"{key.upper()}: {value}"
                )

        if system_lines:
            lines.append(
                "Known user-confirmed system profile:"
            )
            lines.extend(
                f"- {item}"
                for item in system_lines
            )

        facts = self.user_profile.get(
            "facts",
            []
        )

        if facts:
            lines.append(
                "Known user facts/preferences:"
            )
            lines.extend(
                f"- {fact}"
                for fact in facts[-20:]
            )

        if not lines:
            return "No saved memory yet."

        return "\n".join(
            lines
        )