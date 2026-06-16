from jarvis.services.browser_control import BrowserControl


def main():
    browser = BrowserControl()

    print("=" * 50)
    print("Jarvis Browser Control Test")
    print("=" * 50)

    print(browser.execute("new_tab"))
    print(browser.execute("refresh"))
    print(browser.execute("close_tab"))


if __name__ == "__main__":
    main()