from jarvis.services.browser_intelligence import BrowserIntelligence
from jarvis.tools.base_tool import BaseTool


class BrowserIntelligenceTool(BaseTool):

    name = "browser_intelligence"

    def execute(
        self,
        action: str,
        target: str | None = None
    ):
        service = BrowserIntelligence()

        if action == "current_title":
            return f"Current title: {service.get_current_title()}"

        if action == "current_url":
            return service.get_current_url()

        if action == "list_browser_windows":
            return service.format_browser_windows()

        if action == "switch_by_title":
            if not target:
                return "No browser title was provided."

            return service.switch_by_title(
                target
            )

        if action == "close_window_by_title":
            if not target:
                return "No browser title was provided."

            return service.close_window_by_title(
                target
            )

        if action == "close_tab_by_title":
            if not target:
                return "No browser tab title was provided."

            return service.close_tab_by_title(
                target
            )

        if action == "switch_tab_by_title":
            if not target:
                return "No browser tab title was provided."

            return service.switch_tab_by_title(
                target
            )

        return f"Unknown browser intelligence action: {action}"