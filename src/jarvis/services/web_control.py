import json
import subprocess
import webbrowser
from pathlib import Path
from urllib.parse import quote_plus, urlparse

from jarvis.services.app_discovery import AppDiscovery
from jarvis.services.app_resolver import AppResolver


WEB_SHORTCUTS_FILE = Path(
    "data/web_shortcuts.json"
)


DEFAULT_SHORTCUTS = {
    "google": "https://www.google.com",
    "youtube": "https://www.youtube.com",
    "github": "https://github.com",
    "gmail": "https://mail.google.com",
    "chatgpt": "https://chatgpt.com"
}


SEARCH_ENGINES = {
    "google": "https://www.google.com/search?q={query}",
    "youtube": "https://www.youtube.com/results?search_query={query}",
    "bing": "https://www.bing.com/search?q={query}",
    "duckduckgo": "https://duckduckgo.com/?q={query}"
}


BROWSER_COMMANDS = {
    "edge": [
        "msedge.exe",
        "msedge"
    ],
    "microsoft edge": [
        "msedge.exe",
        "msedge"
    ],
    "chrome": [
        "chrome.exe",
        "chrome"
    ],
    "google chrome": [
        "chrome.exe",
        "chrome"
    ],
    "brave": [
        "brave.exe",
        "brave"
    ],
    "firefox": [
        "firefox.exe",
        "firefox"
    ],
    "comet": [
        "comet.exe",
        "comet"
    ]
}


class WebControl:

    def ensure_shortcuts_file(self):
        WEB_SHORTCUTS_FILE.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        if not WEB_SHORTCUTS_FILE.exists():
            with open(
                WEB_SHORTCUTS_FILE,
                "w",
                encoding="utf-8"
            ) as f:
                json.dump(
                    DEFAULT_SHORTCUTS,
                    f,
                    indent=4
                )

    def load_shortcuts(self) -> dict:
        self.ensure_shortcuts_file()

        try:
            with open(
                WEB_SHORTCUTS_FILE,
                "r",
                encoding="utf-8"
            ) as f:
                data = json.load(f)

            if isinstance(data, dict):
                return {
                    str(key).lower().strip(): str(value).strip()
                    for key, value in data.items()
                    if str(key).strip() and str(value).strip()
                }

        except Exception:
            pass

        return DEFAULT_SHORTCUTS.copy()

    def shortcut_exists(
        self,
        name: str
    ) -> bool:
        shortcuts = self.load_shortcuts()
        shortcut_name = name.lower().strip()

        return shortcut_name in shortcuts

    def normalize_url(
        self,
        url: str
    ) -> str:
        url = str(url).strip()

        if not url:
            return ""

        if url.startswith("www."):
            return f"https://{url}"

        parsed = urlparse(
            url
        )

        if parsed.scheme:
            return url

        return f"https://{url}"

    def looks_like_url(
        self,
        text: str
    ) -> bool:
        text = text.lower().strip()

        if text.startswith(
            (
                "http://",
                "https://",
                "www."
            )
        ):
            return True

        if "." in text and " " not in text:
            return True

        return False

    def format_label(
        self,
        label: str
    ) -> str:
        label = str(label).strip()

        special_names = {
            "x": "X",
            "chatgpt": "ChatGPT",
            "youtube": "YouTube",
            "github": "GitHub",
            "gitlab": "GitLab",
            "gmail": "Gmail",
            "devto": "DEV.to",
            "pypi": "PyPI",
            "npm": "NPM",
            "mdn": "MDN",
            "aws": "AWS",
            "azure": "Azure",
            "cnn": "CNN",
            "bbc": "BBC",
            "wsj": "WSJ",
            "npr": "NPR",
            "cnbc": "CNBC",
            "nba": "NBA",
            "nfl": "NFL",
            "mlb": "MLB",
            "nhl": "NHL",
            "fifa": "FIFA",
            "uefa": "UEFA",
            "imdb": "IMDb",
            "openai": "OpenAI",
            "leetcode": "LeetCode",
            "codeforces": "Codeforces",
            "freecodecamp": "freeCodeCamp",
            "duckduckgo": "DuckDuckGo",
            "stackoverflow": "Stack Overflow",
            "stackexchange": "Stack Exchange",
            "formula 1": "Formula 1",
            "google cloud": "Google Cloud",
            "google drive": "Google Drive",
            "google meet": "Google Meet",
            "google gemini": "Google Gemini",
            "microsoft copilot": "Microsoft Copilot",
            "microsoft teams": "Microsoft Teams",
            "prime video": "Prime Video",
            "epic games": "Epic Games",
            "pika network": "Pika Network",
            "khan academy": "Khan Academy",
            "mit opencourseware": "MIT OpenCourseWare",
            "yahoo finance": "Yahoo Finance",
            "proton mail": "Proton Mail",
            "icloud": "iCloud",
            "onedrive": "OneDrive",
            "cloudflare": "Cloudflare",
            "firebase": "Firebase",
            "mongodb": "MongoDB",
            "postgresql": "PostgreSQL",
            "mysql": "MySQL"
        }

        lowered = label.lower()

        if lowered in special_names:
            return special_names[lowered]

        return label.title()

    def try_open_with_command(
        self,
        url: str,
        browser: str
    ) -> bool:
        browser = browser.lower().strip()

        commands = BROWSER_COMMANDS.get(
            browser,
            []
        )

        for command in commands:
            try:
                subprocess.Popen(
                    [
                        command,
                        url
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL
                )

                return True

            except Exception:
                continue

        return False

    def try_open_with_discovered_browser(
        self,
        url: str,
        browser: str
    ) -> bool:
        try:
            resolver = AppResolver()

            resolved_browser = resolver.resolve(
                browser
            )

            discovery = AppDiscovery()
            apps = discovery.load()

            if not apps:
                apps = discovery.scan_all()

            possible_names = [
                resolved_browser,
                browser.lower().strip(),
                "microsoft edge" if browser.lower().strip() == "edge" else "",
                "google chrome" if browser.lower().strip() == "chrome" else ""
            ]

            possible_names = [
                name
                for name in possible_names
                if name
            ]

            for name in possible_names:
                if name not in apps:
                    continue

                browser_path = Path(
                    apps[name]
                )

                if (
                    browser_path.is_absolute()
                    and browser_path.exists()
                    and browser_path.suffix.lower() == ".exe"
                ):
                    subprocess.Popen(
                        [
                            str(browser_path),
                            url
                        ],
                        cwd=str(browser_path.parent),
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        stdin=subprocess.DEVNULL
                    )

                    return True

        except Exception:
            pass

        return False

    def open_url(
        self,
        url: str,
        browser: str | None = None,
        label: str | None = None
    ) -> str:
        normalized_url = self.normalize_url(
            url
        )

        if not normalized_url:
            return "No URL was provided."

        if browser:
            opened = self.try_open_with_command(
                normalized_url,
                browser
            )

            if not opened:
                opened = self.try_open_with_discovered_browser(
                    normalized_url,
                    browser
                )

            if opened:
                shown_label = label or normalized_url

                return (
                    f"Opening {shown_label} "
                    f"in {self.format_label(browser)}."
                )

        try:
            webbrowser.open(
                normalized_url,
                new=2
            )

            shown_label = label or normalized_url

            return f"Opening {shown_label}."

        except Exception as e:
            return f"Failed to open website: {e}"

    def open_shortcut(
        self,
        name: str,
        browser: str | None = None
    ) -> str:
        shortcuts = self.load_shortcuts()
        shortcut_name = name.lower().strip()

        if shortcut_name not in shortcuts:
            return f"Unknown web shortcut: {name}"

        url = shortcuts[shortcut_name]

        label = self.format_label(
            shortcut_name
        )

        return self.open_url(
            url=url,
            browser=browser,
            label=label
        )

    def search(
        self,
        engine: str,
        query: str,
        browser: str | None = None
    ) -> str:
        engine = engine.lower().strip()
        query = str(query).strip()

        if not query:
            return "No search query was provided."

        if engine not in SEARCH_ENGINES:
            return f"Unknown search engine: {engine}"

        encoded_query = quote_plus(
            query
        )

        search_url = SEARCH_ENGINES[engine].format(
            query=encoded_query
        )

        result = self.open_url(
            url=search_url,
            browser=browser,
            label=f"{self.format_label(engine)} search"
        )

        if result.startswith("Opening"):
            return (
                f"Searching {self.format_label(engine)} "
                f"for {query}."
            )

        return result