from jarvis.services.uwp_discovery import UWPDiscovery


def main():
    scanner = UWPDiscovery()
    apps = scanner.scan_all()

    print("=" * 50)
    print(f"UWP / Store Apps Found: {len(apps)}")
    print("=" * 50)

    for name, app_id in list(apps.items())[:80]:
        print(f"{name} -> {app_id}")


if __name__ == "__main__":
    main()