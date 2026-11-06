#!/usr/bin/env python3
"""
serve_probe.py — serve the V1 probe from localhost.

The PayPal JS SDK will not load from a file:// path, so the probe has to be
served. This is a stdlib static server with two properties that matter:

  * it never leaves localhost unless you ask it to (--host 0.0.0.0)
  * it prints the exact URL to open, rather than making you assemble one
"""

from __future__ import annotations

import argparse
import functools
import http.server
import socket
import socketserver
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "probe"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8099)
    ap.add_argument("--host", default="127.0.0.1")
    args = ap.parse_args()

    if not (ROOT / "v1_probe.html").exists():
        print(f"probe not found at {ROOT}/v1_probe.html")
        return 1

    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))

    class Server(socketserver.TCPServer):
        allow_reuse_address = True

    with Server((args.host, args.port), handler) as httpd:
        url = f"http://{'localhost' if args.host == '127.0.0.1' else args.host}:{args.port}/v1_probe.html"
        print("\n  V1 probe served.")
        print(f"  open:  {url}")
        print("  paste your sandbox client id, then press Run V1 probe.")
        print("  ctrl-c to stop.\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n  stopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
