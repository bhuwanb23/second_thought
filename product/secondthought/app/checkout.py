"""
app/checkout.py — the use cases.

Three outcomes, three different pieces of machinery:

  OFFER    authorise a hold (3-day validity) — money is reserved, then captured
  DEFER    a reservation, pay-before-ship: invoice dated to payday, merchant
           ships only after payment. Never credit extended by the merchant.
  DECLINE  no instrument; name the collision, quote the amount that would fit.

Every money action passes through the approval gate: it is proposed, a human
approves, and only then does the gateway call happen.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from ..domain import CashCalendar, InvalidRequest, Obligation, Payday, Policy, decide
from ..domain.reservation import Reservation, State, new_reservation
from .approvals import ApprovalGate
from .ports import GatewayError, PaymentGateway

PAY_BEFORE_SHIP = ("PAY BEFORE SHIP. The merchant reserves the item and the price "
                   "but ships only after the invoice clears. No credit is extended.")
HOLD_NOTE = ("Funds are held now and captured on the approved date. The money is "
             "already reserved, so the merchant ships under its normal policy.")


@dataclass
class Checkout:
    shopper_id: str
    merchant_id: str
    amount_minor: int
    currency: str


class CheckoutService:
    def __init__(self, *, gateway: PaymentGateway, profiles, reservations,
                 ledger, approvals: ApprovalGate, policy: Policy | None = None):
        self.gateway = gateway
        self.profiles = profiles
        self.reservations = reservations
        self.ledger = ledger
        self.approvals = approvals
        self.policy = policy or Policy()

    # -- profile -----------------------------------------------------------
    def calendar_for(self, shopper_id: str, today: date) -> CashCalendar:
        p = self.profiles.get(shopper_id)
        if not p:
            raise InvalidRequest(f"no payday profile for {shopper_id}")
        return CashCalendar(
            today=today,
            opening_balance=p["opening_balance"],
            paydays=[Payday(date.fromisoformat(x["due"]), x["amount_minor"])
                     for x in p.get("paydays", []) if x.get("due")],
            obligations=[Obligation(x["label"], date.fromisoformat(x["due"]),
                                    x["amount_minor"], x.get("essential", True))
                         for x in p.get("obligations", []) if x.get("due")],
            instalments=[],
        )

    # -- the decision ------------------------------------------------------
    def quote(self, checkout: Checkout, today: date | None = None) -> dict:
        """What would happen. Moves no money and proposes nothing yet."""
        today = today or date.today()
        cal = self.calendar_for(checkout.shopper_id, today)
        d = decide(cal, checkout.amount_minor, checkout.currency, self.policy)
        return {
            "shopper_id": checkout.shopper_id,
            "merchant_id": checkout.merchant_id,
            "amount_minor": checkout.amount_minor,
            "currency": checkout.currency,
            "verdict": d.verdict,
            "headline": getattr(d, "headline", None) or self._headline(d),
            "collision": d.collision,
            "collision_date": d.collision_date.isoformat() if d.collision_date else None,
            "safe_amount_minor": self._safe(d),
            # the date a DEFER invoice would fall due — the screen needs it, and so does
            # anyone asking "pay on what day?". None for the other verdicts.
            # Only a DEFER has a "pay on" date a shopper needs. An OFFER's option
            # carries an invoice_due too (the first instalment), and printing that as
            # "pay on" would tell someone to wait when they do not have to.
            "pay_on": (d.recommended.invoice_due.isoformat()
                       if d.verdict == "DEFER" and getattr(d, "recommended", None)
                       and d.recommended.invoice_due else None),
            "instrument": self._instrument_for(d.verdict),
            "fulfilment": self._fulfilment(d.verdict),
            "risk_bearer": self._risk(d.verdict),
            "overridable": True,
        }

    @staticmethod
    def _instrument_for(verdict: str) -> str:
        return {"OFFER": "authorise_hold", "DEFER": "reservation"}.get(verdict, "none")

    @staticmethod
    def _fulfilment(verdict: str) -> str:
        return {"OFFER": HOLD_NOTE, "DEFER": PAY_BEFORE_SHIP}.get(
            verdict, "Nothing is offered, so there is nothing to fulfil.")

    @staticmethod
    def _risk(verdict: str) -> str:
        return "nobody" if verdict in ("DEFER", "DECLINE") else "paypal"

    @staticmethod
    def _safe(d) -> int | None:
        """The engine already computes the largest amount that fits. Trust it."""
        safe = getattr(d, "safe_amount", 0) or 0
        return safe if 0 < safe < d.amount else None

    @staticmethod
    def _headline(d) -> str:
        if d.verdict == "OFFER":
            return "This fits your next four weeks."
        if d.verdict == "DEFER":
            return "This fits, but not today."
        return "This would collide with a bill you must pay."

    # -- proposing a money action -----------------------------------------
    def propose(self, checkout: Checkout, today: date | None = None) -> dict:
        """Decide, then *propose* the matching action. Nothing moves yet."""
        today = today or date.today()
        quote = self.quote(checkout, today)
        if quote["instrument"] == "none":
            return {**quote, "approval_required": False,
                    "note": "No instrument offered. The shopper can still buy in full."}

        cal = self.calendar_for(checkout.shopper_id, today)
        d = decide(cal, checkout.amount_minor, checkout.currency, self.policy)

        # The token covers the arguments only. The tool name is signed alongside
        # them, so a proposal for one action can never be replayed as another.
        if quote["verdict"] == "DEFER":
            due = self._payday_after(cal, today) or (today + timedelta(days=7))
            tool = "create_reservation"
            args = {"shopper_id": checkout.shopper_id,
                    "merchant_id": checkout.merchant_id,
                    "amount_minor": checkout.amount_minor,
                    "currency": checkout.currency,
                    "due_date": due.isoformat()}
        else:
            due = None
            tool = "authorise_hold"
            args = {"shopper_id": checkout.shopper_id,
                    "merchant_id": checkout.merchant_id,
                    "amount_minor": checkout.amount_minor,
                    "currency": checkout.currency}

        approval = self.approvals.propose(tool, args)
        return {**quote, "approval_required": True,
                "tool": tool,
                "proposal": args,
                "due_date": due.isoformat() if due else None,
                "token": approval.token,
                "note": "A human must approve before anything is held or reserved."}

    @staticmethod
    def _payday_after(cal: CashCalendar, today: date) -> date | None:
        upcoming = sorted(p.due for p in cal.paydays if p.due > today)
        return upcoming[0] if upcoming else None

    # -- executing an approved action -------------------------------------
    def execute(self, tool: str, args: dict, token: str,
                now: datetime | None = None) -> dict:
        now = now or datetime.now().replace(microsecond=0)
        self.approvals.redeem(tool, args, token, now=now.timestamp())
        if tool == "create_reservation":
            return self._create_reservation(args, now)
        if tool == "authorise_hold":
            return self._authorise(args, now)
        raise InvalidRequest(f"unknown action: {tool}")

    def _create_reservation(self, args: dict, now: datetime) -> dict:
        due = date.fromisoformat(args["due_date"])
        rid = f"RES-{secrets.token_hex(4).upper()}"
        r = new_reservation(
            id=rid, shopper_id=args["shopper_id"], merchant_id=args["merchant_id"],
            amount_minor=args["amount_minor"], currency=args["currency"],
            due_date=due, hold_until=datetime.combine(due + timedelta(days=2),
                                                     datetime.min.time()),
            now=now)
        inv = self.gateway.create_invoice(
            amount_minor=args["amount_minor"], currency=args["currency"],
            due_date=due, reference=rid)
        r.attach_invoice(inv.id, now)
        self.reservations.save(r, now)
        self.ledger.add(args["shopper_id"], args["merchant_id"],
                        args["amount_minor"], "reservation", rid, now)
        return {"state": r.state.value, "reservation": r.to_dict(),
                "invoice": {"id": inv.id, "due_date": inv.due_date.isoformat(),
                            "pay_url": inv.pay_url},
                "message": f"Reserved. Pay by {due.isoformat()} and the merchant ships."}

    def _authorise(self, args: dict, now: datetime) -> dict:
        auth = self.gateway.authorise(
            amount_minor=args["amount_minor"], currency=args["currency"],
            reference=args["shopper_id"])
        self.ledger.add(args["shopper_id"], args["merchant_id"],
                        args["amount_minor"], "authorisation", auth.id, now)
        return {"state": "AUTHORISED",
                "authorisation": {"id": auth.id, "expires_on":
                                  auth.expires_on.isoformat() if auth.expires_on else None},
                "message": "Funds held. The merchant ships as normal."}

    # -- lifecycle ---------------------------------------------------------
    def mark_paid(self, invoice_id: str, payment_ref: str,
                  now: datetime | None = None) -> Reservation | None:
        """Called from the payment webhook. Idempotent."""
        now = now or datetime.now().replace(microsecond=0)
        row = self.reservations.by_invoice(invoice_id)
        if not row:
            return None
        r = _from_dict(row)
        r.pay(payment_ref, now)
        self.reservations.save(r, now)
        return r

    def fulfil(self, reservation_id: str, now: datetime | None = None) -> dict:
        """Ship. Refuses unless the reservation is PAID — the pay-before-ship rule."""
        now = now or datetime.now().replace(microsecond=0)
        row = self.reservations.get(reservation_id)
        if not row:
            raise InvalidRequest("no such reservation")
        r = _from_dict(row)
        r.fulfil(now)                       # raises ReservationError if unpaid
        self.reservations.save(r, now)
        return {"state": r.state.value, "reservation": r.to_dict()}

    def expire_overdue(self, now: datetime | None = None) -> list[str]:
        now = now or datetime.now().replace(microsecond=0)
        expired = []
        for row in self.reservations.list_open():
            r = _from_dict(row)
            if now > r.hold_until:
                r.expire(now)
                self.reservations.save(r, now)
                expired.append(r.id)
        return expired


def _from_dict(row: dict) -> Reservation:
    from ..domain.reservation import Event
    r = Reservation(
        id=row["id"], shopper_id=row["shopper_id"], merchant_id=row["merchant_id"],
        amount_minor=row["amount_minor"], currency=row["currency"],
        due_date=date.fromisoformat(row["due_date"]),
        hold_until=datetime.fromisoformat(row["hold_until"]),
        invoice_id=row.get("invoice_id"), payment_ref=row.get("payment_ref"),
        state=State(row["state"]))
    r.events = [Event(datetime.fromisoformat(e["at"]), e["kind"], e.get("detail", ""))
                for e in row.get("events", [])]
    return r
