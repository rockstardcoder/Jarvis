import os
import subprocess
from pathlib import Path

from jarvis.services.app_resolver import AppResolver
from jarvis.tools.base_tool import BaseTool
from jarvis.services.app_discovery import AppDiscovery


class OpenAppTool(BaseTool):

    name = "open_app"

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

            if path.is_absolute() and not path.exists():
                return f"Application path for '{resolved_name}' is invalid."

        try:
            if path.is_absolute():
                os.startfile(str(path))
            else:
                subprocess.Popen(
                    app_path,
                    shell=True
                )

            return f"Opening {resolved_name}"

        except Exception:
            try:
                subprocess.Popen(
                    [str(path)],
                    cwd=str(path.parent) if path.is_absolute() else None,
                    shell=False
                )

                return f"Opening {resolved_name}"

            except Exception as e:
                return f"Failed to open {resolved_name}: {e}"