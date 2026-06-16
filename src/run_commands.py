from jarvis.core.router import Router
from jarvis.tools.tool_manager import ToolManager


COMMANDS = [
    "open edge",
    "close edge",
    "open powerpoint",
    "close powerpoint",
    "open comet",
    "close comet",
    "open excel",
    "close excel",
    "refresh apps",
]


def main():
    router = Router()
    tool_manager = ToolManager()

    print("=" * 40)
    print("Jarvis Command Test Runner")
    print("=" * 40)

    for command in COMMANDS:
        print(f"\nYou: {command}")

        route = router.route(command)

        if not route:
            print("Jarvis: No route found.")
            continue

        tool_name = route.pop("tool")
        result = tool_manager.execute(tool_name, **route)

        print(f"Jarvis: {result}")


if __name__ == "__main__":
    main()
