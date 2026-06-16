from jarvis.services.clipboard_control import ClipboardControl


def main():
    clipboard = ClipboardControl()

    print("=" * 50)
    print("Jarvis Clipboard Control Test")
    print("=" * 50)

    print(clipboard.copy_text("Jarvis clipboard test."))
    print(clipboard.show_clipboard())
    print(clipboard.copy_current_date())
    print(clipboard.copy_current_time())
    print(clipboard.clear_clipboard())


if __name__ == "__main__":
    main()