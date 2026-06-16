from jarvis.tools.base_tool import BaseTool
from jarvis.services.package_manager import PackageManager


class PackageTool(BaseTool):

    name = "package_manager"

    def execute(
        self,
        action: str,
        value: str | None = None
    ):

        manager = PackageManager()

        if action == "search":
            if not value:
                return "Tell me what app to search for."

            return manager.search(value)

        if action == "list_installed":
            return manager.list_installed(value)

        if action == "install":
            if not value:
                return "Use: install package <package_id>"

            return manager.install_by_id(value)

        if action == "uninstall":
            if not value:
                return "Use: uninstall package <package_id>"

            return manager.uninstall_by_id(value)

        if action == "settings":
            return manager.open_installed_apps_settings()

        return f"Unknown package action: {action}"