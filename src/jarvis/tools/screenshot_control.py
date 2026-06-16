from jarvis.tools.base_tool import BaseTool
from jarvis.services.screenshot_control import ScreenshotControl


class ScreenshotControlTool(BaseTool):

    name = "screenshot_control"

    def execute(
        self,
        action: str
    ):

        screenshot = ScreenshotControl()

        if action == "full_screenshot":
            return screenshot.delayed_capture_full_screen()

        if action == "active_window_screenshot":
            return screenshot.delayed_capture_active_window()

        if action == "copy_full_screenshot":
            return screenshot.delayed_copy_full_screenshot()

        if action == "copy_active_window_screenshot":
            return screenshot.delayed_copy_active_window_screenshot()

        if action == "open_screenshot_folder":
            return screenshot.open_screenshot_folder()

        if action == "open_snipping_tool":
            return screenshot.open_snipping_tool()

        if action == "open_screen_snip":
            return screenshot.open_screen_snip()

        return f"Unknown screenshot action: {action}"