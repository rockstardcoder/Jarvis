from jarvis.tools.base_tool import BaseTool
from jarvis.services.web_control import WebControl


class WebControlTool(BaseTool):

    name = "web_control"

    def execute(
        self,
        action: str,
        target: str,
        browser: str | None = None,
        engine: str | None = None
    ):

        web = WebControl()

        if action == "open_url":
            return web.open_url(
                url=target,
                browser=browser
            )

        if action == "open_shortcut":
            return web.open_shortcut(
                name=target,
                browser=browser
            )

        if action == "search":
            if not engine:
                engine = "google"

            return web.search(
                engine=engine,
                query=target,
                browser=browser
            )

        return f"Unknown web action: {action}"