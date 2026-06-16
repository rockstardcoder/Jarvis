import json
from pathlib import Path


TOOL_MANIFEST_FILE = Path(
    "data/ai/tool_manifest.json"
)


class ToolManifest:

    def __init__(
        self,
        manifest_path: Path = TOOL_MANIFEST_FILE
    ):
        self.manifest_path = manifest_path
        self.manifest = {}
        self.load()

    def load(
        self
    ) -> dict:
        try:
            if not self.manifest_path.exists():
                self.manifest = {
                    "version": "missing",
                    "tools": {}
                }
                return self.manifest

            with open(
                self.manifest_path,
                "r",
                encoding="utf-8"
            ) as f:
                data = json.load(
                    f
                )

            if not isinstance(
                data,
                dict
            ):
                data = {
                    "version": "invalid",
                    "tools": {}
                }

            if "tools" not in data:
                data["tools"] = {}

            self.manifest = data
            return self.manifest

        except Exception:
            self.manifest = {
                "version": "error",
                "tools": {}
            }

            return self.manifest

    def get_tools(
        self
    ) -> dict:
        tools = self.manifest.get(
            "tools",
            {}
        )

        if isinstance(
            tools,
            dict
        ):
            return tools

        return {}

    def get_tool(
        self,
        tool_name: str
    ):
        return self.get_tools().get(
            tool_name
        )

    def get_prompt_text(
        self
    ) -> str:
        return json.dumps(
            self.manifest,
            indent=2
        )