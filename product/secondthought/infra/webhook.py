"""
infra/webhook.py — a payment webhook is a stranger claiming money moved.

Anyone can POST to a public URL, so an unverified webhook is not a notification,
it is an instruction from an anonymous party to ship goods. This module refuses
everything it cannot verify, and **records the refusal** — a rejection nobody can
see is indistinguishable from a webhook that never arrived.

PayPal's scheme: RSA-SHA256 over

    transmissionId|transmissionTime|webhookId|crc32(rawBody)

with the signature in `PAYPAL-TRANSMISSION-SIG` and the key at
`PAYPAL-CERT-URL`.

Three things worth stating because they are the usual holes:

  * **The raw bytes are signed, not parsed JSON.** Re-serialising before verifying
    changes the message and the signature stops matching — or worse, starts.
  * **The cert URL is attacker-controlled input.** It is fetched only over HTTPS,
    only from a PayPal host, and a failure is a rejection, never a skip.
  * **A valid signature is not a new event.** A captured delivery can be replayed
    forever, so transmission ids are remembered.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
import zlib

from .rsa import KeyError_, parse_public_key, verify_sha256

ALLOWED_CERT_HOSTS = ("api.paypal.com", "api-m.paypal.com", "api.sandbox.paypal.com",
                      "api-m.sandbox.paypal.com", "www.paypal.com", "www.sandbox.paypal.com")
REQUIRED_HEADERS = {
    "transmission_id": "PAYPAL-TRANSMISSION-ID",
    "transmission_time": "PAYPAL-TRANSMISSION-TIME",
    "cert_url": "PAYPAL-CERT-URL",
    "signature": "PAYPAL-TRANSMISSION-SIG",
    "auth_algo": "PAYPAL-AUTH-ALGO",
}


class Rejection(Exception):
    """A delivery that must not be acted on. `reason` is safe to show."""

    def __init__(self, reason: str, detail: str = ""):
        super().__init__(reason)
        self.reason = reason
        self.detail = detail


def canonical(transmission_id: str, transmission_time: str, webhook_id: str,
              raw_body: bytes) -> bytes:
    """The exact string PayPal signs. Note the CRC is of the raw bytes."""
    crc = zlib.crc32(raw_body) & 0xFFFFFFFF
    return f"{transmission_id}|{transmission_time}|{webhook_id}|{crc}".encode()


def check_cert_url(url: str) -> None:
    """Refuse before fetching. Kept separate so an injected lookup cannot skip it."""
    parsed = urllib.parse.urlparse(url or "")
    if parsed.scheme != "https":
        raise Rejection("cert url is not https", parsed.scheme or "missing")
    if parsed.hostname not in ALLOWED_CERT_HOSTS:
        raise Rejection("cert url host is not PayPal", str(parsed.hostname))


def _fetch_cert(url: str, timeout: int = 10) -> str:
    check_cert_url(url)                 # defence in depth; _key checks first
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.read(65536).decode("utf-8", "replace")
    except (urllib.error.URLError, OSError) as exc:
        raise Rejection("cert could not be fetched", str(exc)) from None


class WebhookVerifier:
    """Verify, remember, and keep a visible record of every attempt."""

    def __init__(self, webhook_id: str, *, cert_lookup=None, max_log: int = 200):
        self.webhook_id = webhook_id
        self.cert_lookup = cert_lookup or _fetch_cert
        self.seen: dict[str, float] = {}
        self.log: list[dict] = []
        self.max_log = max_log
        self._cert_cache: dict[str, tuple] = {}

    # -- the gate ----------------------------------------------------------
    def verify(self, headers: dict, raw_body: bytes) -> dict:
        """Return the parsed event, or raise `Rejection` and log why."""
        started = time.time()
        lowered = {k.lower(): v for k, v in (headers or {}).items()}
        try:
            for field, name in REQUIRED_HEADERS.items():
                if not lowered.get(name.lower()):
                    raise Rejection("missing header", name)
            if not self.webhook_id:
                raise Rejection("no webhook id configured",
                                "PAYPAL_WEBHOOK_ID is unset, so nothing can be verified")
            tid = lowered["paypal-transmission-id"]
            if tid in self.seen:
                raise Rejection("replayed transmission", tid)
            message = canonical(tid, lowered["paypal-transmission-time"],
                                self.webhook_id, raw_body)
            n, e = self._key(lowered["paypal-cert-url"])
            sig = _b64(lowered["paypal-transmission-sig"])
            if not verify_sha256(message, sig, n, e):
                raise Rejection("signature does not verify",
                                f"algo={lowered.get('paypal-auth-algo', '?')}")
            try:
                event = json.loads(raw_body.decode() or "{}")
            except (ValueError, UnicodeDecodeError):
                raise Rejection("body is not JSON after a valid signature") from None
            self.seen[tid] = time.time()
            self._record(True, event.get("event_type", "?"), tid, "verified", started)
            return event
        except Rejection as rej:
            self._record(False, "?", lowered.get("paypal-transmission-id", "?"),
                         rej.reason, started, rej.detail)
            raise

    def _key(self, cert_url: str) -> tuple:
        check_cert_url(cert_url)        # an injected lookup must not bypass this
        if cert_url in self._cert_cache:
            return self._cert_cache[cert_url]
        pem = self.cert_lookup(cert_url)
        try:
            key = parse_public_key(pem)
        except KeyError_ as exc:
            raise Rejection("cert is not a usable RSA key", str(exc)) from None
        self._cert_cache[cert_url] = key
        return key

    # -- the record --------------------------------------------------------
    def _record(self, ok: bool, event_type: str, tid: str, reason: str,
                started: float, detail: str = "") -> None:
        self.log.append({"at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                         "ok": ok, "event_type": event_type,
                         "transmission_id": tid[:24], "reason": reason,
                         "detail": detail, "ms": int((time.time() - started) * 1000)})
        if len(self.log) > self.max_log:
            self.log = self.log[-self.max_log:]

    @property
    def rejections(self) -> list:
        return [r for r in self.log if not r["ok"]]

    def summary(self) -> dict:
        return {"received": len(self.log), "rejected": len(self.rejections),
                "accepted": len([r for r in self.log if r["ok"]]),
                "last": self.log[-5:]}


def _b64(value: str) -> bytes:
    import base64
    try:
        return base64.b64decode(value, validate=False)
    except Exception:
        return b""
