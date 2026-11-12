"""
server.py — HTTP transport for the demo.

Stdlib only. Serves one page and a JSON API.

    python3 server.py            # http://0.0.0.0:8000

Two endpoints are deliberately different:

  /healthz      public, minimal. Two booleans a judge can check in one request.
  /diagnostics  operator only, gated by DIAG_TOKEN, returns 404 without it.
                Internal detail never appears on the public endpoint.
"""

from __future__ import annotations

import hmac
import json
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import paylater
from api import (  # noqa: F401  (re-exported: tests and demo.py use server.*)
    CLIENT, DEFAULT, ELIGIBILITY, EXPLAINER, LEDGER, MODEL, PROFILES, SESSIONS,
    _money_action, _persona, approve, build_payload, do_agent, do_extract, execute,
)
from llm import describe
from personas import TODAY
from session import COOKIE as SESSION_COOKIE
from session import GLOBAL_RATE_LIMIT, IP_RATE_LIMIT, RATE_LIMIT

HERE = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.join(HERE, "web")

# --------------------------------------------------------------------------
class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        if args and "/api/" in str(args[0]):
            return
        super().log_message(fmt, *args)

    def _send(self, code, body: bytes, ctype="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        if getattr(self, "_new_session", False) and getattr(self, "_session", None):
            self.send_header("Set-Cookie",
                             f"{SESSION_COOKIE}={self._session.sid}; Path=/; "
                             f"SameSite=Lax; HttpOnly")
        self.end_headers()
        self.wfile.write(body)

    def _bind_session(self):
        """Every request gets its own disposable state, keyed by a cookie."""
        raw = self.headers.get("Cookie") or ""
        sid = None
        for part in raw.split(";"):
            k, _, v = part.strip().partition("=")
            if k == SESSION_COOKIE and v:
                sid = v
                break
        self._session, self._new_session = SESSIONS.get(sid)
        return self._session

    def _json(self, obj, code=200):
        self._send(code, json.dumps(obj, default=str).encode())

    def _read_json(self):
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n) if n else b"{}"
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    # -- GET ----------------------------------------------------------
    def do_GET(self):
        self._bind_session()
        parsed = urlparse(self.path)
        path = parsed.path

        if path in ("/", "/index.html"):
            p = os.path.join(WEB, "index.html")
            if not os.path.exists(p):
                return self._send(500, b"index.html missing", "text/plain")
            with open(p, "rb") as f:
                return self._send(200, f.read(), "text/html; charset=utf-8")

        if path == "/healthz":
            # Public and unauthenticated: booleans only. Both values are already
            # visible on the page badge, so this leaks nothing new. No session
            # counts, no config, no internal flags.
            ai = describe(MODEL)["engine"]
            return self._json({
                "ok": True,
                "paypal_live": CLIENT.mode == "live",
                "ai_live": ai == "llm",
            })

        if path == "/diagnostics":
            # Operator only. A missing or wrong token returns 404, not 401, so the
            # endpoint does not advertise that it exists.
            token = (parse_qs(parsed.query).get("token") or [""])[0]
            expected = os.environ.get("DIAG_TOKEN") or ""
            if not expected or not hmac.compare_digest(token, expected):
                return self._send(404, b'{"error":"not found"}')
            from agentic import approval_secret_source
            return self._json({
                "ok": True,
                "paypal": CLIENT.mode,
                "ai": describe(MODEL)["engine"],
                "approval_secret": approval_secret_source(),
                "diag_token": "env",
                "sessions": SESSIONS.count,
                "limits": {"per_session": RATE_LIMIT, "per_ip": IP_RATE_LIMIT,
                           "global_daily": GLOBAL_RATE_LIMIT},
            })

        if path == "/api/personas":
            return self._json({"personas": [{"key": k, "label": v[1], "amount": v[2]}
                                            for k, v in PERSONAS.items()],
                               "mode": CLIENT.mode, "ai": describe(MODEL)})

        if path == "/api/decide":
            q = parse_qs(parsed.query)
            persona = (q.get("persona") or ["maya"])[0]
            amount = None
            if "amount" in q:
                try:
                    amount = int(round(float(q["amount"][0]) * 100))
                except ValueError:
                    return self._json({"error": "amount must be a number"}, 400)
            try:
                return self._json(build_payload(persona, amount, session=self._session))
            except Exception as e:                              # noqa: BLE001
                return self._json({"error": str(e)}, 400)

        if path == "/api/profile":
            q = parse_qs(parsed.query)
            key = (q.get("persona") or ["maya"])[0]
            prof = self._session.profiles.get(key)
            if not prof:
                return self._json({"profile": None,
                                   "hint": "POST text to set one up once"})
            return self._json({"profile": prof.summary(), "entries": prof.to_dict(),
                               "ai": describe(MODEL)})

        if path == "/api/ledger":
            q = parse_qs(parsed.query)
            persona = (q.get("persona") or ["maya"])[0]
            return self._json({"exposure": self._session.ledger.exposure(persona, TODAY),
                               "entries": [e.__dict__ for e in self._session.ledger.entries]})

        self._send(404, b'{"error":"not found"}')

    # -- POST ---------------------------------------------------------
    def do_POST(self):
        self._bind_session()
        path = urlparse(self.path).path
        body = self._read_json()
        if body is None:
            return self._json({"error": "bad json"}, 400)

        if path == "/api/decide":
            return self._json(build_payload(body.get("persona", "maya"),
                                            body.get("amount"), session=self._session))

        if path in ("/api/extract", "/api/agent", "/api/profile"):
            ip = (self.headers.get("X-Forwarded-For") or "").split(",")[0].strip() \
                 or self.client_address[0]
            allowed, why = SESSIONS.allow_llm(self._session, ip, time.time())
            if not allowed:
                return self._json({"error": "rate limit", "reason": why,
                                   "message": ("This demo caps LLM-backed calls. The persona "
                                               "buttons never call a model and always work.")}, 429)

        if path == "/api/extract":
            text = str(body.get("text") or "")
            if not text.strip():
                return self._json({"error": "no text"}, 400)
            return self._json(do_extract(text, body.get("persona", "maya"),
                                         session=self._session))

        if path == "/api/profile":
            key = body.get("persona", "maya")
            text = str(body.get("text") or "").strip()
            if not text:
                return self._json({"error": "no text"}, 400)
            _k, cal, _l, _a = _persona(key)
            result = extract(text, cal.today, MODEL)
            if not result.obligations:
                return self._json({"error": "could not read any amounts",
                                   "extraction": result.to_dict()}, 400)
            prof = from_extraction(result, key,
                                   int(body.get("opening_balance") or cal.opening_balance),
                                   cal.today)
            self._session.profiles.put(prof)  # this visitor only
            return self._json({"profile": prof.summary(), "entries": prof.to_dict(),
                               "extraction": result.to_dict(), "ai": describe(MODEL),
                               "rerun": "the next decision uses this profile"})

        if path == "/api/agent":
            return self._json(do_agent(body.get("persona", "maya"),
                                       body.get("amount"), session=self._session))

        if path == "/api/paylater":
            amount = int(body.get("amount") or 0)
            elig = paylater.parse_sdk_result(body.get("sdk") or {}, amount)
            self._session.eligibility.put(body.get("persona", "maya"), elig)
            return self._json({"stored": elig.to_dict()})

        if path == "/api/approve":
            payload = build_payload(body.get("persona", "maya"), body.get("amount"),
                                    session=self._session)
            return self._json(approve(payload))

        if path == "/api/execute":
            payload = build_payload(body.get("persona", "maya"), body.get("amount"),
                                    session=self._session)
            return self._json(execute(payload, body.get("token"), session=self._session))

        if path == "/api/override":
            payload = build_payload(body.get("persona", "maya"), body.get("amount"),
                                    session=self._session)
            self._session.ledger.record(payload["persona"], payload["decision"]["amount"],
                          payload["decision"]["currency"], "invoice", override=True,
                          override_reason=body.get("reason", "shopper chose to proceed"),
                          today=date.fromisoformat(payload["today"]))
            return self._json({"ok": True,
                               "message": "Override recorded. Nothing was blocked."})

        if path == "/api/profile/delete":
            return self._json({"deleted": self._session.profiles.delete(body.get("persona", "maya"))})

        if path == "/api/reset":
            self._session.reset()
            return self._json({"ok": True, "message": "this session was reset; personas were never touched"})

        self._send(404, b'{"error":"not found"}')


def main(port: int = 8000):
    ai = describe(MODEL)
    print(f"Second Thought — PayPal: {CLIENT.mode.upper()} · AI: {ai['engine'].upper()}"
          f" ({ai['model']})")
    print(f"  http://0.0.0.0:{port}")
    if ai["engine"] == "llm-mock":
        print("  no LLM_API_KEY set — the agent runs a scripted model on the same code path")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()


if __name__ == "__main__":
    import sys
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 8000)
