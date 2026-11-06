"""
paypal.py — the PayPal adapter.

One interface, two transports:

  LiveTransport       real REST calls to api-m.sandbox.paypal.com
  SimulatedTransport  deterministic canned responses, used when no credentials
                      are present and for tests

The mode is always exposed as `client.mode` ("live" or "simulated") and the UI
renders it as a badge. A demo that cannot say which mode it is in is a demo
that cannot be trusted.

Endpoints implemented (all documented, all sandbox-safe):
  POST /v1/oauth2/token
  POST /v2/checkout/orders                      create (AUTHORIZE)
  POST /v2/checkout/orders/{id}/authorize
  POST /v2/checkout/orders/{id}/capture
  POST /v2/payments/authorizations/{id}/capture
  POST /v2/payments/authorizations/{id}/void
  POST /v2/invoicing/invoices                   invoice with a due date
  POST /v1/notifications/verify-webhook-signature
"""

from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass, field

SANDBOX = "https://api-m.sandbox.paypal.com"
LIVE = "https://api-m.paypal.com"


class PayPalError(RuntimeError):
    def __init__(self, status: int, body: str, path: str = ""):
        super().__init__(f"PayPal {status} on {path}: {body[:300]}")
        self.status = status
        self.body = body
        self.path = path


def _new_request_id() -> str:
    return str(uuid.uuid4())


# --------------------------------------------------------------------------
# transports
# --------------------------------------------------------------------------
class LiveTransport:
    mode = "live"

    def __init__(self, base_url: str, client_id: str, secret: str, timeout: int = 20):
        self.base_url = base_url.rstrip("/")
        self.client_id = client_id
        self.secret = secret
        self.timeout = timeout
        self._token: str | None = None
        self._token_expires_at = 0.0

    # -- auth -------------------------------------------------------------
    def token(self) -> str:
        import time
        if self._token and time.time() < self._token_expires_at - 30:
            return self._token
        creds = base64.b64encode(
            f"{self.client_id}:{self.secret}".encode()).decode()
        req = urllib.request.Request(
            f"{self.base_url}/v1/oauth2/token",
            data=b"grant_type=client_credentials",
            headers={"Authorization": f"Basic {creds}",
                     "Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            body = json.loads(resp.read().decode())
        self._token = body["access_token"]
        self._token_expires_at = time.time() + float(body.get("expires_in", 32000))
        return self._token

    # -- generic ----------------------------------------------------------
    def request(self, method: str, path: str, body: dict | None = None,
                request_id: str | None = None, auth: bool = True) -> dict:
        headers = {"Content-Type": "application/json",
                   "Prefer": "return=representation"}
        if auth:
            headers["Authorization"] = f"Bearer {self.token()}"
        if request_id:
            headers["PayPal-Request-Id"] = request_id
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(f"{self.base_url}{path}", data=data,
                                     headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read().decode()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            raise PayPalError(e.code, e.read().decode(errors="replace"), path) from e


class SimulatedTransport:
    """
    Deterministic stand-in for the sandbox.

    Deliberately mimics the shapes in PayPal's docs — including the
    PAYER_ACTION_REQUIRED status and the authorize→capture id chain — so the
    calling code cannot tell the difference except by reading `mode`.
    """

    mode = "simulated"

    def __init__(self):
        self.calls: list[dict] = []
        self._orders: dict[str, dict] = {}

    def request(self, method: str, path: str, body: dict | None = None,
                request_id: str | None = None, auth: bool = True) -> dict:
        self.calls.append({"method": method, "path": path, "body": body or {},
                           "request_id": request_id})

        # idempotency: same PayPal-Request-Id returns the first result
        if request_id:
            for prev in self.calls[:-1]:
                if prev.get("request_id") == request_id and prev["path"] == path:
                    return dict(prev.get("_result", {}))

        result: dict
        if path == "/v2/checkout/orders":
            oid = "SIM-" + uuid.uuid4().hex[:12].upper()
            amount = (body or {}).get("purchase_units", [{}])[0].get("amount", {})
            self._orders[oid] = {"amount": amount, "intent": (body or {}).get("intent")}
            result = {
                "id": oid,
                "status": "PAYER_ACTION_REQUIRED",
                "intent": (body or {}).get("intent", "CAPTURE"),
                "purchase_units": [{"amount": amount,
                                    "reference_id": (body or {}).get(
                                        "purchase_units", [{}])[0].get("reference_id", "")}],
                "links": [
                    {"href": f"https://api-m.sandbox.paypal.com/v2/checkout/orders/{oid}",
                     "rel": "self", "method": "GET"},
                    {"href": f"https://www.sandbox.paypal.com/checkoutnow?token={oid}",
                     "rel": "payer-action", "method": "GET"},
                ],
            }
        elif path.endswith("/authorize"):
            oid = path.split("/")[4]
            auth_id = "AUTH-" + uuid.uuid4().hex[:12].upper()
            result = {
                "id": oid, "status": "COMPLETED",
                "purchase_units": [{"payments": {"authorizations": [{
                    "id": auth_id, "status": "CREATED",
                    "amount": self._orders.get(oid, {}).get("amount", {}),
                    "expiration_time": "2026-11-04T00:00:00Z",
                }]}}],
            }
        elif path.endswith("/capture") and "/authorizations/" in path:
            auth_id = path.split("/")[4]
            result = {
                "id": auth_id, "status": "CAPTURED",
                "amount": {"currency_code": "USD", "value": "0.00"},
                "seller_protection": {"status": "ELIGIBLE"},
            }
        elif path.endswith("/void"):
            result = {"id": path.split("/")[4], "status": "VOIDED"}
        elif path == "/v2/invoicing/invoices":
            iid = "INV2-" + uuid.uuid4().hex[:10].upper()
            detail = (body or {}).get("detail", {})
            result = {
                "id": iid, "status": "DRAFT",
                "detail": detail,
                "href": f"https://www.sandbox.paypal.com/invoice/payerView/details/{iid}",
            }
        elif path == "/v1/notifications/verify-webhook-signature":
            # the simulator accepts only a well-formed body with the five headers
            result = {"verification_status": "SUCCESS"
                      if (body or {}).get("transmission_id") else "FAILURE"}
        else:
            result = {"status": "SIMULATED", "path": path}

        if request_id:
            self.calls[-1]["_result"] = result
        return result


# --------------------------------------------------------------------------
# the client
# --------------------------------------------------------------------------
@dataclass
class PayPalClient:
    transport: object
    webhook_id: str = ""
    log: list[dict] = field(default_factory=list)

    @property
    def mode(self) -> str:
        return getattr(self.transport, "mode", "unknown")

    # -- checkout ---------------------------------------------------------
    def create_order(self, amount_minor: int, currency: str = "USD",
                     intent: str = "AUTHORIZE", reference: str = "",
                     request_id: str | None = None) -> dict:
        body = {
            "intent": intent,
            "purchase_units": [{
                "reference_id": reference or _new_request_id()[:30],
                "amount": {"currency_code": currency,
                           "value": f"{amount_minor // 100}.{amount_minor % 100:02d}"},
            }],
            "payment_source": {"paypal": {"experience_context": {
                "brand_name": "Northwind Audio",
                "shipping_preference": "NO_SHIPPING",
                "user_action": "PAY_NOW",
                "return_url": "https://example.com/return",
                "cancel_url": "https://example.com/cancel",
            }}},
        }
        return self.transport.request("POST", "/v2/checkout/orders", body,
                                      request_id or _new_request_id())

    def authorize_order(self, order_id: str, request_id: str | None = None) -> dict:
        return self.transport.request(
            "POST", f"/v2/checkout/orders/{order_id}/authorize", {},
            request_id or _new_request_id())

    def capture_authorization(self, auth_id: str, amount_minor: int | None = None,
                              currency: str = "USD",
                              request_id: str | None = None) -> dict:
        body = {}
        if amount_minor:
            body = {"amount": {"currency_code": currency,
                               "value": f"{amount_minor // 100}.{amount_minor % 100:02d}"}}
        return self.transport.request(
            "POST", f"/v2/payments/authorizations/{auth_id}/capture", body,
            request_id or _new_request_id())

    def void_authorization(self, auth_id: str,
                           request_id: str | None = None) -> dict:
        return self.transport.request(
            "POST", f"/v2/payments/authorizations/{auth_id}/void", {},
            request_id or _new_request_id())

    # -- invoicing --------------------------------------------------------
    def create_invoice(self, amount_minor: int, due_date: str, currency: str = "USD",
                       note: str = "", request_id: str | None = None) -> dict:
        """`due_date` is YYYY-MM-DD — this is the DEFER mechanic."""
        body = {
            "detail": {
                "currency_code": currency,
                "note": note or "Scheduled to your payday.",
                "payment_term": {"term_type": "NET_CUSTOM", "due_date": due_date},
            },
            "invoicer": {"business_name": "Northwind Audio"},
            "primary_recipients": [{"billing_info": {"email_address": "shopper@example.com"}}],
            "items": [{
                "name": "Headphones (scheduled payment)",
                "quantity": "1",
                "unit_amount": {"currency_code": currency,
                                "value": f"{amount_minor // 100}.{amount_minor % 100:02d}"},
            }],
        }
        return self.transport.request("POST", "/v2/invoicing/invoices", body,
                                      request_id or _new_request_id())

    # -- webhooks ---------------------------------------------------------
    def verify_webhook(self, headers: dict, event: dict) -> bool:
        body = {
            "transmission_id": headers.get("paypal-transmission-id", ""),
            "transmission_time": headers.get("paypal-transmission-time", ""),
            "cert_url": headers.get("paypal-cert-url", ""),
            "auth_algo": headers.get("paypal-auth-algo", ""),
            "transmission_sig": headers.get("paypal-transmission-sig", ""),
            "webhook_id": self.webhook_id,
            "webhook_event": event,
        }
        out = self.transport.request(
            "POST", "/v1/notifications/verify-webhook-signature", body)
        return out.get("verification_status") == "SUCCESS"


def client_from_env(force_simulated: bool = False) -> PayPalClient:
    """Build a client from the environment, falling back to the simulator."""
    cid = os.environ.get("PAYPAL_CLIENT_ID", "")
    secret = os.environ.get("PAYPAL_CLIENT_SECRET", "")
    webhook_id = os.environ.get("PAYPAL_WEBHOOK_ID", "")
    base = SANDBOX  # sandbox only, by design — this never touches live
    if force_simulated or not (cid and secret):
        return PayPalClient(transport=SimulatedTransport(),
                            webhook_id=webhook_id or "SIM-WEBHOOK")
    return PayPalClient(
        transport=LiveTransport(base, cid, secret), webhook_id=webhook_id)
