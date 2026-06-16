from jarvis.tools.tool_manager import ToolManager


manager = ToolManager()

result = manager.execute(
    "open_app",
    app_name="powerpoint"
)

print(result)