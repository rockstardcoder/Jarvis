from jarvis.tools.base_tool import BaseTool
from jarvis.services.clipboard_control import ClipboardControl


class ClipboardControlTool(BaseTool):

    name = "clipboard_control"

    def execute(
        self,
        action: str,
        value: str | None = None
    ):

        clipboard = ClipboardControl()

        if action == "copy_text":
            return clipboard.copy_text(
                value or ""
            )

        if action == "show_clipboard":
            return clipboard.show_clipboard()

        if action == "clear_clipboard":
            return clipboard.clear_clipboard()

        if action == "copy_date":
            return clipboard.copy_current_date()

        if action == "copy_time":
            return clipboard.copy_current_time()

        if action == "copy_datetime":
            return clipboard.copy_current_datetime()

        if action == "open_clipboard_history":
            return clipboard.open_clipboard_history()

        if action == "paste":
            return clipboard.paste_clipboard()

        if action == "type_text":
            return clipboard.type_text(
                value or ""
            )

        if action == "copy_selected":
            return clipboard.copy_selected_text()

        if action == "cut_selected":
            return clipboard.cut_selected_text()

        if action == "select_all":
            return clipboard.select_all()

        if action == "press_enter":
            return clipboard.press_enter()

        if action == "press_tab":
            return clipboard.press_tab()

        if action == "press_escape":
            return clipboard.press_escape()

        return f"Unknown clipboard action: {action}"