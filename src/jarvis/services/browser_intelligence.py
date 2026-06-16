import time

import psutil
import win32clipboard
import win32com.client
import win32gui
import win32process

from jarvis.services.window_intelligence import WindowIntelligence


BROWSER_PROCESS_NAMES = {
    "chrome.exe",
    "msedge.exe",
    "firefox.exe",
    "brave.exe",
    "opera.exe",
    "opera_gx.exe",
    "vivaldi.exe",
    "comet.exe",
    "arc.exe"
}


class BrowserIntelligence:

    def __init__(
        self
    ):
        self.windows = WindowIntelligence()

    def send_keys(
        self,
        keys: str,
        delay: float = 0.15
    ):
        shell = win32com.client.Dispatch(
            "WScript.Shell"
        )

        shell.SendKeys(
            keys
        )

        time.sleep(
            delay
        )

    def get_clipboard_text(
        self
    ) -> str:
        try:
            win32clipboard.OpenClipboard()

            if win32clipboard.IsClipboardFormatAvailable(
                win32clipboard.CF_UNICODETEXT
            ):
                return win32clipboard.GetClipboardData(
                    win32clipboard.CF_UNICODETEXT
                )

        except Exception:
            return ""

        finally:
            try:
                win32clipboard.CloseClipboard()

            except Exception:
                pass

        return ""

    def set_clipboard_text(
        self,
        text: str
    ):
        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(
                win32clipboard.CF_UNICODETEXT,
                str(
                    text
                )
            )

        finally:
            try:
                win32clipboard.CloseClipboard()

            except Exception:
                pass

    def get_process_name(
        self,
        hwnd: int
    ) -> str:
        try:
            _, pid = win32process.GetWindowThreadProcessId(
                hwnd
            )

            return psutil.Process(
                pid
            ).name().lower()

        except Exception:
            return ""

    def is_browser_window(
        self,
        hwnd: int
    ) -> bool:
        process_name = self.get_process_name(
            hwnd
        )

        return process_name in BROWSER_PROCESS_NAMES

    def get_current_title(
        self
    ) -> str:
        hwnd = win32gui.GetForegroundWindow()

        title = win32gui.GetWindowText(
            hwnd
        ).strip()

        if not title:
            return "No active window title found."

        return title

    def get_current_url(
        self
    ) -> str:
        hwnd = win32gui.GetForegroundWindow()

        if not self.is_browser_window(
            hwnd
        ):
            return (
                "The active window does not look like a supported browser. "
                "Open/focus a browser tab first."
            )

        old_clipboard = self.get_clipboard_text()

        self.send_keys(
            "^l",
            0.15
        )

        self.send_keys(
            "^c",
            0.20
        )

        url = self.get_clipboard_text().strip()

        self.send_keys(
            "{ESC}",
            0.10
        )

        if old_clipboard:
            self.set_clipboard_text(
                old_clipboard
            )

        if not url:
            return "Could not read the current browser URL."

        return f"Current URL: {url}"

    def list_browser_windows(
        self
    ) -> list[dict]:
        browser_windows = []

        for window in self.windows.list_windows():
            process = window["process_name"].lower()

            if process in BROWSER_PROCESS_NAMES:
                browser_windows.append(
                    window
                )

        return browser_windows

    def format_browser_windows(
        self
    ) -> str:
        windows = self.list_browser_windows()

        if not windows:
            return "No browser windows found."

        lines = [
            "Browser windows:"
        ]

        for index, window in enumerate(
            windows,
            start=1
        ):
            lines.append(
                (
                    f"{index}. {window['title']} "
                    f"[{window['process_name']}]"
                )
            )

        return "\n".join(
            lines
        )

    def find_browser_window_by_title(
        self,
        target: str
    ) -> dict | None:
        target = str(
            target
        ).lower().strip()

        windows = self.list_browser_windows()

        for window in windows:
            if window["title"].lower() == target:
                return window

        for window in windows:
            if target in window["title"].lower():
                return window

        return None

    def switch_by_title(
        self,
        target: str
    ) -> str:
        window = self.find_browser_window_by_title(
            target
        )

        if not window:
            return (
                f"No browser window/tab title found matching: {target}. "
                "Without a browser extension, Jarvis can only see visible browser window titles."
            )

        ok = self.windows.activate_window(
            window["hwnd"]
        )

        if ok:
            return f"Switched to browser window: {window['title']}"

        return f"Could not switch to browser window: {window['title']}"

    def close_window_by_title(
        self,
        target: str
    ) -> str:
        window = self.find_browser_window_by_title(
            target
        )

        if not window:
            return (
                f"No browser window/tab title found matching: {target}. "
                "Without a browser extension, Jarvis can only see visible browser window titles."
            )

        ok = self.windows.close_window(
            window["hwnd"]
        )

        if ok:
            return f"Closed browser window: {window['title']}"

        return f"Could not close browser window: {window['title']}"

    def close_tab_by_title(
        self,
        target: str
    ) -> str:
        window = self.find_browser_window_by_title(
            target
        )

        if not window:
            return (
                f"No active browser title found matching: {target}. "
                "True inactive-tab closing needs the future browser extension."
            )

        if not self.windows.activate_window(
            window["hwnd"]
        ):
            return f"Could not focus browser window: {window['title']}"

        self.send_keys(
            "^w",
            0.20
        )

        return f"Closed current tab/window matching: {window['title']}"

    def switch_tab_by_title(
        self,
        target: str
    ) -> str:
        window = self.find_browser_window_by_title(
            target
        )

        if not window:
            return (
                f"No active browser title found matching: {target}. "
                "True inactive-tab switching needs the future browser extension."
            )

        ok = self.windows.activate_window(
            window["hwnd"]
        )

        if ok:
            return f"Focused browser window/tab title: {window['title']}"

        return f"Could not focus browser window/tab title: {window['title']}"