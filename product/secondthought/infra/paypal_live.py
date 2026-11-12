"""
infra/paypal_live.py — the real PayPal sandbox, behind the same contract.

`SimulatedGateway` and `PayPalLiveGateway` implement the identical
`PaymentGateway` protocol; only `mode` differs. That is what makes the badge
honest — the application cannot tell which one it is holding.

Two deliberate safety rails:

  * `PAYPAL_ENV=live` is refused. This adapter moves sandbox money only. A
    mis-set variable should stop the process, not spend a shopper's money.
  * Every mutating call carries a `PayPal-Request-Id`, derived from the caller's
    reference, so a retry is the same request rather than a second one.

The transport is injectable: `tests/test_paypal_live.py` drives the whole
adapter with a fake that records requests, so request construction is verified
without a network, a key or an account.
"""

from __future__ import annotations

import base64
import json
import time
import urllib.error
import urllib.request
from datetime import date
from typing import Callable

from ..app.ports import Authorisation, Capture, GatewayError, Invoice

# (method, url, headers, body_or_None) -> (status, headers, body_bytes)
Transport = Callable[[str, str, dict, "bytes | None"], tuple]


def money(minor: int) -> str:
    """Integer minor units to a PayPal amount string. No floating point, ever."""
    sign = "-" if minor < 0 else ""
    minor = abs(minor)
    return f"{sign}{minor // 100}.{minor % 100:02d}"


def _urllib_transport(method: str, url: str, headers: dict,
                      body: "bytes | None") -> tuple:
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()
    except urllib.error.URLError as e:
        raise GatewayError(f"network: {e.reason}") from None


class PayPalHTTP:
    """Token cache plus one `request()` that never throws on a 4xx."""

    def __init__(self, settings, transport: Transport | None = None):
        self.settings = settings
        self._transport = transport or _urllib_transport
        # an injected transport means a test double; it needs no real credentials
        self.requires_credentials = transport is None
        self._token: str = ""
        self._expires_at: float = 0.0

    # -- auth ---------------------------------------------------------------
    def token(self, force: bool = False) -> dict:
        """Fetch (and cache) an OAuth token. Returns the raw response."""
        if self.settings.env == "live":
            raise GatewayError("refusing to run: PAYPAL_ENV=live moves real money")
        if not force and self._token and time.time() < self._expires_at:
            return {"access_token": self._token, "expires_in": int(self._expires_at - time.time()),
                    "cached": True}
        creds = f"{self.settings.client_id}:{self.settings.client_secret}"
        basic = base64.b64encode(creds.encode()).decode()
        status, _h, raw = self._transport(
            "POST", f"{self.settings.base_url}/v1/oauth2/token",
            {"Authorization": f"Basic {basic}",
             "Content-Type": "application/x-www-form-urlencoded"},
            b"grant_type=client_credentials")
        if status != 200:
            raise GatewayError(f"OAuth failed: HTTP {status} {raw[:300]!r}")
        data = json.loads(raw.decode() or "{}")
        self._token = data.get("access_token", "")
        # refresh a minute early so a slow call never carries a dying token
        self._expires_at = time.time() + int(data.get("expires_in", 0)) - 60
        data["fetched_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        return data

    # -- one call ------------------------------------------------------------
    def request(self, method: str, path: str, body: dict | None = None, *,
                request_id: str | None = None, prefer: str | None = None) -> tuple:
        if self.settings.env == "live":
            raise GatewayError("refusing to run: PAYPAL_ENV=live moves real money")
        if self.requires_credentials and not self.settings.configured:
            raise GatewayError("PAYPAL_CLIENT_ID / PAYPAL_CLIENT_SECRET are not set")
        headers = {"Authorization": f"Bearer {self.token()['access_token']}",
                   "Content-Type": "application/json"}
        if request_id:
            headers["PayPal-Request-Id"] = request_id
        if prefer:
            headers["Prefer"] = prefer
        payload = json.dumps(body).encode() if body is not None else None
        status, rh, raw = self._transport(method, f"{self.settings.base_url}{path}",
                                          headers, payload)
        try:
            parsed = json.loads(raw.decode()) if raw else {}
        except (ValueError, UnicodeDecodeError):
            parsed = {"_raw": raw.decode("utf-8", "replace")}
        return status, rh, parsed


class PayPalLiveGateway:
    """Orders v2 (authorize/capture/void) and Invoicing v2, in sandbox."""

    mode = "live"   # real sandbox transport — not simulated

    def __init__(self, settings, transport: Transport | None = None,
                 on_approval: Callable[[str], None] | None = None,
                 approve_timeout: int = 300, poll_every: int = 5):
        self.http = PayPalHTTP(settings, transport)
        self.environment = settings.env
        self.on_approval = on_approval or (lambda url: None)
        self.approve_timeout = approve_timeout
        self.poll_every = poll_every
        self.log: list[dict] = []      # every call, for the evidence file

    # -- helpers -------------------------------------------------------------
    def _call(self, step: str, method: str, path: str, body: dict | None = None,
              *, request_id: str | None = None, prefer: str | None = None,
              ok=(200, 201, 202, 204)) -> dict:
        status, headers, data = self.http.request(method, path, body,
                                                  request_id=request_id, prefer=prefer)
        self.log.append({"step": step, "method": method, "path": path, "status": status,
                         "request_id": request_id, "sent": body, "received": data})
        if status not in ok:
            raise GatewayError(f"{step}: HTTP {status} {json.dumps(data)[:400]}")
        data["_status"] = status
        data["_headers"] = {k: v for k, v in headers.items()
                            if k.lower() in ("location", "paypal-debug-id")}
        return data

    @staticmethod
    def _approval_url(order: dict) -> str:
        for link in order.get("links") or []:
            if link.get("rel") in ("payer-action", "approve"):
                return link.get("href", "")
        return ""

    def create_order(self, *, amount_minor: int, currency: str, reference: str,
                     request_id: str) -> dict:
        return self._call("create_order", "POST", "/v2/checkout/orders", {
            "intent": "AUTHORIZE",
            "purchase_units": [{
                "reference_id": reference[:40],
                "description": "Second Thought — payday-aware checkout",
                "amount": {"currency_code": currency, "value": money(amount_minor)},
            }],
            "application_context": {"user_action": "PAY_NOW",
                                    "shipping_preference": "NO_SHIPPING"},
        }, request_id=request_id)

    def wait_for_approval(self, order_id: str) -> dict:
        """Poll until the shopper approves in the browser. A human is the payer."""
        deadline = time.time() + self.approve_timeout
        while True:
            order = self._call("poll_order", "GET", f"/v2/checkout/orders/{order_id}")
            if order.get("status") == "APPROVED":
                return order
            if order.get("status") in ("COMPLETED", "VOIDED"):
                raise GatewayError(f"order is {order.get('status')}, not awaiting approval")
            if time.time() > deadline:
                raise GatewayError(
                    f"no approval within {self.approve_timeout}s — the order is still "
                    f"{order.get('status')}. Open the approval URL and run again.")
            time.sleep(self.poll_every)

    # -- PaymentGateway protocol --------------------------------------------
    def authorise(self, *, amount_minor: int, currency: str, reference: str) -> Authorisation:
        order = self.create_order(amount_minor=amount_minor, currency=currency,
                                  reference=reference, request_id=f"st-auth-{reference}")
        url = self._approval_url(order)
        self.on_approval(url)
        self.wait_for_approval(order["id"])
        done = self._call("authorize_order", "POST",
                          f"/v2/checkout/orders/{order['id']}/authorize",
                          prefer="return=representation")
        auths = (done.get("purchase_units") or [{}])[0].get("payments", {}) \
                                                      .get("authorizations", [])
        if not auths:
            raise GatewayError(f"no authorisation in response: {json.dumps(done)[:400]}")
        a = auths[0]
        return Authorisation(id=a["id"], amount_minor=amount_minor, currency=currency,
                             status=a.get("status", "CREATED"),
                             expires_on=_date(a.get("expiration_time")))

    def capture_authorisation(self, auth_id: str) -> Capture:
        body = self._call("capture_authorization", "POST",
                          f"/v2/payments/authorizations/{auth_id}/capture",
                          {"final_capture": True}, prefer="return=representation",
                          request_id=f"st-cap-{auth_id}")
        amount = body.get("amount") or {}
        return Capture(id=body.get("id", ""),
                       amount_minor=_minor(amount.get("value", "0")),
                       currency=amount.get("currency_code", "USD"),
                       status=body.get("status", ""))

    def void_authorisation(self, auth_id: str) -> None:
        body = self._call("void_authorization", "POST",
                          f"/v2/payments/authorizations/{auth_id}/void", {},
                          prefer="return=representation", request_id=f"st-void-{auth_id}")
        # v2 returns 204 No Content by default; with `Prefer: return=representation`
        # it returns the voided resource. Accept either, reject anything else.
        if body.get("_status") == 204 or body.get("status") == "VOIDED":
            return
        raise GatewayError(f"void did not report VOIDED: {json.dumps(body)[:300]}")

    def create_invoice(self, *, amount_minor: int, currency: str,
                       due_date: date, reference: str) -> Invoice:
        body = self._call("create_invoice", "POST", "/v2/invoicing/invoices", {
            "detail": {
                "currency_code": currency,
                "reference": reference[:120],
                "note": "Second Thought — pay on your payday, not before.",
                "invoice_number": reference[:25],
                "payment_term": {"term_type": "DUE_ON_DATE_SPECIFIED",
                                 "due_date": due_date.isoformat()},
            },
            "items": [{"name": "Northwind Audio — order",
                       "quantity": "1",
                       "unit_amount": {"currency_code": currency,
                                       "value": money(amount_minor)}}],
        }, request_id=f"st-inv-{reference}")
        invoice_id = _invoice_id(body)
        if not invoice_id:
            raise GatewayError(f"no invoice id in response: {json.dumps(body)[:300]}")
        return self.get_invoice(invoice_id)

    def get_invoice(self, invoice_id: str) -> Invoice:
        body = self._call("get_invoice", "GET", f"/v2/invoicing/invoices/{invoice_id}")
        detail = body.get("detail") or {}
        term = detail.get("payment_term") or {}
        total = ((body.get("amount") or {}).get("total") or {}).get("value") \
            or _sum_items(body)
        return Invoice(id=body.get("id", invoice_id),
                       amount_minor=_minor(total),
                       currency=detail.get("currency_code", "USD"),
                       due_date=_date(term.get("due_date") or detail.get("invoice_date"))
                       or date.today(),
                       status=body.get("status", "DRAFT"),
                       pay_url=((body.get("detail") or {}).get("metadata") or {})
                       .get("recipient_view_url"))

    def send_invoice(self, invoice_id: str) -> dict:
        return self._call("send_invoice", "POST",
                          f"/v2/invoicing/invoices/{invoice_id}/send", {})

    def cancel_invoice(self, invoice_id: str) -> None:
        """Invoicing v2 deletes a DRAFT; a sent invoice must be cancelled in the UI."""
        self._call("delete_invoice", "DELETE", f"/v2/invoicing/invoices/{invoice_id}")


# --------------------------------------------------------------------------
def _minor(value: str) -> int:
    """'249.00' -> 24900, without float rounding."""
    whole, _, frac = str(value).partition(".")
    return int(whole or 0) * 100 + int((frac + "00")[:2] or 0)


def _date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _invoice_id(body: dict) -> str:
    """Invoicing returns an href rather than an id on create."""
    if body.get("id"):
        return body["id"]
    href = body.get("href") or (body.get("_headers") or {}).get("Location") or ""
    return href.rstrip("/").split("/")[-1] if href else ""


def _sum_items(body: dict) -> str:
    total = 0
    for item in body.get("items") or []:
        unit = item.get("unit_amount") or {}
        total += _minor(unit.get("value", "0")) * int(item.get("quantity", 1))
    return money(total)
