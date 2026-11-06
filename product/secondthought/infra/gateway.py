"""
infra/gateway.py — the simulated PayPal, held to the real contract.

Deliberately honest: this implements the same `PaymentGateway` protocol as the
live adapter, with the same object shapes and the same failure modes, so the
application cannot tell the difference and the badge is the only thing that
changes. It never pretends to have moved money — `mode` is "simulated" and every
invoice is marked as such in its id.
"""

from __future__ import annotations

import itertools
import secrets
from datetime import date, timedelta

from ..app.ports import Authorisation, Capture, GatewayError, Invoice

_AUTH_VALID_DAYS = 3     # PayPal: an authorisation is valid for 3 days


class SimulatedGateway:
    """An in-memory PayPal that behaves like the sandbox, minus the network."""

    mode = "simulated"

    def __init__(self, currency: str = "USD"):
        self.currency = currency
        self._seq = itertools.count(1)
        self._invoices: dict[str, Invoice] = {}
        self._auths: dict[str, Authorisation] = {}
        self.calls: list[str] = []      # audit trail for the demo and for tests

    # -- invoices ----------------------------------------------------------
    def create_invoice(self, *, amount_minor: int, currency: str,
                       due_date: date, reference: str) -> Invoice:
        if amount_minor <= 0:
            raise GatewayError("invoice amount must be positive")
        if due_date < date.today() - timedelta(days=365):
            raise GatewayError("due date is implausibly far in the past")
        inv = Invoice(
            id=f"INV2-SIM{next(self._seq):05d}{secrets.token_hex(2).upper()}",
            amount_minor=amount_minor, currency=currency, due_date=due_date,
            status="SENT", pay_url=f"https://sandbox.paypal.com/i/{reference}")
        self._invoices[inv.id] = inv
        self.calls.append(f"create_invoice {inv.id} {amount_minor} due {due_date}")
        return inv

    def send_invoice(self, invoice_id: str) -> None:
        inv = self.get_invoice(invoice_id)
        if inv.status == "PAID":
            raise GatewayError("cannot send a paid invoice")
        inv.status = "SENT"

    def get_invoice(self, invoice_id: str) -> Invoice:
        try:
            return self._invoices[invoice_id]
        except KeyError:
            raise GatewayError(f"no such invoice: {invoice_id}") from None

    def cancel_invoice(self, invoice_id: str) -> None:
        inv = self.get_invoice(invoice_id)
        if inv.status == "PAID":
            raise GatewayError("cannot cancel a paid invoice")
        inv.status = "CANCELLED"
        self.calls.append(f"cancel_invoice {invoice_id}")

    # -- authorisations ----------------------------------------------------
    def authorise(self, *, amount_minor: int, currency: str,
                  reference: str) -> Authorisation:
        if amount_minor <= 0:
            raise GatewayError("authorisation amount must be positive")
        auth = Authorisation(
            id=f"AUTH-SIM{next(self._seq):05d}{secrets.token_hex(2).upper()}",
            amount_minor=amount_minor, currency=currency, status="CREATED",
            expires_on=date.today() + timedelta(days=_AUTH_VALID_DAYS))
        self._auths[auth.id] = auth
        self.calls.append(f"authorise {auth.id} {amount_minor}")
        return auth

    def capture_authorisation(self, auth_id: str) -> Capture:
        auth = self._auths.get(auth_id)
        if not auth:
            raise GatewayError(f"no such authorisation: {auth_id}")
        if auth.status == "CAPTURED":
            # Idempotent by design: a retry returns the same capture, no double charge.
            return Capture(id=f"CAP-{auth_id[-6:]}", amount_minor=auth.amount_minor,
                           currency=auth.currency, status="COMPLETED",
                           reference="already captured")
        if auth.status == "VOIDED":
            raise GatewayError("cannot capture a voided authorisation")
        if auth.expires_on and auth.expires_on < date.today():
            raise GatewayError("authorisation has expired")
        auth.status = "CAPTURED"
        self.calls.append(f"capture {auth_id}")
        return Capture(id=f"CAP-{auth_id[-6:]}", amount_minor=auth.amount_minor,
                       currency=auth.currency, status="COMPLETED")

    def void_authorisation(self, auth_id: str) -> None:
        auth = self._auths.get(auth_id)
        if not auth:
            raise GatewayError(f"no such authorisation: {auth_id}")
        if auth.status == "CAPTURED":
            raise GatewayError("cannot void a captured authorisation")
        auth.status = "VOIDED"
        self.calls.append(f"void {auth_id}")

    # -- test helpers (not part of the protocol) ---------------------------
    def pay_invoice(self, invoice_id: str) -> Invoice:
        """Simulates the shopper paying, which in production arrives by webhook."""
        inv = self.get_invoice(invoice_id)
        if inv.status != "SENT":
            raise GatewayError(f"cannot pay an invoice in status {inv.status}")
        inv.status = "PAID"
        self.calls.append(f"invoice_paid {invoice_id}")
        return inv
