from jarvis.services.app_discovery import AppDiscovery


scanner = AppDiscovery()

apps = scanner.scan_all()

print("=" * 50)
print(f"Applications Found: {len(apps)}")
print("=" * 50)

for name, path in list(apps.items())[:30]:
    print(name, "->", path)