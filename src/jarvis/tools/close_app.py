from pathlib import Path

from jarvis.tools.base_tool import BaseTool
from jarvis.services.app_discovery import AppDiscovery
from jarvis.services.app_resolver import AppResolver
from jarvis.services.process_manager import ProcessManager


class CloseAppTool(BaseTool):

    name = "close_app"

    def execute(self, app_name: str):

        resolver = AppResolver()
        resolved_name = resolver.resolve(app_name)

        discovery = AppDiscovery()
        apps = discovery.load()

        if resolved_name not in apps:
            discovery.scan_all()
            apps = discovery.load()

        if resolved_name not in apps:
            return f"Application '{resolved_name}' was not found."

        app_path = apps[resolved_name]
        path = Path(app_path)

        if path.is_absolute() and not path.exists():
            discovery.scan_all()
            apps = discovery.load()

            if resolved_name not in apps:
                return f"Application '{resolved_name}' is no longer installed."

            app_path = apps[resolved_name]
            path = Path(app_path)

        process_manager = ProcessManager()
        exe_name = process_manager.get_exe_name(app_path)

        if not exe_name:
            return f"Could not identify process for '{resolved_name}'."

        success = process_manager.close_by_exe(exe_name)

        if success:
            return f"Closing {resolved_name}"

        return f"Application '{resolved_name}' is not running."