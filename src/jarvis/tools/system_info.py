from jarvis.services.system_info import SystemInfo
from jarvis.tools.base_tool import BaseTool


class SystemInfoTool(BaseTool):

    name = "system_info"

    def execute(
        self,
        action: str = "summary"
    ):
        system_info = SystemInfo()

        if action == "summary":
            return system_info.get_system_summary()

        if action == "full_status":
            return system_info.get_full_status()

        if action == "usage":
            return system_info.get_usage_summary()

        if action == "cpu":
            return f"CPU: {system_info.get_cpu_name()}"

        if action == "gpu":
            return f"GPU: {system_info.get_gpu_name()}"

        if action == "ram":
            return f"RAM: {system_info.get_ram_total()}"

        if action == "cpu_usage":
            return system_info.get_cpu_usage()

        if action == "gpu_usage":
            return system_info.get_gpu_usage()

        if action == "ram_usage":
            return system_info.get_ram_usage()

        if action == "battery":
            return system_info.get_battery_status()

        if action == "storage":
            return system_info.get_storage_usage()

        if action == "network":
            return system_info.get_network_status()

        if action == "thermal":
            return system_info.get_thermal_status()

        if action == "os":
            return f"OS: {system_info.get_os_info()}"

        return f"Unknown system info action: {action}"