import platform
import socket
import subprocess
import time

import psutil


class SystemInfo:

    def run_command(
        self,
        command: list[str],
        timeout: int = 6
    ) -> str:
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            output = result.stdout.strip()

            if output:
                return output

            return result.stderr.strip()

        except Exception:
            return ""

    def get_cpu_name(
        self
    ) -> str:
        output = self.run_command(
            [
                "wmic",
                "cpu",
                "get",
                "name"
            ]
        )

        lines = [
            line.strip()
            for line in output.splitlines()
            if line.strip()
        ]

        if len(
            lines
        ) >= 2:
            return lines[1]

        processor = platform.processor()

        if processor:
            return processor

        return "Unknown CPU"

    def get_ram_total(
        self
    ) -> str:
        memory = psutil.virtual_memory()

        gb = memory.total / (
            1024 ** 3
        )

        return f"{gb:.1f} GB"

    def get_ram_usage(
        self
    ) -> str:
        memory = psutil.virtual_memory()

        used = memory.used / (
            1024 ** 3
        )

        total = memory.total / (
            1024 ** 3
        )

        return (
            f"RAM usage: {memory.percent:.0f}% "
            f"({used:.1f} GB / {total:.1f} GB)"
        )

    def get_cpu_usage(
        self
    ) -> str:
        usage = psutil.cpu_percent(
            interval=1
        )

        return f"CPU usage: {usage:.0f}%"

    def get_gpu_name(
        self
    ) -> str:
        output = self.run_command(
            [
                "nvidia-smi",
                "--query-gpu=name",
                "--format=csv,noheader"
            ]
        )

        if output:
            return output.splitlines()[0].strip()

        output = self.run_command(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name"
            ]
        )

        lines = [
            line.strip()
            for line in output.splitlines()
            if line.strip()
        ]

        if lines:
            return ", ".join(
                lines
            )

        return "Unknown GPU"

    def get_gpu_usage(
        self
    ) -> str:
        output = self.run_command(
            [
                "nvidia-smi",
                "--query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu",
                "--format=csv,noheader,nounits"
            ]
        )

        if not output:
            return (
                "GPU usage is unavailable. "
                "nvidia-smi was not found or did not respond."
            )

        line = output.splitlines()[0]

        parts = [
            part.strip()
            for part in line.split(",")
        ]

        if len(
            parts
        ) < 5:
            return f"GPU data: {line}"

        name, usage, mem_used, mem_total, temp = parts[:5]

        return (
            f"GPU: {name}\n"
            f"GPU usage: {usage}%\n"
            f"VRAM usage: {mem_used} MB / {mem_total} MB\n"
            f"GPU temperature: {temp}°C"
        )

    def get_battery_status(
        self
    ) -> str:
        try:
            battery = psutil.sensors_battery()

            if battery is None:
                return (
                    "Battery status is unavailable. "
                    "This device may be a desktop PC or Windows did not expose battery data."
                )

            plugged = (
                "plugged in"
                if battery.power_plugged
                else "not plugged in"
            )

            if battery.secsleft == psutil.POWER_TIME_UNLIMITED:
                time_left = "unlimited / charging"

            elif battery.secsleft == psutil.POWER_TIME_UNKNOWN:
                time_left = "unknown"

            else:
                hours = battery.secsleft // 3600
                minutes = (
                    battery.secsleft % 3600
                ) // 60

                time_left = f"{hours}h {minutes}m"

            return (
                f"Battery: {battery.percent:.0f}%\n"
                f"Power: {plugged}\n"
                f"Estimated time left: {time_left}"
            )

        except Exception as e:
            return f"Battery status is unavailable: {e}"

    def get_storage_usage(
        self
    ) -> str:
        lines = [
            "Storage usage:"
        ]

        seen_mounts = set()

        for partition in psutil.disk_partitions(
            all=False
        ):
            mountpoint = partition.mountpoint

            if mountpoint in seen_mounts:
                continue

            seen_mounts.add(
                mountpoint
            )

            try:
                usage = psutil.disk_usage(
                    mountpoint
                )

                total = usage.total / (
                    1024 ** 3
                )

                used = usage.used / (
                    1024 ** 3
                )

                free = usage.free / (
                    1024 ** 3
                )

                lines.append(
                    (
                        f"- {mountpoint} "
                        f"{usage.percent:.0f}% used "
                        f"({used:.1f} GB / {total:.1f} GB, "
                        f"{free:.1f} GB free)"
                    )
                )

            except Exception:
                continue

        if len(
            lines
        ) == 1:
            return "Storage usage is unavailable."

        return "\n".join(
            lines
        )

    def get_network_status(
        self
    ) -> str:
        try:
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(
                hostname
            )

        except Exception:
            hostname = "Unknown"
            ip_address = "Unknown"

        stats = psutil.net_if_stats()
        counters_before = psutil.net_io_counters()
        time.sleep(
            1
        )
        counters_after = psutil.net_io_counters()

        upload_speed = (
            counters_after.bytes_sent
            - counters_before.bytes_sent
        )

        download_speed = (
            counters_after.bytes_recv
            - counters_before.bytes_recv
        )

        active_interfaces = []

        for name, data in stats.items():
            if data.isup:
                active_interfaces.append(
                    name
                )

        return (
            "Network status:\n"
            f"- Hostname: {hostname}\n"
            f"- Local IP: {ip_address}\n"
            f"- Active interfaces: {', '.join(active_interfaces) if active_interfaces else 'none detected'}\n"
            f"- Current download speed: {download_speed / 1024:.1f} KB/s\n"
            f"- Current upload speed: {upload_speed / 1024:.1f} KB/s"
        )

    def get_thermal_status(
        self
    ) -> str:
        lines = [
            "Thermal / fan status:"
        ]

        found_any = False

        try:
            if hasattr(
                psutil,
                "sensors_temperatures"
            ):
                temps = psutil.sensors_temperatures()

                for sensor_name, entries in temps.items():
                    for entry in entries[:5]:
                        label = entry.label or sensor_name
                        current = entry.current

                        lines.append(
                            f"- {label}: {current}°C"
                        )

                        found_any = True

        except Exception:
            pass

        try:
            if hasattr(
                psutil,
                "sensors_fans"
            ):
                fans = psutil.sensors_fans()

                for fan_name, entries in fans.items():
                    for entry in entries[:5]:
                        label = entry.label or fan_name
                        current = entry.current

                        lines.append(
                            f"- {label}: {current} RPM"
                        )

                        found_any = True

        except Exception:
            pass

        gpu = self.get_gpu_usage()

        if "GPU temperature" in gpu:
            for line in gpu.splitlines():
                if "GPU temperature" in line:
                    lines.append(
                        f"- {line}"
                    )
                    found_any = True

        if not found_any:
            return (
                "Thermal/fan sensors are not available through Windows/psutil. "
                "GPU temperature may still work if nvidia-smi is available."
            )

        return "\n".join(
            lines
        )

    def get_os_info(
        self
    ) -> str:
        return (
            f"{platform.system()} "
            f"{platform.release()} "
            f"{platform.version()}"
        )

    def get_usage_summary(
        self
    ) -> str:
        cpu = self.get_cpu_usage()
        ram = self.get_ram_usage()
        gpu = self.get_gpu_usage()

        return (
            f"{cpu}\n"
            f"{ram}\n"
            f"{gpu}"
        )

    def get_system_summary(
        self
    ) -> str:
        return (
            "System Information:\n"
            f"- CPU: {self.get_cpu_name()}\n"
            f"- GPU: {self.get_gpu_name()}\n"
            f"- RAM: {self.get_ram_total()}\n"
            f"- OS: {self.get_os_info()}"
        )

    def get_full_status(
        self
    ) -> str:
        return (
            f"{self.get_system_summary()}\n\n"
            f"{self.get_usage_summary()}\n\n"
            f"{self.get_battery_status()}\n\n"
            f"{self.get_storage_usage()}\n\n"
            f"{self.get_network_status()}\n\n"
            f"{self.get_thermal_status()}"
        )