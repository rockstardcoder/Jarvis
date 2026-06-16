from jarvis.tools.browser_intelligence import BrowserIntelligenceTool
from jarvis.tools.system_info import SystemInfoTool
from jarvis.tools.web_reader import WebReaderTool
from jarvis.tools.window_intelligence import WindowIntelligenceTool


def main():
    system_tool = SystemInfoTool()
    window_tool = WindowIntelligenceTool()
    browser_tool = BrowserIntelligenceTool()
    web_tool = WebReaderTool()

    print("=" * 60)
    print("System Info Upgrade Test")
    print("=" * 60)
    print(system_tool.execute(action="summary"))
    print()
    print(system_tool.execute(action="battery"))
    print()
    print(system_tool.execute(action="storage"))
    print()
    print(system_tool.execute(action="network"))
    print()
    print(system_tool.execute(action="thermal"))

    print()
    print("=" * 60)
    print("Window Intelligence Test")
    print("=" * 60)
    print(window_tool.execute(action="list_windows"))

    print()
    print("=" * 60)
    print("Browser Intelligence Test")
    print("=" * 60)
    print(browser_tool.execute(action="current_title"))

    print()
    print("=" * 60)
    print("Web Reader Test")
    print("=" * 60)
    print(web_tool.execute(action="wikipedia", target="Python programming language"))


if __name__ == "__main__":
    main()