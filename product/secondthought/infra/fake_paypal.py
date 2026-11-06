"""
infra/fake_paypal.py — a transport that answers like the sandbox, offline.

This is a **test double**, never wired to `--live`. It exists so the live
adapter's request construction, response parsing, idempotency and 204 handling
can be verified without a network, a key or an account — and so `demo.py
--dry-run` exercises exactly the same code path as the real thing.

It is deliberately fussy about the details that bite in production:

  * `POST /v2/checkout/orders` honours `PayPal-Request-Id` the way PayPal does —
    the same header returns the same order; a different header makes a new one.
  * Invoice creation returns only an `href`, not an `id`, because that is what
    PayPal returns. If the adapter cannot parse it, the dry run fails here
    rather than after a browser approval.
  * Void returns **204 with an empty body**, the v2 default.
"""

from __future__ import annotations

import hashlib
import itertools
import json
from urllib.parse import urlparse

_VERBS = ("authorize", "capture", "void", "send", "cancel")


class FakePayPal:
    """`(method, url, headers, body) -> (status, headers, body_bytes)`"""

    def __init__(self):
        self.requests: list[dict] = []
        self.orders: dict[str, dict] = {}
        self.auths: dict[str, dict] = {}
        self.invoices: dict[str, dict] = {}
        self._by_request_id: dict[str, str] = {}
        self._seq = itertools.count(1)
        self._segments: list[str] = []
        self.expires_in = 32400

    # -- transport ----------------------------------------------------------
    def __call__(self, method: str, url: str, headers: dict,
                 body: "bytes | None") -> tuple:
        path = urlparse(url).path
        self._segments = [p for p in path.split("/") if p]
        lowered = {k.lower(): v for k, v in headers.items()}
        # the OAuth body is form-encoded, not JSON — do not try to parse it as such
        is_json = "json" in lowered.get("content-type", "")
        self.requests.append({"method": method, "path": path, "headers": lowered,
                              "body": json.loads(body.decode()) if body and is_json else {}})
        status, payload = self._route(method, self._segments)(lowered)
        raw = b"" if payload is None else json.dumps(payload).encode()
        extra = {"Location": payload["href"]} if payload and "href" in payload else {}
        return status, extra, raw

    # last path segment that is not a verb — the resource id
    @property
    def _rid(self) -> str:
        tail = list(self._segments)
        while tail and tail[-1] in _VERBS:
            tail.pop()
        return tail[-1] if tail else ""

    # -- routes -------------------------------------------------------------
    def _route(self, method: str, seg: list[str]):
        joined = "/" + "/".join(seg)
        if joined == "/v1/oauth2/token":
            return self._token
        if joined == "/v2/checkout/orders":
            return self._create_order
        if joined.startswith("/v2/checkout/orders/"):
            return self._authorize_order if seg[-1] == "authorize" else self._get_order
        if joined.startswith("/v2/payments/authorizations/"):
            return self._capture if seg[-1] == "capture" else self._void
        if joined == "/v2/invoicing/invoices":
            return self._create_invoice
        if joined.startswith("/v2/invoicing/invoices/"):
            if seg[-1] == "send":
                return self._send_invoice
            return self._get_invoice
        return lambda _h: (404, {"name": "NOT_FOUND", "path": joined})

    # -- handlers -----------------------------------------------------------
    def _token(self, _h):
        return 200, {"access_token": "A21AA" + "FAKE" * 8, "token_type": "Bearer",
                     "expires_in": self.expires_in, "app_id": "APP-FAKE-80",
                     "nonce": "2026-11-02T00:00:00Z_nonce",
                     "scope": "https://uri.paypal.com/services/invoicing openid"}

    def _create_order(self, headers):
        rid = headers.get("paypal-request-id", "")
        if rid and rid in self._by_request_id:        # idempotent, as PayPal is
            return 201, self.orders[self._by_request_id[rid]]
        n = next(self._seq)
        unit = self.requests[-1]["body"]["purchase_units"][0]
        oid = f"ORD-DRY{n:04d}{hashlib.sha1(str(n).encode()).hexdigest()[:6].upper()}"
        order = {"id": oid, "status": "CREATED",
                 "intent": self.requests[-1]["body"].get("intent"),
                 "purchase_units": [{"reference_id": unit["reference_id"],
                                     "amount": unit["amount"]}],
                 "links": [{"rel": "payer-action",
                            "href": f"https://www.sandbox.paypal.com/checkoutnow?token={oid}"}]}
        self.orders[oid] = order
        if rid:
            self._by_request_id[rid] = oid
        return 201, order

    def _get_order(self, _h):
        order = self.orders.get(self._rid)
        if not order:
            return 404, {"name": "INVALID_RESOURCE_ID"}
        return 200, {**order, "status": "APPROVED"}      # dry run: buyer approves instantly

    def _authorize_order(self, _h):
        order = self.orders.get(self._rid)
        if not order:
            return 404, {"name": "INVALID_RESOURCE_ID"}
        n = next(self._seq)
        auth = {"id": f"AUTH-DRY{n:012d}", "status": "CREATED",
                "amount": order["purchase_units"][0]["amount"],
                "expiration_time": "2026-11-05T00:00:00Z"}
        self.auths[auth["id"]] = auth
        return 201, {**order, "status": "COMPLETED",
                     "purchase_units": [{**order["purchase_units"][0],
                                         "payments": {"authorizations": [auth]}}]}

    def _capture(self, _h):
        auth = self.auths.get(self._rid)
        if not auth:
            return 404, {"name": "INVALID_RESOURCE_ID"}
        auth["status"] = "CAPTURED"
        return 201, {"id": f"CAP-DRY{auth['id'][-6:]}", "status": "COMPLETED",
                     "amount": auth["amount"],
                     "seller_protection": {"status": "ELIGIBLE"}}

    def _void(self, _h):
        auth = self.auths.get(self._rid)
        if not auth:
            return 404, {"name": "INVALID_RESOURCE_ID"}
        auth["status"] = "VOIDED"
        return 204, None                                  # v2 default: no body at all

    def _create_invoice(self, headers):
        n = next(self._seq)
        tail = hashlib.sha1(str(n).encode()).hexdigest()[:4].upper()
        iid = f"INV2-DRY{n:04d}-0000-0000-000{tail}"
        body = self.requests[-1]["body"]
        self.invoices[iid] = {"id": iid, "status": "DRAFT", "detail": body["detail"],
                              "items": body.get("items", []),
                              "amount": {"total": body["items"][0]["unit_amount"]}}
        return 201, {"href": f"https://api-m.sandbox.paypal.com/v2/invoicing/invoices/{iid}"}

    def _get_invoice(self, _h):
        inv = self.invoices.get(self._rid)
        if not inv:
            return 404, {"name": "INVALID_RESOURCE_ID"}
        return 200, inv

    def _send_invoice(self, _h):
        inv = self.invoices.get(self._rid)
        if not inv:
            return 404, {"name": "INVALID_RESOURCE_ID"}
        inv["status"] = "UNPAID"
        return 202, {"_note": "sent"}
