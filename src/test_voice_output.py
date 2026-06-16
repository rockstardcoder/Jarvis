import time

from jarvis.services.voice.tts_service import TTSService
from jarvis.services.voice.voice_config import VoiceConfig


def main():
    config = VoiceConfig()
    tts = TTSService()

    print("=" * 50)
    print("Jarvis Voice Output Test")
    print("=" * 50)

    print(f"Voice: {config.get_voice_name()}")
    print(f"Rate: {config.get_sapi_rate()}")
    print(f"Volume: {config.get_sapi_volume()}")

    text = "Jarvis voice output is online, Sir."

    print(f"Speaking: {text}")

    accepted = tts.speak(
        text
    )

    time.sleep(
        3
    )

    tts.shutdown(
        wait=False
    )

    if accepted:
        print("Voice output test completed.")
    else:
        print("Voice output test failed to start.")


if __name__ == "__main__":
    main()