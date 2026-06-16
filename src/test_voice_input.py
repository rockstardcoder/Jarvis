from jarvis.services.voice.stt_service import STTService


def main():
    stt = STTService()

    print("=" * 50)
    print("Jarvis Voice Input Test")
    print("=" * 50)

    print(
        stt.list_microphones()
    )

    print()
    print("Speak one short command after it starts listening.")
    print("Example: open notepad")
    print()

    result = stt.listen_once()

    print("=" * 50)
    print("Result")
    print("=" * 50)
    print(result["message"])

    if result["success"]:
        print(
            f"Recognized text: {result['text']}"
        )


if __name__ == "__main__":
    main()