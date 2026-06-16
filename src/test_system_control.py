from jarvis.services.system_control import SystemControl


def main():
    system = SystemControl()

    print("=" * 50)
    print("Jarvis System Control Test")
    print("=" * 50)

    print(system.volume_up())
    print(system.volume_down())
    print(system.mute_volume())
    print(system.mute_volume())
    print(system.open_settings("display"))


if __name__ == "__main__":
    main() 