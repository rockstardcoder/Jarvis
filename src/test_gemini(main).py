from jarvis.config.settings import settings
from jarvis.llm.gemini_provider import GeminiProvider


llm = GeminiProvider(settings.gemini_api_key)

response = llm.generate(
    "You are Jarvis. Reply in one sentence. Introduce yourself."
)

print(response)