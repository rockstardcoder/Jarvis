from jarvis.services.app_discovery import AppDiscovery


discovery = AppDiscovery()

discovery.apps["steam"] = (
    r"C:\Program Files (x86)\Steam\steam.exe"
)

discovery.save()

print(
    discovery.load()
)