from jarvis.tools.base_tool import BaseTool
from jarvis.services.app_discovery import AppDiscovery


class ListAppsTool(BaseTool):

    name = "list_apps"

    def execute(
        self,
        query: str | None = None
    ):

        apps = AppDiscovery().load()

        if not apps:
            apps = AppDiscovery().scan_all()

        app_names = sorted(
            apps.keys()
        )

        if query:
            query = query.lower().strip()

            app_names = [
                name
                for name in app_names
                if query in name.lower()
            ]

        if not app_names:
            return "No matching applications found."

        shown = app_names[:40]

        output = "\n".join(
            shown
        )

        if len(app_names) > 40:
            output += (
                f"\n...and {len(app_names) - 40} more."
            )

        return output