import psutil
import win32con
import win32gui
import win32process


class WindowIntelligence:

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
            ).name()

        except Exception:
            return ""

    def get_window_info(
        self,
        hwnd: int
    ) -> dict:
        title = win32gui.GetWindowText(
            hwnd
        ).strip()

        class_name = ""

        try:
            class_name = win32gui.GetClassName(
                hwnd
            )

        except Exception:
            pass

        process_name = self.get_process_name(
            hwnd
        )

        return {
            "hwnd": hwnd,
            "title": title,
            "class_name": class_name,
            "process_name": process_name
        }

    def list_windows(
        self
    ) -> list[dict]:
        windows = []

        def callback(
            hwnd,
            _
        ):
            if not win32gui.IsWindowVisible(
                hwnd
            ):
                return

            title = win32gui.GetWindowText(
                hwnd
            ).strip()

            if not title:
                return

            windows.append(
                self.get_window_info(
                    hwnd
                )
            )

        win32gui.EnumWindows(
            callback,
            None
        )

        return windows

    def format_window_list(
        self
    ) -> str:
        windows = self.list_windows()

        if not windows:
            return "No visible windows found."

        lines = [
            "Visible windows:"
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

    def is_file_explorer_window(
        self,
        window: dict
    ) -> bool:
        process_name = window.get(
            "process_name",
            ""
        ).lower()

        class_name = window.get(
            "class_name",
            ""
        )

        return (
            process_name == "explorer.exe"
            and class_name in [
                "CabinetWClass",
                "ExploreWClass"
            ]
        )

    def list_file_explorer_windows(
        self
    ) -> list[dict]:
        return [
            window
            for window in self.list_windows()
            if self.is_file_explorer_window(
                window
            )
        ]

    def format_file_explorer_windows(
        self
    ) -> str:
        windows = self.list_file_explorer_windows()

        if not windows:
            return "No File Explorer folder windows found."

        lines = [
            "File Explorer windows:"
        ]

        for index, window in enumerate(
            windows,
            start=1
        ):
            lines.append(
                f"{index}. {window['title']}"
            )

        return "\n".join(
            lines
        )

    def find_window_by_title(
        self,
        target: str,
        windows: list[dict] | None = None
    ) -> dict | None:
        target = str(
            target
        ).lower().strip()

        if not target:
            return None

        windows = windows or self.list_windows()

        exact_matches = [
            window
            for window in windows
            if window["title"].lower() == target
        ]

        if exact_matches:
            return exact_matches[0]

        partial_matches = [
            window
            for window in windows
            if target in window["title"].lower()
        ]

        if partial_matches:
            return partial_matches[0]

        return None

    def activate_window(
        self,
        hwnd: int
    ) -> bool:
        try:
            win32gui.ShowWindow(
                hwnd,
                win32con.SW_RESTORE
            )

            win32gui.SetForegroundWindow(
                hwnd
            )

            return True

        except Exception:
            return False

    def close_window(
        self,
        hwnd: int
    ) -> bool:
        try:
            win32gui.PostMessage(
                hwnd,
                win32con.WM_CLOSE,
                0,
                0
            )

            return True

        except Exception:
            return False

    def close_by_title(
        self,
        target: str
    ) -> str:
        window = self.find_window_by_title(
            target
        )

        if not window:
            return f"No window found matching: {target}"

        ok = self.close_window(
            window["hwnd"]
        )

        if ok:
            return f"Closed window: {window['title']}"

        return f"Could not close window: {window['title']}"

    def switch_by_title(
        self,
        target: str
    ) -> str:
        window = self.find_window_by_title(
            target
        )

        if not window:
            return f"No window found matching: {target}"

        ok = self.activate_window(
            window["hwnd"]
        )

        if ok:
            return f"Switched to window: {window['title']}"

        return f"Could not switch to window: {window['title']}"

    def close_file_explorer(
        self,
        target: str | None = None
    ) -> str:
        windows = self.list_file_explorer_windows()

        if not windows:
            return "No File Explorer folder window is open."

        if target:
            match = self.find_window_by_title(
                target,
                windows
            )

            if not match:
                return f"No File Explorer window found matching: {target}"

            ok = self.close_window(
                match["hwnd"]
            )

            if ok:
                return f"Closed File Explorer window: {match['title']}"

            return f"Could not close File Explorer window: {match['title']}"

        foreground = win32gui.GetForegroundWindow()

        for window in windows:
            if window["hwnd"] == foreground:
                ok = self.close_window(
                    window["hwnd"]
                )

                if ok:
                    return f"Closed File Explorer window: {window['title']}"

        ok = self.close_window(
            windows[0]["hwnd"]
        )

        if ok:
            return f"Closed File Explorer window: {windows[0]['title']}"

        return "Could not close File Explorer window."

    def close_task_manager(
        self
    ) -> str:
        import subprocess
        import time

        windows = self.list_windows()

        for window in windows:
            title = window["title"].lower()
            process = window["process_name"].lower()

            if (
                "task manager" in title
                or process == "taskmgr.exe"
            ):
                ok = self.close_window(
                    window["hwnd"]
                )

                if ok:
                    time.sleep(
                        0.7
                    )

                    still_open = any(
                        item["process_name"].lower() == "taskmgr.exe"
                        for item in self.list_windows()
                    )

                    if not still_open:
                        return f"Closed window: {window['title']}"

                try:
                    subprocess.run(
                        [
                            "taskkill",
                            "/IM",
                            "Taskmgr.exe",
                            "/F"
                        ],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )

                    return "Closed Task Manager."

                except Exception:
                    return f"Could not close window: {window['title']}"

        return "Task Manager window was not found."