"""
app/ports.py — what the application needs from the outside world.

Narrow interfaces, so the domain never learns that PayPal exists and the tests
never need a network. The simulated implementation is held to the same shape as
the real one, which is what makes a "simulated" badge honest: it is the same
contract, not a different code path with the money removed.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol


@dataclass
class Invoice:
    id: str
    amount_minor: int
    currency: str
    due_date: date
    status: str            # DRAFT | SENT | PAID | CANCELLED
    pay_url: str | None = None


@dataclass
class Authorisation:
    id: str
    amount_minor: int
    currency: str
    status: str            # CREATED | CAPTURED | VOIDED
    expires_on: date | None = None


@dataclass
class Capture:
    id: str
    amount_minor: int
    currency: str
    status: str            # COMPLETED | PENDING | DECLINED
    reference: str | None = None


class PaymentGateway(Protocol):
    """Every method a real PayPal client must provide. No more, no less."""

    mode: str              # "live" (real sandbox transport) or "simulated"

    def create_invoice(self, *, amount_minor: int, currency: str,
                       due_date: date, reference: str) -> Invoice: ...

    def send_invoice(self, invoice_id: str) -> None: ...

    def get_invoice(self, invoice_id: str) -> Invoice: ...

    def cancel_invoice(self, invoice_id: str) -> None: ...

    def authorise(self, *, amount_minor: int, currency: str,
                  reference: str) -> Authorisation: ...

    def capture_authorisation(self, auth_id: str) -> Capture: ...

    def void_authorisation(self, auth_id: str) -> None: ...


class GatewayError(Exception):
    """A call to PayPal that did not succeed."""
