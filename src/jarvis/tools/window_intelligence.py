from jarvis.services.window_intelligence import WindowIntelligence
from jarvis.tools.base_tool import BaseTool


class WindowIntelligenceTool(BaseTool):

    name = "window_intelligence"

    def execute(
        self,
        action: str,
        target: str | None = None
    ):
        service = WindowIntelligence()

        if action == "list_windows":
            return service.format_window_list()

        if action == "list_file_explorer":
            return service.format_file_explorer_windows()

        if action == "close_by_title":
            if not target:
                return "No window title was provided."

            return service.close_by_title(
                target
            )

        if action == "switch_by_title":
            if not target:
                return "No window title was provided."

            return service.switch_by_title(
                target
            )

        if action == "close_file_explorer":
            return service.close_file_explorer(
                target
            )

        if action == "close_task_manager":
            return service.close_task_manager()

        return f"Unknown window intelligence action: {action}"