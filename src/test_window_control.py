from jarvis.services.window_control import WindowControl


def main():
    window = WindowControl()

    print("=" * 50)
    print("Jarvis Window Control Test")
    print("=" * 50)

    print("This test will show desktop in 2 seconds.")
    print(window.show_desktop())


if __name__ == "__main__":
    main()