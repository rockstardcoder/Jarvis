from jarvis.tools.base_tool import BaseTool
from jarvis.services.browser_control import BrowserControl


class BrowserControlTool(BaseTool):

    name = "browser_control"

    def execute(
        self,
        action: str,
        value: str | None = None,
        browser: str | None = None
    ):

        browser_control = BrowserControl()

        return browser_control.execute(
            action=action,
            value=value,
            browser=browser
        )