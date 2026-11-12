"""
profile.py — the shopper's payday profile.

This exists to fix the weakest assumption in the product: nobody types their
bills in at a checkout.

A shopper sets their profile up ONCE, deliberately, in their own time — the same
way they'd set up a budget app. After that every checkout is instant, because
the profile already knows their paydays and their essential bills. The checkout
never asks a question; it just applies the profile.

The profile is shopper-owned: it is created by them, is visible to them, can be
edited or deleted at any time, and no merchant sees its contents. See
DATA_AND_PRIVACY.md.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import date

from engine import CashCalendar, Obligation, Payday

DEFAULT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "profiles.json")
_UNSET = object()


@dataclass
class ProfileEntry:
    label: str
    amount_minor: int
    due: str | None = None       # ISO date; None means "recurring, no fixed date yet"
    essential: bool = True
    confidence: float = 0.5
    confirmed: bool = False      # the shopper has looked at this line


@dataclass
class PaydayProfile:
    shopper_id: str
    currency: str = "USD"
    paydays: list[ProfileEntry] = field(default_factory=list)
    obligations: list[ProfileEntry] = field(default_factory=list)
    opening_balance: int = 0
    consented_at: str | None = None
    setup_source: str = "unknown"      # "typed" | "extracted" | "persona"

    # -- the honest summary shown to the shopper -------------------------
    def summary(self) -> dict:
        return {
            "paydays": len(self.paydays),
            "obligations": len(self.obligations),
            "unconfirmed": sum(1 for o in self.obligations if not o.confirmed),
            "opening_balance": self.opening_balance,
            "consented_at": self.consented_at,
            "setup_source": self.setup_source,
        }

    def to_calendar(self, today: date) -> CashCalendar:
        return CashCalendar(
            today=today,
            opening_balance=self.opening_balance,
            paydays=[Payday(date.fromisoformat(p.due), p.amount_minor)
                     for p in self.paydays if p.due],
            obligations=[Obligation(o.label, date.fromisoformat(o.due or today.isoformat()),
                                    o.amount_minor, o.essential)
                         for o in self.obligations],
            instalments=[],
        )

    def to_dict(self) -> dict:
        return asdict(self)


class ProfileStore:
    """
    ProfileStore()          -> persists to profiles.json
    ProfileStore(path=None) -> in-memory only
    """

    def __init__(self, path: str | None = _UNSET):
        self.path = DEFAULT_PATH if path is _UNSET else path
        self.profiles: dict[str, PaydayProfile] = {}
        self.load()

    def load(self) -> None:
        if self.path and os.path.exists(self.path):
            try:
                with open(self.path) as f:
                    raw = json.load(f)
                self.profiles = {k: _from_dict(v) for k, v in raw.items()}
            except (json.JSONDecodeError, TypeError, OSError, KeyError):
                self.profiles = {}

    def save(self) -> None:
        if not self.path:
            return
        with open(self.path, "w") as f:
            json.dump({k: v.to_dict() for k, v in self.profiles.items()}, f, indent=2)

    def get(self, shopper_id: str) -> PaydayProfile | None:
        return self.profiles.get(shopper_id)

    def put(self, profile: PaydayProfile) -> PaydayProfile:
        self.profiles[profile.shopper_id] = profile
        self.save()
        return profile

    def delete(self, shopper_id: str) -> bool:
        existed = self.profiles.pop(shopper_id, None) is not None
        self.save()
        return existed


def _from_dict(d: dict) -> PaydayProfile:
    return PaydayProfile(
        shopper_id=d["shopper_id"],
        currency=d.get("currency", "USD"),
        paydays=[ProfileEntry(**e) for e in d.get("paydays", [])],
        obligations=[ProfileEntry(**e) for e in d.get("obligations", [])],
        opening_balance=d.get("opening_balance", 0),
        consented_at=d.get("consented_at"),
        setup_source=d.get("setup_source", "unknown"),
    )


def from_extraction(extraction, shopper_id: str, opening_balance: int,
                    today: date, source: str = "extracted") -> PaydayProfile:
    """Build a profile from what the model read out of the shopper's own words."""
    prof = PaydayProfile(
        shopper_id=shopper_id,
        opening_balance=opening_balance,
        consented_at=today.isoformat(),
        setup_source=source,
    )
    for o in extraction.obligations:
        prof.obligations.append(ProfileEntry(
            label=o.label, amount_minor=o.amount_minor,
            due=(o.due or today).isoformat(), essential=o.essential,
            confidence=o.confidence,
            confirmed=o.confidence >= 0.6,   # low confidence needs a human look
        ))
    for inc in getattr(extraction, "income", []) or []:
        prof.paydays.append(ProfileEntry(
            label=inc.label, amount_minor=inc.amount_minor,
            due=(inc.due or today).isoformat(), essential=False,
            confidence=inc.confidence, confirmed=True))
    return prof


def answer_quality(profile: PaydayProfile | None) -> dict:
    """
    How much the product actually knows, said on screen.

    With no profile the answer is coarser. The product says so rather than
    pretending to precision it does not have — the same honesty rule that
    governs the AI badge.
    """
    if profile is None:
        return {"grade": "demo",
                "note": "not your real data — using a demo persona, so this answer is illustrative",
                "detail": "demo persona"}
    unconfirmed = sum(1 for o in profile.obligations if not o.confirmed)
    if unconfirmed == 0 and profile.obligations:
        return {"grade": "full",
                "note": "your payday profile, every line confirmed",
                "detail": f"{len(profile.obligations)} bill(s), all confirmed"}
    return {"grade": "partial",
            "note": f"{unconfirmed} line(s) still need your confirmation — treat this as approximate",
            "detail": f"{len(profile.obligations)} bill(s), {unconfirmed} unconfirmed"}
