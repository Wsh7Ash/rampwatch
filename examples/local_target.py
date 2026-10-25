#!/usr/bin/env python3
"""Local demo target for rampwatch — a tiny loopback-only HTTP server.

Standard library only:

    python examples/local_target.py --port 8080
    rampwatch run --url http://127.0.0.1:8080/ --max-rps 50

Every request is answered 200 after a short simulated work delay so latency
percentiles are interesting. It binds loopback by default and must never be
exposed to a network.
"""

import argparse
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class Handler(BaseHTTPRequestHandler):
    work_ms = 15

    def do_GET(self):
        if self.path == "/slow":
            time.sleep(0.25)
            status, body = 200, b"slow"
        elif self.path == "/error":
            status, body = 503, b"unavailable"
        else:
            status, body = 200, b"ok"
        time.sleep(self.work_ms / 1000)
        self.send_response(status)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass  # keep the demo output clean


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"local target on http://{args.host}:{args.port}/ — Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
