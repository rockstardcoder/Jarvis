from jarvis.config.settings import settings
from jarvis.llm.gemini_provider import GeminiProvider


class LLMManager:
    def __init__(self):
        provider = settings.llm_provider.lower()

        if provider == "gemini":
            self.provider = GeminiProvider(
                settings.gemini_api_key
            )
        else:
            raise ValueError(
                f"Unknown provider: {provider}"
            )

    def generate(self, prompt: str) -> str:
        return self.provider.generate(prompt)