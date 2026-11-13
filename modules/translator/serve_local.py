#!/usr/bin/env python3
"""Local-only demo of the future endpoint: POST /translate?to=a2a|mcp|email  (binds 127.0.0.1).
Not deployed anywhere. Stores nothing, executes nothing, calls no URL."""
import json, sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from botvow_translate import translate, TranslationError, MAX_BYTES


class H(BaseHTTPRequestHandler):
    def do_POST(self):
        u = urlparse(self.path)
        n = int(self.headers.get("Content-Length", 0))
        if u.path != "/translate": return self._send(404, {"error": "use POST /translate?to=mcp|a2a|email"})
        if n > MAX_BYTES: return self._send(413, {"error": "too large"})
        q = parse_qs(u.query)
        try:
            r = translate(self.rfile.read(n).decode("utf-8"), q.get("to", [""])[0], a2a_version=q.get("a2a_version", ["1.0"])[0])
            r.pop("envelope")
            self._send(200, r)
        except TranslationError as e:
            self._send(400, {"error": str(e)})

    def _send(self, code, obj):
        b = json.dumps(obj, ensure_ascii=False, default=str).encode()
        self.send_response(code); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

    def log_message(self, *a): pass


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8787
    print(f"listening on http://127.0.0.1:{port}/translate (local only)")
    HTTPServer(("127.0.0.1", port), H).serve_forever()
