import json
import re
import string
import winreg
from pathlib import Path

import win32com.client

from jarvis.services.system_apps import SYSTEM_APPS


DATA_FILE = Path("data/apps.json")


BAD_APP_NAME_WORDS = [
    "professional plus",
    "ltsc professional",
    "server accounts",
    "language preferences",
    "spreadsheet compare",
    "reset preferences",
    "skinned",
    "uninstall",
    "uninstaller",
    "remove",
    "setup",
    "installer",
    "update",
    "updater",
    "maintenance",
    "repair",
    "runtime",
    "redistributable",
    "webview2 runtime",
    "clicktorun",
    "common files",
    "dotnet",
    "internet explorer",
]


BAD_EXE_WORDS = [
    "ospprearm",
    "appvlp",
    "unins",
    "uninstall",
    "setup",
    "installer",
    "install",
    "update",
    "updater",
    "helper",
    "service",
    "crash",
    "crashpad",
    "handler",
    "ffmpeg",
    "ffprobe",
    "python",
    "node",
    "npm",
    "npx",
    "vcredist",
    "redistributable",
    "repair",
    "maintenance",
    "webview",
    "clicktorun",
    "bootstrap",
    "elevation",
    "notification",
    "diagnostic",
    "telemetry",
    "driver",
    "drivers",
    "spddump",
    "telemetry",
    "lrio",
    "plugin",
    "plugins",
]


BAD_PATH_WORDS = [
    "common files",
    "telemetry",
    "easytuneengineservice",
    "package cache",
    "windows\\installer",
    "$recycle.bin",
    "system volume information",
    "windows\\winsxs",
    "windows\\servicing",
    "windows\\softwaredistribution",
    "appdata\\local\\temp",
    "appdata\\local\\packages",
    "appdata\\local\\microsoft",
    "appdata\\local\\google\\chrome",
    "appdata\\local\\pip",
    "appdata\\local\\npm-cache",
    "temp",
    "tmp",
    "cache",
]


REGISTRY_PATHS = [
    (
        winreg.HKEY_LOCAL_MACHINE,
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
    ),
    (
        winreg.HKEY_CURRENT_USER,
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
    ),
    (
        winreg.HKEY_LOCAL_MACHINE,
        r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
    ),
]


class AppDiscovery:

    def __init__(self):
        self.apps = {}

    def save(self):
        DATA_FILE.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(
            DATA_FILE,
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                self.apps,
                f,
                indent=4
            )

    def load(self):
        if not DATA_FILE.exists():
            return {}

        with open(
            DATA_FILE,
            "r",
            encoding="utf-8"
        ) as f:
            self.apps = json.load(f)

        return self.apps

    def normalize_name(self, name: str) -> str:
        name = str(name).lower().strip()

        name = name.replace(
            ".exe",
            ""
        )

        name = name.replace(
            " - shortcut",
            ""
        )

        name = re.sub(
            r"\s+",
            " ",
            name
        )

        return name.strip()

    def name_tokens(self, name: str) -> list[str]:
        cleaned = re.sub(
            r"[^a-z0-9]+",
            " ",
            str(name).lower()
        )

        tokens = [
            token
            for token in cleaned.split()
            if len(token) > 1
        ]

        ignored_tokens = {
            "the",
            "app",
            "application",
            "software",
            "desktop",
            "client",
            "manager",
            "launcher",
            "classic",
            "x64",
            "x86",
            "64",
            "32",
            "for",
            "and",
            "with",
            "tool",
            "tools",
            "service",
            "runtime",
        }

        return [
            token
            for token in tokens
            if token not in ignored_tokens
        ]

    def is_bad_app_name(self, app_name: str) -> bool:
        app_name = str(app_name).lower()

        return any(
            word in app_name
            for word in BAD_APP_NAME_WORDS
        )

    def is_bad_path(self, path: Path) -> bool:
        path_text = str(path).lower()

        return any(
            word in path_text
            for word in BAD_PATH_WORDS
        )

    def is_bad_exe(self, exe_path: Path) -> bool:
        exe_name = exe_path.name.lower()
        stem = exe_path.stem.lower()

        if exe_path.suffix.lower() != ".exe":
            return True

        if self.is_bad_path(exe_path):
            return True

        return any(
            word in stem or word in exe_name
            for word in BAD_EXE_WORDS
        )

    def clean_registry_path(self, raw_path: str) -> str | None:
        if not raw_path:
            return None

        path = str(raw_path).strip()

        if "," in path:
            path = path.split(",")[0]

        path = path.strip().strip('"')

        if not path.lower().endswith(".exe"):
            return None

        return path

    def read_registry_value(self, key, value_name: str):
        try:
            return winreg.QueryValueEx(
                key,
                value_name
            )[0]
        except Exception:
            return None

    def score_exe(
        self,
        exe_path: Path,
        app_name: str,
        install_folder: Path | None = None
    ) -> int:
        if self.is_bad_exe(exe_path):
            return -9999

        score = 0

        exe_stem = exe_path.stem.lower()
        app_name = str(app_name).lower()
        tokens = self.name_tokens(app_name)

        if exe_stem == app_name:
            score += 120

        compact_app = re.sub(
            r"[^a-z0-9]+",
            "",
            app_name
        )

        compact_exe = re.sub(
            r"[^a-z0-9]+",
            "",
            exe_stem
        )

        if compact_exe == compact_app:
            score += 100

        if compact_app and compact_app in compact_exe:
            score += 60

        if compact_exe and compact_exe in compact_app:
            score += 35

        for token in tokens:
            if token in exe_stem:
                score += 25

        if install_folder:
            folder_name = install_folder.name.lower()
            folder_tokens = self.name_tokens(folder_name)

            for token in folder_tokens:
                if token in exe_stem:
                    score += 15

        try:
            size = exe_path.stat().st_size

            if size > 300_000:
                score += 5

            if size > 2_000_000:
                score += 5

            if size > 20_000_000:
                score += 2

        except Exception:
            pass

        common_good_names = [
            "app",
            "main",
            "launcher",
            "client",
            "start",
        ]

        if exe_stem in common_good_names:
            score += 10

        return score

    def find_best_exe_in_folder(
        self,
        folder: Path,
        app_name: str,
        recursive_depth: int = 1
    ) -> str | None:
        if not folder.exists() or not folder.is_dir():
            return None

        if self.is_bad_path(folder):
            return None

        exe_files = []
        max_candidates = 50

        try:
            direct_items = list(folder.iterdir())
        except Exception:
            return None

        for item in direct_items:
            if len(exe_files) >= max_candidates:
                break

            try:
                if item.suffix.lower() == ".exe" and item.is_file():
                    exe_files.append(item)
            except Exception:
                continue

        if recursive_depth >= 1:
            for item in direct_items:
                if len(exe_files) >= max_candidates:
                    break

                try:
                    if not item.is_dir():
                        continue

                    if self.is_bad_path(item):
                        continue

                    try:
                        child_items = list(item.iterdir())
                    except Exception:
                        continue

                    for child in child_items:
                        if len(exe_files) >= max_candidates:
                            break

                        try:
                            if (
                                child.suffix.lower() == ".exe"
                                and child.is_file()
                            ):
                                exe_files.append(child)

                        except Exception:
                            continue

                except Exception:
                    continue

        if not exe_files:
            return None

        best_exe = None
        best_score = -9999

        for exe_path in exe_files:
            try:
                score = self.score_exe(
                    exe_path,
                    app_name,
                    folder
                )

                if score > best_score:
                    best_score = score
                    best_exe = exe_path

            except Exception:
                continue

        if best_exe is None:
            return None

        if best_score < 0:
            return None

        return str(best_exe)

    def scan_start_menu(self):
        shell = win32com.client.Dispatch(
            "WScript.Shell"
        )

        start_menu_locations = [
            Path(
                r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs"
            ),
            Path.home()
            / "AppData"
            / "Roaming"
            / "Microsoft"
            / "Windows"
            / "Start Menu"
            / "Programs",
        ]

        found_apps = {}

        for location in start_menu_locations:
            if not location.exists():
                continue

            for shortcut in location.rglob("*.lnk"):
                try:
                    app_name = self.normalize_name(
                        shortcut.stem
                    )

                    if self.is_bad_app_name(app_name):
                        continue

                    target = shell.CreateShortcut(
                        str(shortcut)
                    ).Targetpath

                    if not target:
                        continue

                    target_path = Path(target)

                    if target_path.suffix.lower() != ".exe":
                        continue

                    if self.is_bad_exe(target_path):
                        continue

                    found_apps[app_name] = str(target_path)

                except Exception:
                    pass

        return found_apps

    def scan_system_apps(self):
        found_apps = {}

        for name, exe in SYSTEM_APPS.items():
            app_name = self.normalize_name(name)
            found_apps[app_name] = exe

        return found_apps

    def scan_registry(self):
        found_apps = {}

        for hive, path in REGISTRY_PATHS:
            try:
                root = winreg.OpenKey(
                    hive,
                    path
                )

                count = winreg.QueryInfoKey(
                    root
                )[0]

                for i in range(count):
                    try:
                        subkey_name = winreg.EnumKey(
                            root,
                            i
                        )

                        subkey = winreg.OpenKey(
                            root,
                            subkey_name
                        )

                        display_name = self.read_registry_value(
                            subkey,
                            "DisplayName"
                        )

                        if not display_name:
                            continue

                        app_name = self.normalize_name(
                            display_name
                        )

                        if self.is_bad_app_name(app_name):
                            continue

                        exe_path = None

                        display_icon = self.read_registry_value(
                            subkey,
                            "DisplayIcon"
                        )

                        clean_icon_path = self.clean_registry_path(
                            display_icon
                        )

                        if clean_icon_path:
                            icon_path = Path(clean_icon_path)

                            if (
                                icon_path.exists()
                                and not self.is_bad_exe(icon_path)
                            ):
                                exe_path = str(icon_path)

                        if exe_path is None:
                            install_location = self.read_registry_value(
                                subkey,
                                "InstallLocation"
                            )

                            if install_location:
                                install_folder = Path(
                                    str(install_location).strip().strip('"')
                                )

                                exe_path = self.find_best_exe_in_folder(
                                    install_folder,
                                    app_name,
                                    recursive_depth=1
                                )

                        if exe_path:
                            found_apps[app_name] = exe_path

                    except Exception:
                        pass

            except Exception:
                pass

        return found_apps

    def get_drive_roots(self) -> list[Path]:
        drives = []

        for letter in string.ascii_uppercase:
            drive = Path(f"{letter}:/")

            if drive.exists():
                drives.append(drive)

        return drives

    def get_common_scan_locations(self) -> list[Path]:
        locations = []

        for drive in self.get_drive_roots():
            locations.extend(
                [
                    drive / "Program Files",
                    drive / "Program Files (x86)",
                    drive / "Games",
                    drive / "Game Launchers",
                    drive / "Steam",
                    drive / "Epic Games",
                    drive / "Apps",
                    drive / "Applications",
                    drive / "1" / "Game Launchers",
                    drive / "1" / "Games",
                    drive / "1" / "Apps",
                ]
            )

        unique_locations = []

        for location in locations:
            if location in unique_locations:
                continue

            if location.exists() and location.is_dir():
                if not self.is_bad_path(location):
                    unique_locations.append(location)

        return unique_locations
    def scan_common_locations(self):
        found_apps = {}

        locations = self.get_common_scan_locations()

        for location in locations:
            try:
                children = list(location.iterdir())
            except Exception:
                continue

            for child in children:
                try:
                    if not child.is_dir():
                        continue

                    if self.is_bad_path(child):
                        continue

                    app_name = self.normalize_name(
                        child.name
                    )

                    if self.is_bad_app_name(app_name):
                        continue

                    exe_path = self.find_best_exe_in_folder(
                        child,
                        app_name,
                        recursive_depth=1
                    )

                    if not exe_path:
                        continue

                    score = self.score_exe(
                        Path(exe_path),
                        app_name,
                        child
                    )

                    if score < 45:
                        continue

                    found_apps[app_name] = exe_path

                except Exception:
                    continue

        return found_apps
    def merge_apps(
        self,
        base_apps: dict,
        new_apps: dict,
        overwrite: bool
    ):
        for app_name, app_path in new_apps.items():
            if not app_name or not app_path:
                continue

            app_name = self.normalize_name(app_name)

            if self.is_bad_app_name(app_name):
                continue

            if app_name in base_apps and not overwrite:
                continue

            base_apps[app_name] = app_path

        return base_apps

    def remove_dead_paths(self, apps: dict):
        cleaned_apps = {}

        for app_name, app_path in apps.items():
            path = Path(app_path)

            if path.is_absolute():
                if path.exists():
                    cleaned_apps[app_name] = app_path
            else:
                cleaned_apps[app_name] = app_path

        return cleaned_apps
    

    def scan_with_summary(self):
        old_apps = self.load()

        new_apps = self.scan_all()

        added = {}
        removed = {}
        updated = {}

        for app_name, app_path in new_apps.items():
            if app_name not in old_apps:
                added[app_name] = app_path
                continue

            if old_apps[app_name] != app_path:
                updated[app_name] = {
                    "old": old_apps[app_name],
                    "new": app_path
                }

        for app_name, app_path in old_apps.items():
            if app_name not in new_apps:
                removed[app_name] = app_path

        return {
            "total": len(new_apps),
            "added": added,
            "removed": removed,
            "updated": updated,
            "apps": new_apps
        }

    def scan_all(self):
        apps = {}

        common_apps = self.scan_common_locations()
        registry_apps = self.scan_registry()
        start_menu_apps = self.scan_start_menu()
        system_apps = self.scan_system_apps()

        apps = self.merge_apps(
            apps,
            common_apps,
            overwrite=True
        )

        apps = self.merge_apps(
            apps,
            registry_apps,
            overwrite=True
        )

        apps = self.merge_apps(
            apps,
            start_menu_apps,
            overwrite=True
        )

        apps = self.merge_apps(
            apps,
            system_apps,
            overwrite=True
        )

        apps = self.remove_dead_paths(apps)

        self.apps = dict(
            sorted(
                apps.items()
            )
        )

        self.save()

        return self.apps