from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()


class Settings(BaseModel):
    assistant_name: str = "Jarvis"
    assistant_title: str = "Sir"

    llm_provider: str = "gemini"

    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")

    debug: bool = True


settings = Settings()