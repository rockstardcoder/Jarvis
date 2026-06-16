from google import genai
from jarvis.llm.base import BaseLLM


class GeminiProvider(BaseLLM):

    def __init__(self, api_key: str):

        self.client = genai.Client(
            api_key=api_key
        )

    def generate(
        self,
        prompt: str
    ) -> str:

        try:

            response = (
                self.client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt
                )
            )

            return response.text

        except Exception as e:

            return (
                "Gemini is currently unavailable. "
                f"Error: {str(e)}"
            )