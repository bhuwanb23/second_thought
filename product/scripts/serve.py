#!/usr/bin/env python3
"""
scripts/serve.py — run the app locally, the way Render will.

    python3 scripts/serve.py                 # 0.0.0.0:8000
    PORT=8099 python3 scripts/serve.py --pidfile /tmp/st.pid

Binds 0.0.0.0 because a preview proxy is not on this machine. Writes a PID file
so the process can be stopped by PID rather than by `pkill -f`, which has killed
the wrong shell more than once in this project.
"""

from __future__ import annotations

import argparse
import os
import socket
import sys
from pathlib import Path
from wsgiref.simple_server import WSGIRequestHandler, make_server

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from secondthought.config import load          # noqa: E402
from secondthought.interfaces.http import App  # noqa: E402


class Quiet(WSGIRequestHandler):
    def log_message(self, fmt, *args):
        if os.environ.get("ST_ACCESS_LOG"):
            sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=int(os.environ.get("PORT", 8000)))
    ap.add_argument("--pidfile", default="")
    args = ap.parse_args()

    settings = load()
    app = App(settings)
    if args.pidfile:
        Path(args.pidfile).write_text(str(os.getpid()))

    try:
        httpd = make_server("0.0.0.0", args.port, app, handler_class=Quiet)
    except OSError as exc:
        print(f"cannot bind {args.port}: {exc}", file=sys.stderr)
        return 1
    print(f"Second Thought on http://0.0.0.0:{httpd.server_port}  "
          f"(boot {app.boot}, sessions in memory: {app.sessions.count})", flush=True)
    from secondthought.interfaces.badge import badges
    print("badges: " + ", ".join(b["label"] for b in badges(settings)), flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        return 0
    finally:
        if args.pidfile:
            Path(args.pidfile).unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
