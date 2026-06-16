import time

import win32api
import win32con
import win32gui


VK_LEFT_WINDOWS = 0x5B


class WindowControl:

    def key_down(
        self,
        key_code: int
    ):
        win32api.keybd_event(
            key_code,
            0,
            0,
            0
        )

    def key_up(
        self,
        key_code: int
    ):
        win32api.keybd_event(
            key_code,
            0,
            win32con.KEYEVENTF_KEYUP,
            0
        )

    def press_key(
        self,
        key_code: int
    ):
        self.key_down(
            key_code
        )

        time.sleep(
            0.05
        )

        self.key_up(
            key_code
        )

        time.sleep(
            0.05
        )

    def hotkey(
        self,
        *keys: int
    ):
        for key in keys:
            self.key_down(
                key
            )

            time.sleep(
                0.02
            )

        time.sleep(
            0.05
        )

        for key in reversed(
            keys
        ):
            self.key_up(
                key
            )

            time.sleep(
                0.02
            )

        time.sleep(
            0.08
        )

    def wait_for_target_window(
        self,
        delay: float = 2.0
    ):
        time.sleep(
            delay
        )

    def get_active_window(
        self
    ):
        return win32gui.GetForegroundWindow()

    def is_valid_window(
        self,
        hwnd
    ) -> bool:
        if not hwnd:
            return False

        if not win32gui.IsWindow(
            hwnd
        ):
            return False

        return True

    def minimize_active_window(
        self
    ) -> str:
        self.wait_for_target_window()

        hwnd = self.get_active_window()

        if not self.is_valid_window(
            hwnd
        ):
            return "No active window was found."

        try:
            win32gui.ShowWindow(
                hwnd,
                win32con.SW_MINIMIZE
            )

            return "Minimized active window."

        except Exception as e:
            return f"Failed to minimize active window: {e}"

    def maximize_active_window(
        self
    ) -> str:
        self.wait_for_target_window()

        hwnd = self.get_active_window()

        if not self.is_valid_window(
            hwnd
        ):
            return "No active window was found."

        try:
            win32gui.ShowWindow(
                hwnd,
                win32con.SW_MAXIMIZE
            )

            return "Maximized active window."

        except Exception as e:
            return f"Failed to maximize active window: {e}"

    def restore_active_window(
        self
    ) -> str:
        self.wait_for_target_window()

        hwnd = self.get_active_window()

        if not self.is_valid_window(
            hwnd
        ):
            return "No active window was found."

        try:
            win32gui.ShowWindow(
                hwnd,
                win32con.SW_RESTORE
            )

            return "Restored active window."

        except Exception as e:
            return f"Failed to restore active window: {e}"

    def close_active_window(
        self
    ) -> str:
        self.wait_for_target_window()

        try:
            self.hotkey(
                win32con.VK_MENU,
                win32con.VK_F4
            )

            return "Closing active window."

        except Exception as e:
            return f"Failed to close active window: {e}"

    def snap_left(
        self
    ) -> str:
        self.wait_for_target_window()

        self.hotkey(
            VK_LEFT_WINDOWS,
            win32con.VK_LEFT
        )

        return "Snapped window left."

    def snap_right(
        self
    ) -> str:
        self.wait_for_target_window()

        self.hotkey(
            VK_LEFT_WINDOWS,
            win32con.VK_RIGHT
        )

        return "Snapped window right."

    def snap_up(
        self
    ) -> str:
        self.wait_for_target_window()

        self.hotkey(
            VK_LEFT_WINDOWS,
            win32con.VK_UP
        )

        return "Snapped window up."

    def snap_down(
        self
    ) -> str:
        self.wait_for_target_window()

        self.hotkey(
            VK_LEFT_WINDOWS,
            win32con.VK_DOWN
        )

        return "Snapped window down."

    def move_to_next_monitor(
        self
    ) -> str:
        self.wait_for_target_window()

        self.hotkey(
            VK_LEFT_WINDOWS,
            win32con.VK_SHIFT,
            win32con.VK_RIGHT
        )

        return "Moved window to next monitor."

    def move_to_previous_monitor(
        self
    ) -> str:
        self.wait_for_target_window()

        self.hotkey(
            VK_LEFT_WINDOWS,
            win32con.VK_SHIFT,
            win32con.VK_LEFT
        )

        return "Moved window to previous monitor."

    def show_desktop(
        self
    ) -> str:
        self.hotkey(
            VK_LEFT_WINDOWS,
            ord("D")
        )

        return "Showing desktop."

    def task_view(
        self
    ) -> str:
        self.hotkey(
            VK_LEFT_WINDOWS,
            win32con.VK_TAB
        )

        return "Opening task view."

    def switch_window(
        self
    ) -> str:
        self.hotkey(
            win32con.VK_MENU,
            win32con.VK_TAB
        )

        return "Switching window."

    def minimize_all_windows(
        self
    ) -> str:
        self.hotkey(
            VK_LEFT_WINDOWS,
            ord("M")
        )

        return "Minimized all windows."

    def restore_minimized_windows(
        self
    ) -> str:
        self.hotkey(
            VK_LEFT_WINDOWS,
            win32con.VK_SHIFT,
            ord("M")
        )

        return "Restored minimized windows."