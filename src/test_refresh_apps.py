from jarvis.services.app_discovery import AppDiscovery


def print_section(title: str, data: dict):
    print()
    print("=" * 60)
    print(title)
    print("=" * 60)

    if not data:
        print("None")
        return

    for name, value in data.items():
        print(f"{name} -> {value}")


def main():
    discovery = AppDiscovery()
    summary = discovery.scan_with_summary()

    print("=" * 60)
    print("Jarvis App Refresh Summary")
    print("=" * 60)

    print(f"Total apps: {summary['total']}")
    print(f"Added: {len(summary['added'])}")
    print(f"Removed: {len(summary['removed'])}")
    print(f"Updated: {len(summary['updated'])}")

    print_section(
        "Added Apps",
        summary["added"]
    )

    print_section(
        "Removed Apps",
        summary["removed"]
    )

    print_section(
        "Updated Apps",
        summary["updated"]
    )


if __name__ == "__main__":
    main()