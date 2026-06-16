import json
from pathlib import Path

import requests


AI_SETTINGS_FILE = Path(
    "data/settings/ai_settings.json"
)


DEFAULT_SETTINGS = {
    "ai_enabled": True,
    "tool_routing_enabled": True,
    "chat_fallback_enabled": True,
    "provider": "ollama",
    "base_url": "http://localhost:11434",
    "model": "llama3.1:8b",
    "temperature": 0,
    "timeout": 90,
    "keep_alive": "30m"
}


class OllamaClient:

    def __init__(
        self
    ):
        self.settings = DEFAULT_SETTINGS.copy()
        self.last_error = ""
        self.last_raw_response = ""
        self.load()

    def load(
        self
    ):
        AI_SETTINGS_FILE.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        if not AI_SETTINGS_FILE.exists():
            self.save()
            return self.settings

        try:
            with open(
                AI_SETTINGS_FILE,
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
        AI_SETTINGS_FILE.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(
            AI_SETTINGS_FILE,
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                self.settings,
                f,
                indent=4
            )

    def is_enabled(
        self
    ) -> bool:
        return bool(
            self.settings.get(
                "ai_enabled",
                True
            )
        )

    def is_tool_routing_enabled(
        self
    ) -> bool:
        return bool(
            self.settings.get(
                "tool_routing_enabled",
                True
            )
        )

    def is_chat_fallback_enabled(
        self
    ) -> bool:
        return bool(
            self.settings.get(
                "chat_fallback_enabled",
                True
            )
        )

    def get_base_url(
        self
    ) -> str:
        return str(
            self.settings.get(
                "base_url",
                DEFAULT_SETTINGS["base_url"]
            )
        ).rstrip("/")

    def get_model(
        self
    ) -> str:
        return str(
            self.settings.get(
                "model",
                DEFAULT_SETTINGS["model"]
            )
        )

    def get_timeout(
        self
    ) -> int:
        return int(
            self.settings.get(
                "timeout",
                DEFAULT_SETTINGS["timeout"]
            )
        )

    def get_temperature(
        self
    ) -> float:
        return float(
            self.settings.get(
                "temperature",
                DEFAULT_SETTINGS["temperature"]
            )
        )

    def get_keep_alive(
        self
    ) -> str:
        return str(
            self.settings.get(
                "keep_alive",
                DEFAULT_SETTINGS["keep_alive"]
            )
        )

    def health_check(
        self
    ) -> tuple[bool, str]:
        try:
            response = requests.get(
                f"{self.get_base_url()}/api/tags",
                timeout=8
            )

            if response.status_code != 200:
                return False, (
                    f"Ollama returned status "
                    f"{response.status_code}."
                )

            return True, "Ollama is available."

        except Exception as e:
            return False, f"Ollama is not available: {e}"

    def list_models(
        self
    ) -> tuple[bool, list[str], str]:
        try:
            response = requests.get(
                f"{self.get_base_url()}/api/tags",
                timeout=8
            )

            if response.status_code != 200:
                return (
                    False,
                    [],
                    f"Ollama returned status {response.status_code}."
                )

            data = response.json()

            models = data.get(
                "models",
                []
            )

            model_names = []

            for model in models:
                name = model.get(
                    "name"
                )

                if name:
                    model_names.append(
                        str(
                            name
                        )
                    )

            return True, model_names, "Models loaded."

        except Exception as e:
            return False, [], f"Could not list Ollama models: {e}"

    def get_status_text(
        self
    ) -> str:
        ok, health_message = self.health_check()
        models_ok, models, models_message = self.list_models()

        lines = [
            "Ollama / AI Status:",
            "- Provider: Ollama",
            f"- Base URL: {self.get_base_url()}",
            f"- Current model: {self.get_model()}",
            f"- AI enabled: {self.is_enabled()}",
            f"- Tool routing enabled: {self.is_tool_routing_enabled()}",
            f"- Chat fallback enabled: {self.is_chat_fallback_enabled()}",
            f"- Keep alive: {self.get_keep_alive()}",
            f"- Health: {health_message}"
        ]

        if models_ok:
            if models:
                lines.append(
                    "- Installed models:"
                )

                for model in models:
                    lines.append(
                        f"  - {model}"
                    )

            else:
                lines.append(
                    "- Installed models: none found"
                )

        else:
            lines.append(
                f"- Installed models: {models_message}"
            )

        if not ok:
            lines.append(
                "- Fix: start Ollama and check OLLAMA_MODELS."
            )

        return "\n".join(
            lines
        )

    def warm_up(
        self
    ) -> str:
        response = self.generate(
            prompt="Reply with only: ready",
            json_mode=False,
            temperature=0,
            max_tokens=5
        )

        if response:
            return f"AI warmed up using {self.get_model()}."

        return (
            "AI warm up failed. "
            f"{self.last_error}"
        )

    def chat(
        self,
        messages: list[dict],
        json_mode: bool = False,
        temperature: float | None = None,
        max_tokens: int | None = None
    ) -> str:
        self.last_error = ""
        self.last_raw_response = ""

        if not self.is_enabled():
            self.last_error = "AI is disabled."
            return ""

        options = {
            "temperature": (
                self.get_temperature()
                if temperature is None
                else temperature
            )
        }

        if max_tokens is not None:
            options["num_predict"] = int(
                max_tokens
            )

        payload = {
            "model": self.get_model(),
            "messages": messages,
            "stream": False,
            "keep_alive": self.get_keep_alive(),
            "options": options
        }

        if json_mode:
            payload["format"] = "json"

        try:
            response = requests.post(
                f"{self.get_base_url()}/api/chat",
                json=payload,
                timeout=self.get_timeout()
            )

            self.last_raw_response = response.text

            if response.status_code != 200:
                self.last_error = (
                    f"Ollama chat status {response.status_code}: "
                    f"{response.text}"
                )
                return ""

            data = response.json()

            message = data.get(
                "message",
                {}
            )

            content = message.get(
                "content",
                ""
            )

            content = str(
                content
            ).strip()

            if not content:
                self.last_error = "Ollama returned empty message content."

            return content

        except Exception as e:
            self.last_error = f"Ollama chat failed: {e}"
            return ""

    def generate(
        self,
        prompt: str,
        json_mode: bool = False,
        temperature: float | None = None,
        max_tokens: int | None = None
    ) -> str:
        self.last_error = ""
        self.last_raw_response = ""

        if not self.is_enabled():
            self.last_error = "AI is disabled."
            return ""

        options = {
            "temperature": (
                self.get_temperature()
                if temperature is None
                else temperature
            )
        }

        if max_tokens is not None:
            options["num_predict"] = int(
                max_tokens
            )

        payload = {
            "model": self.get_model(),
            "prompt": str(
                prompt
            ),
            "stream": False,
            "keep_alive": self.get_keep_alive(),
            "options": options
        }

        if json_mode:
            payload["format"] = "json"

        try:
            response = requests.post(
                f"{self.get_base_url()}/api/generate",
                json=payload,
                timeout=self.get_timeout()
            )

            self.last_raw_response = response.text

            if response.status_code != 200:
                self.last_error = (
                    f"Ollama generate status {response.status_code}: "
                    f"{response.text}"
                )
                return ""

            data = response.json()

            content = data.get(
                "response",
                ""
            )

            content = str(
                content
            ).strip()

            if not content:
                self.last_error = "Ollama returned empty generate response."

            return content

        except Exception as e:
            self.last_error = f"Ollama generate failed: {e}"
            return ""

    def generate_response(
        self,
        user_input: str,
        memory_context: str = "",
        tool_context: str = ""
    ) -> str:
        if not self.is_chat_fallback_enabled():
            return ""

        system_prompt = f"""
You are Jarvis, a local Windows desktop assistant.

Truth and grounding rules:
- Do not claim you checked the internet unless a web/search/browser/web_reader tool result was provided.
- Do not claim live sports, current statistics, current prices, or Wikipedia values unless a web_reader result was provided in recent tool context.
- Do not claim system specs, CPU usage, GPU usage, RAM, temperatures, storage, network, or installed hardware unless system_info tool result or saved user-confirmed memory provides it.
- If saved memory says a PC fact, answer as "Your saved ..." not as live detection.
- Do not claim an action was completed unless a Jarvis tool executed it and the recent tool context says it succeeded.
- If the user says something like "good", "nice", or "thanks", do not pretend the last action succeeded unless recent tool context actually says it succeeded.
- If exact current web information is needed and no web_reader result is available, say Jarvis needs to read/search the page first.
- Keep replies concise and practical.

Saved memory:
{memory_context}

Recent tool context:
{tool_context}
""".strip()

        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": str(
                    user_input
                )
            }
        ]

        response = self.chat(
            messages=messages,
            json_mode=False,
            temperature=0.2,
            max_tokens=160
        )

        if response:
            return response

        return self.generate(
            prompt=(
                f"{system_prompt}\n\n"
                f"User: {user_input}\n"
                "Jarvis:"
            ),
            json_mode=False,
            temperature=0.2,
            max_tokens=160
        )