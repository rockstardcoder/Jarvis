from jarvis.ai.llm_router import LLMRouter
from jarvis.ai.memory_store import MemoryStore
from jarvis.tools.system_info import SystemInfoTool


def test_ai_planner():
    memory = MemoryStore()
    router = LLMRouter()

    commands = [
        "close notepad then open comet and search what is python on google in comet",
        "search mr beast on youtube",
        "open youtube",
        "close this tab",
        "what is my gpu",
        "gpu usage"
    ]

    print("=" * 60)
    print("AI Planner Test")
    print("=" * 60)

    for command in commands:
        result = router.plan(
            command,
            memory_context=memory.get_context_text()
        )

        print()
        print(f"Command: {command}")
        print(f"Success: {result.get('success')}")
        print(f"Message: {result.get('message')}")
        print(f"Routes: {result.get('routes')}")


def test_memory():
    memory = MemoryStore()

    print()
    print("=" * 60)
    print("Memory Test")
    print("=" * 60)

    print(
        memory.extract_and_store_system_profile(
            "gpu is rtx 4060, processor is i5 14600k and ram is 32gb"
        )
    )

    print()
    print(memory.get_context_text())


def test_system_info():
    tool = SystemInfoTool()

    print()
    print("=" * 60)
    print("System Info Test")
    print("=" * 60)

    print(
        tool.execute(
            action="summary"
        )
    )

    print()
    print(
        tool.execute(
            action="usage"
        )
    )


def main():
    test_memory()
    test_system_info()
    test_ai_planner()


if __name__ == "__main__":
    main()