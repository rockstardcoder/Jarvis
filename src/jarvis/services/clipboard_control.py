import time
from datetime import datetime

import win32api
import win32clipboard
import win32con


VK_LEFT_WINDOWS = 0x5B


class ClipboardControl:

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

        for key in reversed(keys):
            self.key_up(
                key
            )

            time.sleep(
                0.02
            )

        time.sleep(
            0.08
        )

    def set_clipboard_text(
        self,
        text: str
    ) -> bool:
        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()

            win32clipboard.SetClipboardText(
                str(text)
            )

            win32clipboard.CloseClipboard()

            return True

        except Exception:
            try:
                win32clipboard.CloseClipboard()
            except Exception:
                pass

            return False

    def get_clipboard_text(
        self
    ) -> str:
        try:
            win32clipboard.OpenClipboard()

            if not win32clipboard.IsClipboardFormatAvailable(
                win32con.CF_UNICODETEXT
            ):
                win32clipboard.CloseClipboard()
                return ""

            text = win32clipboard.GetClipboardData(
                win32con.CF_UNICODETEXT
            )

            win32clipboard.CloseClipboard()

            return str(text)

        except Exception:
            try:
                win32clipboard.CloseClipboard()
            except Exception:
                pass

            return ""

    def clear_clipboard(
        self
    ) -> str:
        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.CloseClipboard()

            return "Clipboard cleared."

        except Exception as e:
            try:
                win32clipboard.CloseClipboard()
            except Exception:
                pass

            return f"Failed to clear clipboard: {e}"

    def copy_text(
        self,
        text: str
    ) -> str:
        if not str(text).strip():
            return "No text was provided."

        success = self.set_clipboard_text(
            text
        )

        if success:
            return "Text copied to clipboard."

        return "Failed to copy text to clipboard."

    def show_clipboard(
        self
    ) -> str:
        text = self.get_clipboard_text()

        if not text:
            return "Clipboard is empty or does not contain text."

        max_length = 1000

        if len(text) > max_length:
            text = text[:max_length] + "\n...clipboard text is longer."

        return f"Clipboard:\n{text}"

    def copy_current_date(
        self
    ) -> str:
        value = datetime.now().strftime(
            "%d-%m-%Y"
        )

        self.set_clipboard_text(
            value
        )

        return f"Copied current date: {value}"

    def copy_current_time(
        self
    ) -> str:
        value = datetime.now().strftime(
            "%I:%M %p"
        )

        self.set_clipboard_text(
            value
        )

        return f"Copied current time: {value}"

    def copy_current_datetime(
        self
    ) -> str:
        value = datetime.now().strftime(
            "%d-%m-%Y %I:%M %p"
        )

        self.set_clipboard_text(
            value
        )

        return f"Copied current date and time: {value}"

    def open_clipboard_history(
        self
    ) -> str:
        self.hotkey(
            VK_LEFT_WINDOWS,
            ord("V")
        )

        return "Opening clipboard history."

    def wait_before_target_action(
        self,
        delay: float = 2.0
    ):
        time.sleep(
            delay
        )

    def paste_clipboard(
        self
    ) -> str:
        self.wait_before_target_action()

        self.hotkey(
            win32con.VK_CONTROL,
            ord("V")
        )

        return "Pasted clipboard content."

    def type_text(
        self,
        text: str
    ) -> str:
        if not str(text).strip():
            return "No text was provided."

        success = self.set_clipboard_text(
            text
        )

        if not success:
            return "Failed to prepare text for typing."

        self.wait_before_target_action()

        self.hotkey(
            win32con.VK_CONTROL,
            ord("V")
        )

        return "Typed text."

    def copy_selected_text(
        self
    ) -> str:
        self.wait_before_target_action()

        self.hotkey(
            win32con.VK_CONTROL,
            ord("C")
        )

        return "Copied selected text."

    def cut_selected_text(
        self
    ) -> str:
        self.wait_before_target_action()

        self.hotkey(
            win32con.VK_CONTROL,
            ord("X")
        )

        return "Cut selected text."

    def select_all(
        self
    ) -> str:
        self.wait_before_target_action()

        self.hotkey(
            win32con.VK_CONTROL,
            ord("A")
        )

        return "Selected all text."

    def press_enter(
        self
    ) -> str:
        self.wait_before_target_action()

        self.press_key(
            win32con.VK_RETURN
        )

        return "Pressed Enter."

    def press_tab(
        self
    ) -> str:
        self.wait_before_target_action()

        self.press_key(
            win32con.VK_TAB
        )

        return "Pressed Tab."

    def press_escape(
        self
    ) -> str:
        self.wait_before_target_action()

        self.press_key(
            win32con.VK_ESCAPE
        )

        return "Pressed Escape."