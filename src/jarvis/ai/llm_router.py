import json
import re

from jarvis.ai.ollama_client import OllamaClient
from jarvis.ai.safety_validator import SafetyValidator
from jarvis.ai.tool_manifest import ToolManifest


class LLMRouter:

    def __init__(
        self
    ):
        self.client = OllamaClient()
        self.manifest = ToolManifest()
        self.validator = SafetyValidator(
            self.manifest
        )
        self.last_model_response = ""

    def extract_json(
        self,
        text: str
    ):
        text = str(
            text
        ).strip()

        self.last_model_response = text

        if not text:
            return None

        text = text.replace(
            "```json",
            ""
        ).replace(
            "```",
            ""
        ).strip()

        try:
            return json.loads(
                text
            )

        except Exception:
            pass

        match = re.search(
            r"(\[[\s\S]*\]|\{[\s\S]*\})",
            text
        )

        if not match:
            return None

        try:
            return json.loads(
                match.group(1)
            )

        except Exception:
            return None

    def build_tool_router_prompt(
        self,
        user_input: str,
        memory_context: str = ""
    ) -> str:
        manifest_text = self.manifest.get_prompt_text()

        return f"""
You are the Jarvis AI tool planner.

Return either:
1. One JSON object for one action.
2. One JSON array of objects for multi-step actions.
3. {{"tool": null, "reason": "chat"}} for normal chat.

STRICT RULES:
- Return JSON only.
- No markdown.
- No explanation.
- Use only tools/actions from the manifest.
- Do not invent tool names.
- Do not claim actions. Only produce tool routes.
- For live system data, use system_info.
- For webpage reading, Wikipedia extraction, links, tables, or search results, use web_reader.
- For current browser title/URL or title-based browser control, use browser_intelligence.
- For File Explorer windows, visible windows, or title-based window control, use window_intelligence.
- For YouTube searches, use web_control with engine "youtube".
- For "search X on youtube", target should be X and engine should be youtube.
- For "open YouTube", use web_control open_shortcut target youtube.
- If the command has "then" or multiple clear actions, return a JSON array in execution order.

Saved memory:
{memory_context}

Allowed tools manifest:
{manifest_text}

Examples:

User: search mr beast on youtube
JSON:
{{"tool":"web_control","action":"search","engine":"youtube","target":"mr beast"}}

User: open youtube
JSON:
{{"tool":"web_control","action":"open_shortcut","target":"youtube"}}

User: current url
JSON:
{{"tool":"browser_intelligence","action":"current_url"}}

User: read current tab title
JSON:
{{"tool":"browser_intelligence","action":"current_title"}}

User: close tab titled python
JSON:
{{"tool":"browser_intelligence","action":"close_tab_by_title","target":"python"}}

User: switch to tab titled youtube
JSON:
{{"tool":"browser_intelligence","action":"switch_tab_by_title","target":"youtube"}}

User: close file explorer
JSON:
{{"tool":"window_intelligence","action":"close_file_explorer"}}

User: close task manager
JSON:
{{"tool":"window_intelligence","action":"close_task_manager"}}

User: list windows
JSON:
{{"tool":"window_intelligence","action":"list_windows"}}

User: battery status
JSON:
{{"tool":"system_info","action":"battery"}}

User: storage usage
JSON:
{{"tool":"system_info","action":"storage"}}

User: network speed
JSON:
{{"tool":"system_info","action":"network"}}

User: thermal status
JSON:
{{"tool":"system_info","action":"thermal"}}

User: summarize webpage example.com
JSON:
{{"tool":"web_reader","action":"summarize_url","target":"example.com"}}

User: extract links from example.com
JSON:
{{"tool":"web_reader","action":"extract_links","target":"example.com"}}

User: wikipedia virat kohli
JSON:
{{"tool":"web_reader","action":"wikipedia","target":"virat kohli"}}

User: close notepad then open comet and search what is python on google in comet
JSON:
[
  {{"tool":"close_app","app_name":"notepad"}},
  {{"tool":"open_app","app_name":"comet"}},
  {{"tool":"web_control","action":"search","engine":"google","target":"what is python","browser":"comet"}}
]

User: what is ollama
JSON:
{{"tool":null,"reason":"chat"}}

Now convert this user command:
{user_input}

JSON:
""".strip()

    def validate_one_route(
        self,
        route
    ) -> tuple[bool, dict | None, str]:
        if not isinstance(
            route,
            dict
        ):
            return False, None, "Route is not a dictionary."

        if route.get(
            "tool"
        ) in [
            None,
            "",
            "none",
            "null"
        ]:
            return False, None, route.get(
                "reason",
                "chat"
            )

        return self.validator.validate(
            route
        )

    def plan(
        self,
        user_input: str,
        memory_context: str = ""
    ) -> dict:
        if not self.client.is_enabled():
            return {
                "success": False,
                "routes": [],
                "message": "AI is disabled."
            }

        if not self.client.is_tool_routing_enabled():
            return {
                "success": False,
                "routes": [],
                "message": "AI tool routing is disabled."
            }

        prompt = self.build_tool_router_prompt(
            user_input,
            memory_context
        )

        response_text = self.client.generate(
            prompt=prompt,
            json_mode=False,
            temperature=0,
            max_tokens=320
        )

        data = self.extract_json(
            response_text
        )

        if data is None:
            return {
                "success": False,
                "routes": [],
                "message": (
                    "AI did not return valid JSON. "
                    f"Raw response: {response_text or self.client.last_error}"
                ),
                "raw": response_text
            }

        if isinstance(
            data,
            dict
        ):
            valid, route, message = self.validate_one_route(
                data
            )

            return {
                "success": valid,
                "routes": [route] if route else [],
                "message": message,
                "raw": data
            }

        if isinstance(
            data,
            list
        ):
            validated_routes = []

            for item in data:
                valid, route, message = self.validate_one_route(
                    item
                )

                if not valid:
                    return {
                        "success": False,
                        "routes": [],
                        "message": message,
                        "raw": data
                    }

                if route:
                    validated_routes.append(
                        route
                    )

            if not validated_routes:
                return {
                    "success": False,
                    "routes": [],
                    "message": "AI produced an empty plan.",
                    "raw": data
                }

            return {
                "success": True,
                "routes": validated_routes,
                "message": "AI plan validated.",
                "raw": data
            }

        return {
            "success": False,
            "routes": [],
            "message": "AI returned unsupported JSON.",
            "raw": data
        }

    def route(
        self,
        user_input: str
    ) -> dict:
        result = self.plan(
            user_input
        )

        route = None

        if result.get(
            "routes"
        ):
            route = result["routes"][0]

        return {
            "success": result.get(
                "success",
                False
            ),
            "route": route,
            "message": result.get(
                "message",
                ""
            ),
            "raw": result.get(
                "raw"
            )
        }

    def generate_response(
        self,
        user_input: str,
        memory_context: str = "",
        tool_context: str = ""
    ) -> str:
        return self.client.generate_response(
            user_input,
            memory_context=memory_context,
            tool_context=tool_context
        )

    def health_check(
        self
    ) -> str:
        ok, message = self.client.health_check()

        if ok:
            return message

        return message

    def startup_check(
        self
    ) -> str:
        ok, message = self.client.health_check()

        if not ok:
            return (
                "AI offline. Exact commands are still available. "
                f"{message}"
            )

        ok_models, models, _ = self.client.list_models()

        if not ok_models:
            return (
                "AI available, but installed models could not be listed."
            )

        if self.client.get_model() not in models:
            return (
                f"AI available, but model {self.client.get_model()} "
                "was not found. Run: ollama pull "
                f"{self.client.get_model()}"
            )

        return (
            f"AI Brain ready using {self.client.get_model()}."
        )