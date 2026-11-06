"""
ledger.py — our own plan ledger.

This exists because of validation finding V1: no PayPal API exposes a
consumer's existing BNPL plans to a merchant. So we keep the ones *we*
originated, and the shopper can declare the ones we cannot see.

That is the honest boundary of what the product knows, and it is enough to
catch the collision that actually causes late fees: the same shopper buying
more than once with the same merchant inside one month.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import date, timedelta

from engine import INSTALMENT_GAP_DAYS, Instalment, split_instalments

DEFAULT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ledger.json")
_UNSET = object()   # distinguishes "use the default file" from "in-memory only"


@dataclass
class LedgerEntry:
    plan_id: str
    shopper_id: str
    amount: int                 # minor units
    currency: str
    started: str                # ISO date
    instrument: str             # "pay_in_4" | "invoice" | "authorize_hold"
    paypal_ref: str = ""        # order / authorization / invoice id
    override: bool = False      # shopper bought despite a non-OFFER verdict
    override_reason: str = ""

    def instalments(self) -> list[Instalment]:
        if self.instrument != "pay_in_4":
            return []
        start = date.fromisoformat(self.started)
        parts = split_instalments(self.amount, 4)
        return [
            Instalment(self.plan_id, i + 1,
                       start + timedelta(days=INSTALMENT_GAP_DAYS * i), amt)
            for i, amt in enumerate(parts)
        ]


class Ledger:
    def __init__(self, path: str | None = _UNSET):
        """
        Ledger()          -> persists to ledger.json
        Ledger(path=None) -> in-memory only (tests, demos)
        """
        self.path = DEFAULT_PATH if path is _UNSET else path
        self.entries: list[LedgerEntry] = []
        self.load()

    # -- persistence ------------------------------------------------------
    def load(self) -> None:
        if self.path and os.path.exists(self.path):
            try:
                with open(self.path) as f:
                    raw = json.load(f)
                self.entries = [LedgerEntry(**e) for e in raw]
            except (json.JSONDecodeError, TypeError, OSError):
                self.entries = []

    def save(self) -> None:
        if not self.path:
            return
        with open(self.path, "w") as f:
            json.dump([asdict(e) for e in self.entries], f, indent=2)

    # -- queries ----------------------------------------------------------
    def instalments_for(self, shopper_id: str) -> list[Instalment]:
        out: list[Instalment] = []
        for e in self.entries:
            if e.shopper_id == shopper_id:
                out.extend(e.instalments())
        return out

    def live_plans(self, shopper_id: str, today: date) -> list[LedgerEntry]:
        return [e for e in self.entries
                if e.shopper_id == shopper_id
                and e.instrument == "pay_in_4"
                and date.fromisoformat(e.started) + timedelta(days=42) >= today]

    def exposure(self, shopper_id: str, today: date) -> dict:
        live = self.live_plans(shopper_id, today)
        open_amount = 0
        for e in live:
            done = sum(1 for i in e.instalments() if i.due < today)
            open_amount += sum(i.amount for i in e.instalments()[done:])
        return {
            "plans_open": len(live),
            "open_amount": open_amount,
            "overrides": sum(1 for e in self.entries if e.override),
        }

    # -- writes -----------------------------------------------------------
    def record(self, shopper_id: str, amount: int, currency: str,
               instrument: str, paypal_ref: str = "",
               override: bool = False, override_reason: str = "",
               today: date | None = None) -> LedgerEntry:
        today = today or date.today()
        entry = LedgerEntry(
            plan_id=f"PLAN-{len(self.entries) + 1:03d}",
            shopper_id=shopper_id,
            amount=amount,
            currency=currency,
            started=today.isoformat(),
            instrument=instrument,
            paypal_ref=paypal_ref,
            override=override,
            override_reason=override_reason,
        )
        self.entries.append(entry)
        self.save()
        return entry
