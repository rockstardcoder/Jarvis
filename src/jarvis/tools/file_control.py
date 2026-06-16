from jarvis.tools.base_tool import BaseTool
from jarvis.services.file_control import FileControl


class FileControlTool(BaseTool):

    name = "file_control"

    def execute(
        self,
        action: str,
        target: str | None = None
    ):

        file_control = FileControl()

        if action == "refresh_folders":
            return file_control.refresh_folder_index()

        if action == "open_folder":
            if not target:
                return "No folder name was provided."

            return file_control.open_folder(
                target
            )

        if action == "find_folder":
            if not target:
                return "No folder name was provided."

            return file_control.find_folder(
                target
            )

        if action == "open_path":
            if not target:
                return "No path was provided."

            return file_control.open_path(
                target
            )

        return f"Unknown file action: {action}"