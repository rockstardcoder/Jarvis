import os
import subprocess
import time
from datetime import datetime
from io import BytesIO
from pathlib import Path

import win32clipboard
import win32con
import win32gui
from PIL import ImageGrab


SCREENSHOT_DIR = Path(
    "data/screenshots"
)


class ScreenshotControl:

    def ensure_screenshot_dir(
        self
    ):
        SCREENSHOT_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

    def create_screenshot_path(
        self,
        prefix: str = "screenshot"
    ) -> Path:
        self.ensure_screenshot_dir()

        timestamp = datetime.now().strftime(
            "%Y-%m-%d_%H-%M-%S"
        )

        return SCREENSHOT_DIR / f"{prefix}_{timestamp}.png"

    def capture_full_screen(
        self
    ) -> str:
        try:
            path = self.create_screenshot_path(
                "full_screenshot"
            )

            image = ImageGrab.grab(
                all_screens=True
            )

            image.save(
                path
            )

            return f"Screenshot saved: {path}"

        except Exception as e:
            return f"Failed to take screenshot: {e}"

    def get_active_window_rect(
        self
    ):
        hwnd = win32gui.GetForegroundWindow()

        if not hwnd:
            return None

        if not win32gui.IsWindow(
            hwnd
        ):
            return None

        try:
            rect = win32gui.GetWindowRect(
                hwnd
            )

            left, top, right, bottom = rect

            if right <= left or bottom <= top:
                return None

            return rect

        except Exception:
            return None

    def capture_active_window(
        self
    ) -> str:
        try:
            rect = self.get_active_window_rect()

            if rect is None:
                return "No active window was found."

            path = self.create_screenshot_path(
                "active_window"
            )

            image = ImageGrab.grab(
                bbox=rect
            )

            image.save(
                path
            )

            return f"Active window screenshot saved: {path}"

        except Exception as e:
            return f"Failed to capture active window: {e}"

    def image_to_clipboard(
        self,
        image
    ) -> bool:
        try:
            output = BytesIO()

            image.convert(
                "RGB"
            ).save(
                output,
                "BMP"
            )

            data = output.getvalue()[14:]
            output.close()

            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()

            win32clipboard.SetClipboardData(
                win32con.CF_DIB,
                data
            )

            win32clipboard.CloseClipboard()

            return True

        except Exception:
            try:
                win32clipboard.CloseClipboard()
            except Exception:
                pass

            return False

    def copy_full_screenshot(
        self
    ) -> str:
        try:
            image = ImageGrab.grab(
                all_screens=True
            )

            success = self.image_to_clipboard(
                image
            )

            if success:
                return "Screenshot copied to clipboard."

            return "Failed to copy screenshot to clipboard."

        except Exception as e:
            return f"Failed to copy screenshot: {e}"

    def copy_active_window_screenshot(
        self
    ) -> str:
        try:
            rect = self.get_active_window_rect()

            if rect is None:
                return "No active window was found."

            image = ImageGrab.grab(
                bbox=rect
            )

            success = self.image_to_clipboard(
                image
            )

            if success:
                return "Active window screenshot copied to clipboard."

            return "Failed to copy active window screenshot."

        except Exception as e:
            return f"Failed to copy active window screenshot: {e}"

    def open_screenshot_folder(
        self
    ) -> str:
        try:
            self.ensure_screenshot_dir()

            os.startfile(
                str(SCREENSHOT_DIR.resolve())
            )

            return "Opening screenshot folder."

        except Exception as e:
            return f"Failed to open screenshot folder: {e}"

    def open_snipping_tool(
        self
    ) -> str:
        try:
            subprocess.Popen(
                [
                    "SnippingTool.exe"
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL
            )

            return "Opening Snipping Tool."

        except Exception as e:
            return f"Failed to open Snipping Tool: {e}"

    def open_screen_snip(
        self
    ) -> str:
        try:
            subprocess.Popen(
                [
                    "explorer.exe",
                    "ms-screenclip:"
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL
            )

            return "Opening screen snip."

        except Exception as e:
            return f"Failed to open screen snip: {e}"

    def delayed_capture_full_screen(
        self,
        delay: float = 2.0
    ) -> str:
        time.sleep(
            delay
        )

        return self.capture_full_screen()

    def delayed_capture_active_window(
        self,
        delay: float = 2.0
    ) -> str:
        time.sleep(
            delay
        )

        return self.capture_active_window()

    def delayed_copy_full_screenshot(
        self,
        delay: float = 2.0
    ) -> str:
        time.sleep(
            delay
        )

        return self.copy_full_screenshot()

    def delayed_copy_active_window_screenshot(
        self,
        delay: float = 2.0
    ) -> str:
        time.sleep(
            delay
        )

        return self.copy_active_window_screenshot()