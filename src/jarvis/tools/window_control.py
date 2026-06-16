from jarvis.tools.base_tool import BaseTool
from jarvis.services.window_control import WindowControl


class WindowControlTool(BaseTool):

    name = "window_control"

    def execute(
        self,
        action: str
    ):

        window = WindowControl()

        if action == "minimize":
            return window.minimize_active_window()

        if action == "maximize":
            return window.maximize_active_window()

        if action == "restore":
            return window.restore_active_window()

        if action == "close":
            return window.close_active_window()

        if action == "snap_left":
            return window.snap_left()

        if action == "snap_right":
            return window.snap_right()

        if action == "snap_up":
            return window.snap_up()

        if action == "snap_down":
            return window.snap_down()

        if action == "next_monitor":
            return window.move_to_next_monitor()

        if action == "previous_monitor":
            return window.move_to_previous_monitor()

        if action == "show_desktop":
            return window.show_desktop()

        if action == "task_view":
            return window.task_view()

        if action == "switch_window":
            return window.switch_window()

        if action == "minimize_all":
            return window.minimize_all_windows()

        if action == "restore_minimized":
            return window.restore_minimized_windows()

        return f"Unknown window action: {action}"