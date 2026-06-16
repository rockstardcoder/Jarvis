import ctypes
import subprocess
import time

import win32api
import win32con


class SystemControl:

    def press_key(
        self,
        key_code: int,
        times: int = 1
    ):
        for _ in range(times):
            win32api.keybd_event(
                key_code,
                0,
                0,
                0
            )

            time.sleep(
                0.05
            )

            win32api.keybd_event(
                key_code,
                0,
                win32con.KEYEVENTF_KEYUP,
                0
            )

            time.sleep(
                0.05
            )

    def volume_up(
        self,
        steps: int = 2
    ) -> str:
        self.press_key(
            win32con.VK_VOLUME_UP,
            steps
        )

        return "Volume increased."

    def volume_down(
        self,
        steps: int = 2
    ) -> str:
        self.press_key(
            win32con.VK_VOLUME_DOWN,
            steps
        )

        return "Volume decreased."

    def mute_volume(self) -> str:
        self.press_key(
            win32con.VK_VOLUME_MUTE,
            1
        )

        return "Volume muted or unmuted."

    def lock_pc(self) -> str:
        try:
            ctypes.windll.user32.LockWorkStation()
            return "Locking PC."

        except Exception as e:
            return f"Failed to lock PC: {e}"

    def sleep_pc(self) -> str:
        try:
            command = (
                "Add-Type -AssemblyName System.Windows.Forms; "
                "[System.Windows.Forms.Application]::SetSuspendState("
                "'Suspend', $false, $false)"
            )

            subprocess.Popen(
                [
                    "powershell.exe",
                    "-NoProfile",
                    "-WindowStyle",
                    "Hidden",
                    "-Command",
                    command
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            return "Putting PC to sleep."

        except Exception as e:
            return f"Failed to put PC to sleep: {e}"

    def shutdown_pc(self) -> str:
        try:
            subprocess.Popen(
                [
                    "shutdown.exe",
                    "/s",
                    "/t",
                    "0"
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            return "Shutting down PC."

        except Exception as e:
            return f"Failed to shut down PC: {e}"

    def restart_pc(self) -> str:
        try:
            subprocess.Popen(
                [
                    "shutdown.exe",
                    "/r",
                    "/t",
                    "0"
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            return "Restarting PC."

        except Exception as e:
            return f"Failed to restart PC: {e}"

    def open_settings_uri(
        self,
        uri: str,
        label: str
    ) -> str:
        try:
            subprocess.Popen(
                [
                    "explorer.exe",
                    uri
                ]
            )

            return f"Opening {label}."

        except Exception as e:
            return f"Failed to open {label}: {e}"

    def open_settings(
        self,
        page: str = "home"
    ) -> str:
        page = page.lower().strip()

        settings_pages = {
            "home": {
                "uri": "ms-settings:",
                "label": "Windows settings"
            },
            "settings": {
                "uri": "ms-settings:",
                "label": "Windows settings"
            },
            "display": {
                "uri": "ms-settings:display",
                "label": "display settings"
            },
            "sound": {
                "uri": "ms-settings:sound",
                "label": "sound settings"
            },
            "audio": {
                "uri": "ms-settings:sound",
                "label": "sound settings"
            },
            "bluetooth": {
                "uri": "ms-settings:bluetooth",
                "label": "Bluetooth settings"
            },
            "network": {
                "uri": "ms-settings:network",
                "label": "network settings"
            },
            "wifi": {
                "uri": "ms-settings:network-wifi",
                "label": "Wi-Fi settings"
            },
            "wi-fi": {
                "uri": "ms-settings:network-wifi",
                "label": "Wi-Fi settings"
            },
            "ethernet": {
                "uri": "ms-settings:network-ethernet",
                "label": "Ethernet settings"
            },
            "power": {
                "uri": "ms-settings:powersleep",
                "label": "power settings"
            },
            "battery": {
                "uri": "ms-settings:batterysaver",
                "label": "battery settings"
            },
            "storage": {
                "uri": "ms-settings:storagesense",
                "label": "storage settings"
            },
            "apps": {
                "uri": "ms-settings:appsfeatures",
                "label": "apps settings"
            },
            "uninstall": {
                "uri": "ms-settings:appsfeatures",
                "label": "installed apps settings"
            },
            "windows update": {
                "uri": "ms-settings:windowsupdate",
                "label": "Windows Update settings"
            },
            "update": {
                "uri": "ms-settings:windowsupdate",
                "label": "Windows Update settings"
            },
            "privacy": {
                "uri": "ms-settings:privacy",
                "label": "privacy settings"
            },
            "mouse": {
                "uri": "ms-settings:mousetouchpad",
                "label": "mouse settings"
            },
            "keyboard": {
                "uri": "ms-settings:typing",
                "label": "keyboard settings"
            },
            "time": {
                "uri": "ms-settings:dateandtime",
                "label": "date and time settings"
            },
            "date": {
                "uri": "ms-settings:dateandtime",
                "label": "date and time settings"
            },
        }

        settings_page = settings_pages.get(
            page
        )

        if not settings_page:
            return f"Unknown settings page: {page}"

        return self.open_settings_uri(
            settings_page["uri"],
            settings_page["label"]
        )