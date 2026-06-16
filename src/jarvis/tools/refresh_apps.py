from jarvis.tools.base_tool import BaseTool
from jarvis.services.app_discovery import AppDiscovery


class RefreshAppsTool(BaseTool):

    name = "refresh_apps"

    def execute(self):

        summary = AppDiscovery().scan_with_summary()

        return (
            "Application scan complete. "
            f"Desktop apps: {summary['total']} "
            f"(Added: {len(summary['added'])}, "
            f"Removed: {len(summary['removed'])}, "
            f"Updated: {len(summary['updated'])})."
        )