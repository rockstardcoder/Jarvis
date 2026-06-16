from jarvis.services.screenshot_control import ScreenshotControl


def main():
    screenshot = ScreenshotControl()

    print("=" * 50)
    print("Jarvis Screenshot Control Test")
    print("=" * 50)

    print("Taking screenshot in 2 seconds.")
    print(screenshot.delayed_capture_full_screen())

    print(screenshot.open_screenshot_folder())


if __name__ == "__main__":
    main()