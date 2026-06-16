from jarvis.services.web_control import WebControl


def main():
    web = WebControl()

    shortcuts = web.load_shortcuts()

    print("=" * 50)
    print("Jarvis Web Control Test")
    print("=" * 50)

    print(f"Loaded shortcuts: {len(shortcuts)}")

    print(web.open_shortcut("google"))
    print(web.open_shortcut("facebook"))
    print(web.open_shortcut("formula 1"))
    print(web.search("google", "python tkinter tutorial"))


if __name__ == "__main__":
    main()