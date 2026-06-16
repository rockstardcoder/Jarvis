from jarvis.config.settings import settings


class Assistant:
    def __init__(self):
        self.name = settings.assistant_name

    def initialize(self):
        print("=" * 40)
        print(f"{self.name} Initializing...")
        print("=" * 40)

        print("Loading Settings...")
        print("Loading Router...")
        print("Loading LLM Provider...")

        print()
        print(f"{self.name} Ready.")