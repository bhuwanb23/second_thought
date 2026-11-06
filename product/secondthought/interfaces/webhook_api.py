"""
interfaces/webhook_api.py — the two routes that face outward.

`POST /api/webhook` is the only unauthenticated mutating route in the product, so
it is kept in its own file where it can be read in full. It verifies first, and
every attempt — accepted or refused — lands in a log that `/diagnostics` shows.

`GET /diagnostics` is closed by default. If `DIAG_TOKEN` is unset the route
answers 404 rather than 401: an endpoint that does not exist is a smaller target
than one that says "you need a token".
"""

from __future__ import annotations

import hmac
import json
from datetime import datetime

from ..infra.webhook import Rejection, WebhookVerifier


class WebhookAPI:
    def __init__(self, webhook_id: str, *, diag_token: str = "",
                 cert_lookup=None, event_repo=None):
        self.verifier = WebhookVerifier(webhook_id, cert_lookup=cert_lookup)
        self.diag_token = diag_token or ""
        self.event_repo = event_repo

    # -- routes ------------------------------------------------------------
    def route(self, path: str, environ, raw_body: bytes, headers: list,
              service_for):
        """Returns a (body, status, headers) tuple, or None if not our path."""
        if path == "/api/webhook":
            return self._webhook(environ, raw_body, headers, service_for)
        if path == "/diagnostics":
            return self._diagnostics(environ, headers)
        return None

    def _webhook(self, environ, raw_body, headers, service_for):
        provided = {k[5:].replace("_", "-").upper() if k.startswith("HTTP_") else k:
                    v for k, v in environ.items() if k.startswith("HTTP_")}
        try:
            event = self.verifier.verify(provided, raw_body)
        except Rejection as rej:
            # 400, not 500: this is the caller's fault and it is not retryable.
            return ({"received": False, "reason": rej.reason, "detail": rej.detail,
                     "note": "rejection logged and visible at /diagnostics"},
                    "400 Bad Request", headers)
        event_id = event.get("id", "")
        if not isinstance(event_id, str) or not event_id.strip():
            return ({"received": False, "reason": "event has no id",
                     "note": "a webhook without an event id cannot be replay-protected"},
                    "400 Bad Request", headers)
        claimed = bool(self.event_repo and self.event_repo.claim(
            event_id, event.get("event_type", ""), datetime.now().replace(microsecond=0)))
        if self.event_repo and not claimed:
            return ({"received": True, "event_type": event.get("event_type"),
                     "event_id": event_id, "applied": False,
                     "note": "idempotent — a repeat changes nothing"},
                    "200 OK", headers)
        try:
            outcome = self.apply(event, service_for)
        except Exception:
            if self.event_repo:
                self.event_repo.release(event_id)
            raise
        if (event.get("event_type") == "INVOICING.INVOICE.PAID"
                and not outcome.get("applied")):
            if self.event_repo:
                self.event_repo.release(event_id)
            return ({"received": False, "event_type": event.get("event_type"),
                     "event_id": event_id, **outcome,
                     "note": "reservation is not ready; PayPal should retry"},
                    "503 Service Unavailable", headers)
        return ({"received": True, "event_type": event.get("event_type"),
                 "event_id": event.get("id"), **outcome}, "200 OK", headers)

    def apply(self, event: dict, service_for) -> dict:
        """A verified event still has to be one we know what to do with."""
        kind = event.get("event_type", "")
        resource = event.get("resource") or {}
        if kind == "INVOICING.INVOICE.PAID":
            invoice_id = resource.get("id") or (resource.get("invoice") or {}).get("id")
            if not invoice_id:
                return {"applied": False, "reason": "no invoice id in the event"}
            svc = service_for()
            reservation = svc.mark_paid(invoice_id, event.get("id", ""))
            return {"applied": reservation is not None,
                    "invoice_id": invoice_id,
                    "note": "idempotent — a repeat changes nothing"}
        if kind.startswith("PAYMENT.CAPTURE"):
            return {"applied": False,
                    "reason": f"{kind} does not move a reservation"}
        return {"applied": False, "reason": f"unhandled event type: {kind or 'none'}"}

    def _diagnostics(self, environ, headers):
        """
        Counts are public; detail is not.

        V6.4 asks for a refused webhook to be *visible*, and a visitor who cannot
        see the counter has to take my word for it. So the totals are readable by
        anyone and the last five events — which carry transmission ids and event
        types — need the token. If no token is configured the route does not exist.
        """
        if not self.diag_token:
            return ({"error": "not found"}, "404 Not Found", headers)
        summary = self.verifier.summary()
        public = {"received": summary["received"], "rejected": summary["rejected"],
                  "accepted": summary["accepted"]}
        supplied = environ.get("HTTP_X_DIAG_TOKEN") or ""
        if not hmac.compare_digest(supplied, self.diag_token):
            return ({"webhooks": public, "detail": "send X-Diag-Token for recent events"},
                    "200 OK", headers)
        return ({"webhooks": summary, "detail": "full"}, "200 OK", headers)
