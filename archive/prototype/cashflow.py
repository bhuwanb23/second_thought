"""
cashflow.py — the raw material: calendars, money, and balance projection.

Split out of engine.py so every module stays under 300 lines. Nothing here
decides anything; it represents a month and projects a balance curve.
"""

from __future__ import annotations

import calendar as _cal
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Literal

Verdict = Literal["OFFER", "DEFER", "DECLINE"]
OptionKind = Literal["PAY_NOW", "PAY_IN_4", "DEFER_TO_PAYDAY", "PARTIAL_NOW"]

HORIZON_DAYS = 45
INSTALMENT_GAP_DAYS = 14


class InvalidRequest(ValueError):
    """Raised for inputs that are not a judgement call — bad data."""


# --------------------------------------------------------------------------
# inputs
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Payday:
    due: date
    amount: int  # minor units, income


@dataclass(frozen=True)
class Obligation:
    label: str
    due: date
    amount: int  # minor units
    essential: bool = True


@dataclass(frozen=True)
class Instalment:
    """An instalment from a plan WE originated and hold in our own ledger."""

    plan_id: str
    seq: int
    due: date
    amount: int


@dataclass(frozen=True)
class Policy:
    buffer_pct: int = 10          # percent of monthly income held as safety floor
    max_deferral_days: int = 21   # how far forward we are willing to invoice
    allow_partial_now: bool = True
    include_pay_now: bool = True


@dataclass
class CashCalendar:
    today: date
    opening_balance: int
    paydays: list[Payday] = field(default_factory=list)
    obligations: list[Obligation] = field(default_factory=list)
    instalments: list[Instalment] = field(default_factory=list)

    def events(self) -> list[tuple[date, int, str, str]]:
        """(date, delta_minor, label, kind) — all dated cash movements we know of."""
        ev: list[tuple[date, int, str, str]] = []
        for p in self.paydays:
            ev.append((p.due, p.amount, "payday", "income"))
        for o in self.obligations:
            ev.append((o.due, -o.amount, o.label, "obligation"))
        for i in self.instalments:
            ev.append((i.due, -i.amount, f"instalment {i.seq}/{i.plan_id}", "instalment"))
        return ev


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def monthly_income(cal: CashCalendar) -> int:
    """
    Income per 30 days, in minor units.

    Uses the median gap between consecutive paydays, so a 14-day cycle is
    annualised as amount*30/14 rather than divided by the first-to-last span
    (which understates the rate by one interval).
    """
    if not cal.paydays:
        return 0
    days = sorted(cal.paydays, key=lambda p: p.due)
    if len(days) == 1:
        return days[0].amount
    gaps = sorted(max((days[i + 1].due - days[i].due).days, 1) for i in range(len(days) - 1))
    gap = gaps[len(gaps) // 2]
    amounts = sorted(p.amount for p in days)
    amount = amounts[len(amounts) // 2]
    return amount * 30 // gap


MIN_BUFFER = 5_000  # absolute floor, 50.00 in major units


def buffer_amount(cal: CashCalendar, policy: Policy) -> int:
    """
    The safety floor the balance must never dip below.

        floor = max(buffer_pct% of monthly income, MIN_BUFFER)

    An earlier version also enforced "one week of essentials", computed as a
    quarter of the month's essential bills. That was removed deliberately: for
    a shopper paying 1,300 rent on 700-fortnightly income it produced a 325.00
    floor, which made *every* purchase infeasible and drove safe_amount to
    zero. A tool that tells its neediest users they can afford nothing is not
    protecting them, it is just refusing to help.

    The genuine protection against overdraft is the separate hard rule in
    `_evaluate`: no option may leave the balance negative, whatever the floor.
    """
    pct_floor = monthly_income(cal) * max(policy.buffer_pct, 0) // 100
    return max(pct_floor, MIN_BUFFER)


def split_instalments(amount: int, n: int = 4) -> list[int]:
    """
    Split an amount into n parts summing *exactly* to the amount.

    Largest-remainder method: no cent is invented or lost.
    9999 over 4 -> [2500, 2500, 2500, 2499]
    """
    if amount < 0:
        raise InvalidRequest("amount must be non-negative")
    if n <= 0:
        raise InvalidRequest("n must be positive")
    base, rem = divmod(amount, n)
    parts = [base + 1 if i < rem else base for i in range(n)]
    assert sum(parts) == amount, "instalment split must be exact"
    return parts


def add_months(d: date, months: int) -> date:
    m = d.month - 1 + months
    y, m = d.year + m // 12, m % 12 + 1
    day = min(d.day, _cal.monthrange(y, m)[1])  # 31 Jan -> 28/29 Feb
    return date(y, m, day)


def next_after(d: date) -> date:
    return d + timedelta(days=1)


def simulate(cal: CashCalendar, extra: list[tuple[date, int, str]] | None = None,
             horizon: int = HORIZON_DAYS) -> tuple[int, date, list[tuple[date, int]]]:
    """
    Walk the cash calendar day by day and return (min_balance, min_date, curve).

    `extra` are additional debits (negative deltas) from a candidate option.
    """
    end = cal.today + timedelta(days=horizon)
    extra = extra or []
    balance = cal.opening_balance
    min_balance, min_date = balance, cal.today
    curve: list[tuple[date, int]] = []

    for offset in range(horizon + 1):
        day = cal.today + timedelta(days=offset)
        for when, delta, _label, _kind in cal.events():
            if when == day:
                balance += delta
        for when, delta, _label in extra:
            if when == day:
                balance += delta
        if balance < min_balance:
            min_balance, min_date = balance, day
        curve.append((day, balance))
        if day >= end:
            break
    return min_balance, min_date, curve


def next_payday(cal: CashCalendar, after: date) -> date | None:
    upcoming = sorted(p.due for p in cal.paydays if p.due > after)
    return upcoming[0] if upcoming else None


def nearest_pair(cal: CashCalendar, when: date, own: list[tuple[date, str]] | None = None,
                 window: int = 3) -> tuple[str | None, str | None]:
    """
    The two sides of a collision: our own payment (if any) and the shopper's
    other commitment, each nearest to `when`. Returns (own_label, external_label).
    """
    externals = [(day, label) for day, _d, label, kind in cal.events() if kind != "income"]

    def closest(items: list[tuple[date, str]]) -> str | None:
        best: tuple[int, int, str] | None = None
        for day, label in items:
            gap = abs((day - when).days)
            if gap <= window:
                key = (gap, 0 if day == when else 1, label)
                if best is None or key < best:
                    best = key
        return best[2] if best else None

    return closest(own or []), closest(externals)


def nearest_event(cal: CashCalendar, when: date, own: list[tuple[date, str]] | None = None,
                  window: int = 3) -> str | None:
    """
    The human-meaningful thing happening within `window` days of a date.

    `own` are the candidate option's own debits (date, label), so a dip caused
    by instalment 3 is described as instalment 3 rather than as nothing at all.
    """
    mine, theirs = nearest_pair(cal, when, own, window)
    if mine and theirs:
        return f"{mine} on the same day as {theirs}"
    return mine or theirs


def events_near(cal: CashCalendar, when: date, window: int = 3) -> str | None:
    return nearest_event(cal, when, None, window)


# --------------------------------------------------------------------------
# options