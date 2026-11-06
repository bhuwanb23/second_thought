"""
interfaces/http.py — the same use cases over WSGI, with a box per visitor.

Stdlib only, because the point of this file is not a framework. The routing is
deliberately boring so that the security properties are visible in one screen:

  * `/healthz` returns booleans and status words. No paths, no keys, no versions.
  * A visitor's profile is written into their session and nowhere else.
  * `/api/execute` refuses an unknown tool outright, before any token is looked
    at, and then refuses a token that does not match these exact arguments.
  * Model-backed routes are rate limited by session *and* by IP.

Every money-moving route is read-only until a token from a real proposal arrives.
"""

from __future__ import annotations

import hmac
import json
import time
from datetime import date, datetime
from urllib.parse import parse_qs

from ..app.approvals import ApprovalError, ApprovalGate
from ..app.checkout import Checkout, CheckoutService
from ..app.ports import GatewayError
from ..domain import InvalidRequest, Policy
from ..domain.engine import decide
from ..infra.db import Database, LedgerRepo, ProfileRepo, ReservationRepo, WebhookRepo
from ..infra.gateway import SimulatedGateway
from ..infra.paypal_live import PayPalLiveGateway
from .badge import badges, health_payload
from .plumbing import cookie, ip, json_body, raw_body
from .screens import explain, render_page
from .session import SessionStore
from .webhook_api import WebhookAPI

COOKIE = "st_sid"
# The two actions that can move money. Anything else is refused, not mapped.
MONEY_TOOLS = ("create_reservation", "authorise_hold")

PERSONAS = {
    "ada": {"label": "Ada — comfortable month", "amount_minor": 24_900,
            "profile": {"opening_balance": 210_000,
                        "paydays": [{"due": "2026-11-05", "amount_minor": 200_000},
                                    {"due": "2026-11-19", "amount_minor": 200_000},
                                    {"due": "2026-12-03", "amount_minor": 200_000}],
                        "obligations": [{"label": "rent", "due": "2026-11-28",
                                         "amount_minor": 145_000, "essential": True}]}},
    "ben": {"label": "Ben — payday is in five days", "amount_minor": 24_900,
            "profile": {"opening_balance": 30_000,
                        "paydays": [{"due": "2026-11-07", "amount_minor": 260_000}],
                        "obligations": [{"label": "car loan", "due": "2026-11-20",
                                         "amount_minor": 31_200, "essential": True},
                                        {"label": "rent", "due": "2026-11-28",
                                         "amount_minor": 145_000, "essential": True}]}},
    "cleo": {"label": "Cleo — genuinely squeezed", "amount_minor": 24_900,
             "profile": {"opening_balance": 45_000,
                         "paydays": [{"due": "2026-11-05", "amount_minor": 110_000}],
                         "obligations": [{"label": "rent", "due": "2026-11-25",
                                          "amount_minor": 130_000, "essential": True}]}},
}
# V5 asks after "Maya": the prototype's name for the DEFER persona. Same shape as ben.
PERSONA_ALIASES = {"maya": "ben"}


class ScopedProfiles:
    """`profiles.get(id)` for one visitor: their own box first, defaults never written."""

    def __init__(self, session, defaults):
        self.session = session
        self.defaults = defaults

    def get(self, shopper_id):
        if shopper_id == "me":
            return self.session.profile
        return self.defaults.get(shopper_id)

    def save(self, shopper_id, payload, _now):
        if shopper_id != "me":
            raise InvalidRequest("only your own profile can be written")
        self.session.profile = payload


def _http_date() -> str:
    return time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())


class App:
    """WSGI callable. `App()(environ, start_response)`."""

    def __init__(self, settings, *, sessions=None, gateway=None, clock=None,
                 cert_lookup=None):
        self.settings = settings
        self.clock = clock or time.time
        self.sessions = sessions or SessionStore(
            (settings.approval_secret or "dev-only-change-me").encode())
        self.gateway = gateway or self._gateway_for(settings)
        self.db = Database(settings.db_path)
        self.defaults = ProfileRepo(self.db)          # read-only persona store
        self.reservations = ReservationRepo(self.db)
        self.ledger = LedgerRepo(self.db)
        self.webhook_events = WebhookRepo(self.db)
        self.boot = self.sessions.boot
        self.attempts: list = []                      # refused money calls, for tests
        self.webhooks = WebhookAPI(settings.paypal.webhook_id,
                                   diag_token=settings.diag_token,
                                   cert_lookup=cert_lookup,
                                   event_repo=self.webhook_events)
        for key, persona in PERSONAS.items():
            self.defaults.save(key, persona["profile"], datetime(2026, 11, 1, 9, 0))

    @staticmethod
    def _gateway_for(settings):
        """Use the sandbox adapter only when sandbox credentials are configured."""
        if settings.paypal.configured:
            return PayPalLiveGateway(settings.paypal)
        return SimulatedGateway()

    # -- the service, rebuilt per request so nothing can be shared by accident
    def service(self, session) -> CheckoutService:
        return CheckoutService(gateway=self.gateway,
                               profiles=ScopedProfiles(session, self.defaults),
                               reservations=self.reservations, ledger=self.ledger,
                               approvals=session.approvals, policy=Policy())

    def close(self) -> None:
        self.db.close()

    # -- WSGI --------------------------------------------------------------
    def __call__(self, environ, start_response):
        try:
            body, status, headers = self._handle(environ)
        except Exception as exc:                        # noqa: BLE001
            body, status, headers = ({"error": "internal error",
                                      "detail": type(exc).__name__}, "500 Internal Server Error",
                                     [])
        payload = (json.dumps(body, default=str) if isinstance(body, (dict, list))
                   else str(body)).encode()
        ctype = "application/json" if isinstance(body, (dict, list)) else "text/html; charset=utf-8"
        head = [("Content-Type", ctype),
                ("Content-Length", str(len(payload))),
                ("Cache-Control", "no-store"),
                ("X-Content-Type-Options", "nosniff")] + headers
        start_response(status, head)
        return [payload]

    def _handle(self, environ):
        method = environ.get("REQUEST_METHOD", "GET").upper()
        path = environ.get("PATH_INFO", "/")
        query = parse_qs(environ.get("QUERY_STRING", ""))
        raw_cookie = cookie(environ, COOKIE)
        session = self.sessions.read_cookie(raw_cookie)
        new_cookie = None
        if session is None:
            session = self.sessions.new()
            new_cookie = self.sessions.issue_cookie(session)
        cookie_flags = "Path=/; HttpOnly; SameSite=Lax"
        if self.settings.env == "production":
            cookie_flags += "; Secure"
        headers = [("Set-Cookie", f"{COOKIE}={new_cookie}; {cookie_flags}")] \
            if new_cookie else [("Set-Cookie", "")]
        headers = [h for h in headers if h[1]]

        if path in ("/api/webhook", "/diagnostics"):
            routed = self.webhooks.route(
                path, environ, raw_body(environ), headers,
                lambda: self.service(session))
            if routed is not None:
                return routed
        if path == "/":
            return render_page(self.settings, PERSONAS), "200 OK", headers
        if path == "/healthz":
            return health_payload(self.settings), "200 OK", headers
        if path == "/api/session":
            return {"session": session.public, "boot": self.boot,
                    "badges": badges(self.settings)}, "200 OK", headers
        if path == "/api/personas":
            return {"personas": [{"id": k, "label": v["label"],
                                  "amount_minor": v["amount_minor"]}
                                 for k, v in PERSONAS.items()]}, "200 OK", headers
        if path == "/api/quote":
            return self._quote(session, query, headers)
        if path == "/api/profile" and method == "POST":
            return self._save_profile(session, environ, headers)
        if path == "/api/plan" and method == "POST":
            return self._plan(session, environ, headers)
        if path == "/api/execute" and method == "POST":
            return self._execute(session, environ, headers)
        if path == "/api/extract" and method == "POST":
            return self._extract(session, environ, headers)
        return {"error": "not found"}, "404 Not Found", headers

    # -- routes ------------------------------------------------------------
    def _persona(self, key):
        key = PERSONA_ALIASES.get(key, key)
        if key != "me" and key not in PERSONAS:
            return None, None
        return key, PERSONAS.get(key, {})

    def _quote(self, session, query, headers):
        key = (query.get("persona") or ["maya"])[0]
        key, persona = self._persona(key)
        if key is None:
            return {"error": "unknown persona"}, "400 Bad Request", headers
        svc = self.service(session)
        try:
            raw_amount = (query.get("amount_minor") or [persona["amount_minor"]])[0]
            amount = self._amount(raw_amount)
            out = svc.quote(Checkout(key, "Northwind Audio", amount, "USD"), date(2026, 11, 1))
        except InvalidRequest as exc:
            return {"error": str(exc)}, "400 Bad Request", headers
        out["profile"] = "session" if key == "me" and session.profile else (
            "persona-default" if key != "me" else None)
        out["explain"] = explain(out)          # the words a shopper actually reads
        return out, "200 OK", headers

    def _save_profile(self, session, environ, headers):
        body = json_body(environ)
        profile = body.get("profile")
        if not isinstance(profile, dict):
            return {"error": "profile must be an object"}, "400 Bad Request", headers
        allowed, why = self.sessions.allow_profile(session, ip(environ), self.clock())
        if not allowed:
            return {"error": "rate limit", "reason": why}, "429 Too Many Requests", headers
        session.profile = profile
        return {"saved": True, "scope": "this session only",
                "budget": why}, "200 OK", headers

    def _plan(self, session, environ, headers):
        body = json_body(environ)
        key, persona = self._persona(str(body.get("persona", "maya")))
        if key is None:
            return {"error": "unknown persona"}, "400 Bad Request", headers
        svc = self.service(session)
        try:
            raw_amount = body.get("amount_minor")
            if raw_amount is None:
                raw_amount = (persona or {}).get("amount_minor", 24_900)
            amount = self._amount(raw_amount)
            out = svc.propose(Checkout(key, "Northwind Audio", amount, "USD"), date(2026, 11, 1))
        except InvalidRequest as exc:
            return {"error": str(exc)}, "400 Bad Request", headers
        return out, "200 OK", headers

    @staticmethod
    def _amount(value) -> int:
        if isinstance(value, bool):
            raise InvalidRequest("amount_minor must be an integer")
        if isinstance(value, float):
            raise InvalidRequest("amount_minor must be an integer")
        try:
            amount = int(value)
        except (TypeError, ValueError):
            raise InvalidRequest("amount_minor must be an integer") from None
        if amount <= 0 or amount > 100_000_000:
            raise InvalidRequest("amount_minor is outside the supported range")
        return amount

    def _execute(self, session, environ, headers):
        body = json_body(environ)
        tool = str(body.get("tool") or "")
        args = body.get("args") if isinstance(body.get("args"), dict) else {}
        token = body.get("token")
        # (1) an unrecognised money tool is refused before anything else.
        if tool not in MONEY_TOOLS:
            self.attempts.append({"tool": tool, "reason": "unknown tool",
                                  "session": session.id[:8]})
            return ({"error": "unknown tool", "accepted": list(MONEY_TOOLS),
                     "note": "a money tool not in the list is not mapped onto one"},
                    "400 Bad Request", headers)
        # (2) no token, a stale token, another session's token, or altered args.
        if not token:
            self.attempts.append({"tool": tool, "reason": "no token",
                                  "session": session.id[:8]})
            return ({"error": "approval required",
                     "note": "propose first, then approve those exact arguments"},
                    "403 Forbidden", headers)
        svc = self.service(session)
        try:
            done = svc.execute(tool, args, token)
        except ApprovalError as exc:
            self.attempts.append({"tool": tool, "reason": str(exc),
                                  "session": session.id[:8]})
            return {"error": "approval refused", "reason": str(exc)}, "403 Forbidden", headers
        except GatewayError as exc:
            return {"error": "gateway refused", "reason": str(exc)}, "502 Bad Gateway", headers
        return done, "200 OK", headers

    def _extract(self, session, environ, headers):
        allowed, why = self.sessions.allow_llm(session, ip(environ), self.clock())
        if not allowed:
            return {"error": "rate limit", "reason": why,
                    "message": ("Model-backed calls are capped. The persona buttons never "
                                "call a model and always work.")}, "429 Too Many Requests", headers
        body = json_body(environ)
        from ..ai.agent import Agent
        from ..ai.extract import LLMExtractor
        llm = LLMExtractor(self.settings.llm) if self.settings.llm.configured else None
        agent = Agent(self.service(session), llm=llm)
        ext = agent.extract(str(body.get("text") or ""), date(2026, 11, 1))
        return {"extraction": ext.to_dict(), "budget": self.sessions.per_session
                - len(session.llm_calls)}, "200 OK", headers
