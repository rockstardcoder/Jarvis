from jarvis.tools.registry import ToolRegistry

from jarvis.tools.open_app import OpenAppTool
from jarvis.tools.close_app import CloseAppTool
from jarvis.tools.refresh_apps import RefreshAppsTool
from jarvis.tools.list_apps import ListAppsTool

from jarvis.tools.system_control import SystemControlTool
from jarvis.tools.web_control import WebControlTool
from jarvis.tools.browser_control import BrowserControlTool
from jarvis.tools.file_control import FileControlTool
from jarvis.tools.clipboard_control import ClipboardControlTool
from jarvis.tools.window_control import WindowControlTool
from jarvis.tools.screenshot_control import ScreenshotControlTool
from jarvis.tools.ppt_maker import PPTMakerTool
from jarvis.tools.document_maker import DocumentMakerTool
from jarvis.tools.pdf_tools import PDFToolsTool


class ToolManager:

    def __init__(self):

        self.registry = ToolRegistry()

        self.registry.register(
            OpenAppTool()
        )

        self.registry.register(
            CloseAppTool()
        )

        self.registry.register(
            RefreshAppsTool()
        )

        self.registry.register(
            ListAppsTool()
        )

        self.registry.register(
            SystemControlTool()
        )

        self.registry.register(
            WebControlTool()
        )

        self.registry.register(
            BrowserControlTool()
        )

        self.registry.register(
            FileControlTool()
        )

        self.registry.register(
            ClipboardControlTool()
        )

        self.registry.register(
            WindowControlTool()
        )

        self.registry.register(
            ScreenshotControlTool()
        )

        self.registry.register(
            PPTMakerTool()
        )

        self.registry.register(
            DocumentMakerTool()
        )

        self.registry.register(
            PDFToolsTool()
        )

    def execute(
        self,
        tool_name: str,
        **kwargs
    ):

        tool = self.registry.get(
            tool_name
        )

        if tool is None:
            return (
                f"Tool '{tool_name}' "
                f"not found."
            )

        return tool.execute(
            **kwargs
        )