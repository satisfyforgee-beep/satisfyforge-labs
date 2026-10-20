#!/usr/bin/env python3
"""Private localhost-only, read-only SatisfyForge Trading Lab dashboard.

No order routes. No money movement, API tokens, WebSockets, authentication,
or cloud publication. Bind to 127.0.0.1 ONLY.
"""
from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from urllib.parse import urlsplit

from zerocost_bot.dashboard_model import build_snapshot

ASSETS = Path(__file__).resolve().parent / "dashboard_assets"
ROUTES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/app.js": ("app.js", "application/javascript; charset=utf-8"),
    "/styles.css": ("styles.css", "text/css; charset=utf-8"),
}


def make_handler(report_path=None):
    """Inject explicit path dependency for tests; user requests cannot set paths."""

    class PrivateHandler(BaseHTTPRequestHandler):
        server_version = "SatisfyForgeLocal/0.4"
        sys_version = ""

        def _send(self, status, payload, content_type):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store, max-age=0")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'none'; base-uri 'none'; frame-ancestors 'none'; "
                "script-src 'self'; style-src 'self'; connect-src 'self'; "
                "img-src 'self'; object-src 'none'; form-action 'none'"
            )
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(payload)

        def _host_is_local(self):
            hostname = self.headers.get("Host", "")
            port = self.server.server_address[1]
            return hostname in ("127.0.0.1:" + str(port),
                                "localhost:" + str(port))

        def do_GET(self):
            if not self._host_is_local():
                return self._send(403, b"Forbidden", "text/plain")
            try:
                parsed = urlsplit(self.path)
            except ValueError:
                return self._send(400, b"Invalid URL", "text/plain")
            if parsed.query or parsed.fragment:
                return self._send(400, b"Unexpected query", "text/plain")
            if parsed.path == "/health":
                return self._send(200, b'{"state":"ok","mode":"local_read_only"}',
                                  "application/json")
            if parsed.path == "/api/status":
                view = build_snapshot(report_path)
                payload = json.dumps(view, allow_nan=False, separators=(",", ":"))
                return self._send(200, payload.encode("utf-8"),
                                  "application/json; charset=utf-8")
            route = ROUTES.get(parsed.path)
            if not route:
                return self._send(404, b"Not found", "text/plain")
            filename, mime = route
            try:
                data = (ASSETS / filename).read_bytes()
            except OSError:
                return self._send(503, b"Dashboard asset missing", "text/plain")
            return self._send(200, data, mime)

        def do_HEAD(self):
            return self.do_GET()

        def do_POST(self):
            return self._send(405, b"Read-only service", "text/plain")

        def do_PUT(self):
            return self._send(405, b"Read-only service", "text/plain")

        def do_DELETE(self):
            return self._send(405, b"Read-only service", "text/plain")

        def log_message(self, format, *args):
            # Never print arbitrary request URLs, including accidentally pasted
            # secrets or login codes.
            return

    return PrivateHandler


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Private SatisfyForge dashboard: no trades and no cloud access")
    parser.add_argument("--port", type=int, default=8765,
                        help="local-only port (default 8765)")
    parser.add_argument("--report", default=None,
                        help="optional explicitly supplied market-data JSON report")
    args = parser.parse_args(argv)
    if not 1024 <= args.port <= 65535:
        parser.error("port must be between 1024 and 65535")
    server = ThreadingHTTPServer(("127.0.0.1", args.port),
                                 make_handler(report_path=args.report))
    print("SatisfyForge Trading Lab (READ ONLY)")
    print("Open http://127.0.0.1:{}/ in a browser on THIS computer".format(
        server.server_address[1]))
    print("No trading, passwords, public hosting or brokerage access.")
    try:
        server.serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
