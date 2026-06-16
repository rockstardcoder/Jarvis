from jarvis.tools.base_tool import BaseTool
from jarvis.services.system_control import SystemControl


class SystemControlTool(BaseTool):

    name = "system_control"

    def execute(
        self,
        action: str,
        value: str | None = None
    ):

        system = SystemControl()

        if action == "volume_up":
            return system.volume_up()

        if action == "volume_down":
            return system.volume_down()

        if action == "mute":
            return system.mute_volume()

        if action == "lock":
            return system.lock_pc()

        if action == "sleep":
            return system.sleep_pc()

        if action == "shutdown":
            return system.shutdown_pc()

        if action == "restart":
            return system.restart_pc()

        if action == "settings":
            page = value or "home"
            return system.open_settings(page)

        return f"Unknown system action: {action}"