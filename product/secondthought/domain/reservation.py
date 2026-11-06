"""
domain/reservation.py — the pay-before-ship promise, as a state machine.

This is the rule the whole product rests on:

    The merchant reserves the item and the price, but ships only after payment.

It is not a convention or a comment. `fulfil()` raises unless the reservation is
PAID, and there is no method that lets a caller skip the payment state. A
merchant integrating this cannot accidentally ship into unpaid credit.

    RESERVED ──pay──▶ PAID ──fulfil──▶ FULFILLED
       │                │
       ├──expire──▶ EXPIRED
       └──cancel──▶ RELEASED
                        └──refund──▶ REFUNDED
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum

from .cashflow import InvalidRequest


class State(str, Enum):
    RESERVED = "RESERVED"      # price locked, waiting for payment on the due date
    PAID = "PAID"              # money has arrived
    FULFILLED = "FULFILLED"    # shipped — only reachable from PAID
    EXPIRED = "EXPIRED"        # not paid by the hold deadline
    RELEASED = "RELEASED"      # shopper cancelled before paying
    REFUNDED = "REFUNDED"      # paid, then returned


class ReservationError(InvalidRequest):
    """A transition that the promise does not allow."""


@dataclass
class Event:
    at: datetime
    kind: str
    detail: str = ""


@dataclass
class Reservation:
    id: str
    shopper_id: str
    merchant_id: str
    amount_minor: int
    currency: str
    due_date: date
    hold_until: datetime
    invoice_id: str | None = None
    payment_ref: str | None = None
    paid_at: datetime | None = None
    fulfilled_at: datetime | None = None
    state: State = State.RESERVED
    events: list[Event] = field(default_factory=list)

    # -- guards ------------------------------------------------------------
    def _require(self, *allowed: State) -> None:
        if self.state not in allowed:
            raise ReservationError(
                f"cannot do that from {self.state.value}; "
                f"expected {' or '.join(s.value for s in allowed)}")

    def _log(self, at: datetime, kind: str, detail: str = "") -> None:
        self.events.append(Event(at, kind, detail))

    @property
    def is_open(self) -> bool:
        return self.state is State.RESERVED

    @property
    def owes_shipping(self) -> bool:
        return self.state is State.PAID

    # -- transitions -------------------------------------------------------
    def attach_invoice(self, invoice_id: str, at: datetime) -> None:
        self._require(State.RESERVED)
        self.invoice_id = invoice_id
        self._log(at, "invoice_attached", invoice_id)

    def pay(self, payment_ref: str, at: datetime) -> None:
        """
        Idempotent: a webhook retried five times still leaves one payment.
        Paying twice with a *different* reference is refused, not silently
        merged — that is money we did not expect.
        """
        # A webhook is at-least-once. A repeat of the same payment must be a
        # no-op in every state that came after it — paid, shipped, refunded.
        if (self.state in (State.PAID, State.FULFILLED, State.REFUNDED)
                and payment_ref == self.payment_ref):
            self._log(at, "payment_duplicate_ignored", payment_ref)
            return
        self._require(State.RESERVED)
        self.state = State.PAID
        self.payment_ref = payment_ref
        self.paid_at = at
        self._log(at, "paid", payment_ref)

    def fulfil(self, at: datetime) -> None:
        """Ship. Only after payment — this is the promise, enforced."""
        self._require(State.PAID)
        self.state = State.FULFILLED
        self.fulfilled_at = at
        self._log(at, "fulfilled")

    def expire(self, at: datetime) -> None:
        self._require(State.RESERVED)
        if at <= self.hold_until:
            raise ReservationError(
                f"too early: the hold runs until {self.hold_until.isoformat()}")
        self.state = State.EXPIRED
        self._log(at, "expired", f"hold_until={self.hold_until.isoformat()}")

    def cancel(self, at: datetime, reason: str = "shopper cancelled") -> None:
        self._require(State.RESERVED)
        self.state = State.RELEASED
        self._log(at, "released", reason)

    def refund(self, at: datetime, reason: str = "returned") -> None:
        self._require(State.PAID, State.FULFILLED)
        self.state = State.REFUNDED
        self._log(at, "refunded", reason)

    # -- reporting ---------------------------------------------------------
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "shopper_id": self.shopper_id,
            "merchant_id": self.merchant_id,
            "amount_minor": self.amount_minor,
            "currency": self.currency,
            "due_date": self.due_date.isoformat(),
            "hold_until": self.hold_until.isoformat(),
            "invoice_id": self.invoice_id,
            "payment_ref": self.payment_ref,
            "state": self.state.value,
            "shippable": self.state is State.PAID,
            "events": [{"at": e.at.isoformat(), "kind": e.kind, "detail": e.detail}
                       for e in self.events],
        }


def new_reservation(*, id: str, shopper_id: str, merchant_id: str,
                    amount_minor: int, currency: str, due_date: date,
                    hold_until: datetime, now: datetime) -> Reservation:
    if amount_minor <= 0:
        raise ReservationError("amount must be positive")
    if hold_until < now:
        raise ReservationError("hold_until is already in the past")
    r = Reservation(id=id, shopper_id=shopper_id, merchant_id=merchant_id,
                    amount_minor=amount_minor, currency=currency,
                    due_date=due_date, hold_until=hold_until)
    r._log(now, "reserved", f"{amount_minor} due {due_date.isoformat()}")
    return r
