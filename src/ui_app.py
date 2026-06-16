from __future__ import annotations

import sys
from pathlib import Path

import webview

from jarvis.desktop.webview_bridge import WebviewBridge


ROOT_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIST = ROOT_DIR / "frontend" / "dist"
INDEX_HTML = FRONTEND_DIST / "index.html"


def main() -> None:
    if not INDEX_HTML.exists():
        print("Frontend build not found.")
        print(f"Missing file: {INDEX_HTML}")
        print()
        print("Run these commands first:")
        print("cd frontend")
        print("npm run build")
        sys.exit(1)

    bridge = WebviewBridge()

    window = webview.create_window(
        title="Jarvis",
        url=INDEX_HTML.as_uri(),
        js_api=bridge,
        width=1280,
        height=800,
        min_size=(960, 640),
        frameless=False,
        easy_drag=False,
    )

    try:
        webview.start(debug=True)
    finally:
        bridge.shutdown()


if __name__ == "__main__":
    main()