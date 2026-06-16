from __future__ import annotations

import http.server
import json
import socket
import socketserver
import sys
import threading
import time
import webbrowser
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

import webview

from jarvis.desktop.webview_bridge import WebviewBridge


ROOT_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIST = ROOT_DIR / "frontend" / "dist"
INDEX_HTML = FRONTEND_DIST / "index.html"

AUTH_RESULT_LOCK = threading.Lock()
AUTH_RESULT: dict = {
    "pending": False,
    "completed": False,
    "payload": None,
    "created_at": 0,
}


class JarvisStaticHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            directory=str(FRONTEND_DIST),
            **kwargs,
        )

    def log_message(self, format, *args):
        return

    def _send_json(self, data: dict, status: int = 200) -> None:
        body = json.dumps(data).encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html: str, status: int = 200) -> None:
        body = html.encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        requested_path = unquote(self.path.split("?", 1)[0])

        if requested_path == "/jarvis-auth/complete":
            length = int(self.headers.get("Content-Length", "0") or "0")
            raw = self.rfile.read(length).decode("utf-8") if length else "{}"

            try:
                payload = json.loads(raw)
            except Exception:
                payload = {}

            with AUTH_RESULT_LOCK:
                AUTH_RESULT["pending"] = False
                AUTH_RESULT["completed"] = True
                AUTH_RESULT["payload"] = payload
                AUTH_RESULT["created_at"] = time.time()

            self._send_json({"ok": True, "message": "Jarvis received Google login."})
            return

        self._send_json({"ok": False, "message": "Unknown endpoint."}, status=404)

    def do_GET(self):
        parsed = urlparse(self.path)
        requested_path = unquote(parsed.path)

        if requested_path == "/jarvis-auth/status":
            with AUTH_RESULT_LOCK:
                data = {
                    "ok": True,
                    "pending": bool(AUTH_RESULT["pending"]),
                    "completed": bool(AUTH_RESULT["completed"]),
                    "payload": AUTH_RESULT["payload"] if AUTH_RESULT["completed"] else None,
                }

                if AUTH_RESULT["completed"]:
                    AUTH_RESULT["completed"] = False
                    AUTH_RESULT["payload"] = None

            self._send_json(data)
            return

        if requested_path == "/jarvis-auth/success":
            self._send_html(
                """
                <!doctype html>
                <html>
                  <head>
                    <title>Jarvis Google Login</title>
                    <style>
                      body {
                        margin: 0;
                        min-height: 100vh;
                        display: grid;
                        place-items: center;
                        background: #05070d;
                        color: #e6fbff;
                        font-family: system-ui, -apple-system, Segoe UI, sans-serif;
                      }
                      .card {
                        max-width: 520px;
                        border: 1px solid rgba(255,255,255,.12);
                        border-radius: 24px;
                        padding: 32px;
                        background: rgba(255,255,255,.05);
                        box-shadow: 0 20px 80px rgba(0,0,0,.45);
                        text-align: center;
                      }
                      h1 { margin: 0 0 12px; }
                      p { color: #9fb3c8; line-height: 1.6; }
                    </style>
                  </head>
                  <body>
                    <div class="card">
                      <h1>Google sign-in complete</h1>
                      <p>You can return to the Jarvis desktop app now. This browser tab can be closed.</p>
                    </div>
                  </body>
                </html>
                """
            )
            return

        if requested_path in ("", "/"):
            self.path = "/index.html"
            return super().do_GET()

        file_path = FRONTEND_DIST / requested_path.lstrip("/")

        if file_path.exists() and file_path.is_file():
            return super().do_GET()

        self.path = "/index.html"
        return super().do_GET()


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


class JarvisJsApi:
    __slots__ = ("_bridge", "_frontend_url")

    def __init__(self, bridge: WebviewBridge, frontend_url: str) -> None:
        self._bridge = bridge
        self._frontend_url = frontend_url.rstrip("/") + "/"

    def handle_command(self, command: str, payload: dict | None = None):
        if command == "auth.google_browser_start":
            with AUTH_RESULT_LOCK:
                AUTH_RESULT["pending"] = True
                AUTH_RESULT["completed"] = False
                AUTH_RESULT["payload"] = None
                AUTH_RESULT["created_at"] = time.time()

            url = self._frontend_url + "?jarvis_browser_google=1"

            try:
                webbrowser.open(url)
                return {
                    "ok": True,
                    "message": "Google sign-in opened in your browser.",
                    "data": {
                        "reply": "Google sign-in opened in your browser.",
                        "meta": "AUTH / GOOGLE BROWSER OPENED",
                    },
                }
            except Exception as exc:
                return {
                    "ok": False,
                    "message": f"Could not open browser: {exc}",
                    "data": {
                        "reply": f"Could not open browser: {exc}",
                        "meta": "AUTH / GOOGLE BROWSER FAILED",
                    },
                }

        return self._bridge.handle_command(command, payload)


def find_free_port(start_port: int = 8765) -> int:
    for port in range(start_port, start_port + 100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue

    raise RuntimeError("No free localhost port found for Jarvis UI.")


def start_frontend_server() -> tuple[ReusableTCPServer, str]:
    port = find_free_port(8765)

    server = ReusableTCPServer(
        ("127.0.0.1", port),
        JarvisStaticHandler,
    )

    thread = threading.Thread(
        target=server.serve_forever,
        daemon=True,
    )
    thread.start()

    return server, f"http://127.0.0.1:{port}/"


def main() -> None:
    if not INDEX_HTML.exists():
        print("Frontend build not found.")
        print(f"Missing file: {INDEX_HTML}")
        print()
        print("Run these commands first:")
        print("cd frontend")
        print("npm run build")
        sys.exit(1)

    server = None
    bridge = WebviewBridge()

    try:
        server, frontend_url = start_frontend_server()
        api = JarvisJsApi(bridge, frontend_url)

        print(f"Jarvis frontend served at: {frontend_url}")

        webview.create_window(
            title="Jarvis",
            url=frontend_url,
            js_api=api,
            width=1280,
            height=800,
            min_size=(960, 640),
            frameless=False,
            easy_drag=False,
        )

        webview.start(debug=False)

    finally:
        try:
            bridge.shutdown()
        except Exception:
            pass

        if server is not None:
            try:
                server.shutdown()
                server.server_close()
            except Exception:
                pass


if __name__ == "__main__":
    main()
