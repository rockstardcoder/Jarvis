import json
from pathlib import Path


ALIASES_FILE = Path(
    "data/app_aliases.json"
)


class AppResolver:

    def __init__(self):

        self.aliases = {}

        if ALIASES_FILE.exists():

            with open(
                ALIASES_FILE,
                "r",
                encoding="utf-8"
            ) as f:

                self.aliases = json.load(f)

    def resolve(
        self,
        app_name: str
    ):

        app_name = (
            app_name
            .lower()
            .strip()
        )

        return self.aliases.get(
            app_name,
            app_name
        )