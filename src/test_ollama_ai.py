from jarvis.ai.llm_router import LLMRouter


def test_route(
    router: LLMRouter,
    command: str
):
    print("=" * 60)
    print(f"Command: {command}")

    result = router.route(
        command
    )

    print(f"Success: {result.get('success')}")
    print(f"Message: {result.get('message')}")
    print(f"Route: {result.get('route')}")
    print(f"Raw: {result.get('raw')}")


def main():
    router = LLMRouter()

    print("=" * 60)
    print("Jarvis Ollama AI Brain Test")
    print("=" * 60)
    print(router.health_check())

    test_route(
        router,
        "can you open notepad for me"
    )

    test_route(
        router,
        "make a school presentation about water conservation"
    )

    test_route(
        router,
        "create a professional report about artificial intelligence"
    )

    test_route(
        router,
        "take a screenshot of my screen"
    )

    test_route(
        router,
        "search google for best python tutorial"
    )

    test_route(
        router,
        "what is the capital of France"
    )

    print("=" * 60)
    print("Fallback chat test")
    print("=" * 60)

    response = router.generate_response(
        "Say hello in one short sentence."
    )

    print(
        response
        if response
        else "No fallback response returned."
    )


if __name__ == "__main__":
    main()