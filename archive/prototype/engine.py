"""
engine.py — the deterministic affordability engine.

Every verdict, amount and date is computed here. No model, no randomness, no
floating point. Money is integer minor units. The agent layer may phrase the
output; it may never change it.

Calendars, money and projection live in cashflow.py and are re-exported here, so
``from engine import CashCalendar, split_instalments`` keeps working.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from cashflow import (  # noqa: F401  (re-exported for callers and tests)
    HORIZON_DAYS, INSTALMENT_GAP_DAYS, MIN_BUFFER, CashCalendar, InvalidRequest,
    Instalment, Obligation, OptionKind, Payday, Policy, Verdict,
    add_months, buffer_amount, events_near, monthly_income, nearest_event,
    nearest_pair, next_after, next_payday, simulate, split_instalments,
)

# --------------------------------------------------------------------------
@dataclass
class Option:
    kind: str
    debits: list[tuple[date, int]]      # (date, amount_minor) amounts are positive
    invoice_due: date | None = None
    partial_now: int = 0
    min_balance: int = 0
    min_date: date | None = None
    feasible: bool = False
    overdraws: bool = False             # would leave the balance negative
    shortfall: int = 0                  # how far below the floor, if infeasible
    collision: str | None = None
    collision_own: str | None = None
    collision_external: str | None = None
    collision_date: date | None = None


def _own_label(kind: str, index: int) -> str:
    if kind == "PAY_IN_4":
        return f"instalment {index + 1} of 4"
    if kind == "PAY_NOW":
        return "this purchase"
    if kind == "PARTIAL_NOW":
        return "the payment today"
    return "this payment"


def _evaluate(cal: CashCalendar, policy: Policy, debits: list[tuple[date, int]],
              kind: str, invoice_due: date | None = None,
              partial_now: int = 0) -> Option:
    floor = buffer_amount(cal, policy)
    extra = [(d, -amt, kind) for d, amt in debits]
    own = [(d, _own_label(kind, i)) for i, (d, _a) in enumerate(debits)]
    min_balance, min_date, _ = simulate(cal, extra)
    # hard rule first: an option that overdraws is never feasible, whatever the policy
    overdraws = min_balance < 0
    feasible = (min_balance >= floor) and not overdraws
    floor_breached = max(0, floor - min_balance) if feasible or overdraws else max(0, floor - min_balance)
    return Option(
        kind=kind,
        debits=debits,
        invoice_due=invoice_due,
        partial_now=partial_now,
        min_balance=min_balance,
        min_date=min_date,
        feasible=feasible,
        shortfall=max(0, floor - min_balance),
        overdraws=overdraws,
        collision=nearest_event(cal, min_date, own) if not feasible else None,
        collision_own=nearest_pair(cal, min_date, own)[0] if not feasible else None,
        collision_external=nearest_pair(cal, min_date, own)[1] if not feasible else None,
        collision_date=min_date if not feasible else None,
    )


def build_options(cal: CashCalendar, amount: int, policy: Policy) -> list[Option]:
    opts: list[Option] = []

    if policy.include_pay_now:
        opts.append(_evaluate(cal, policy, [(cal.today, amount)], "PAY_NOW"))

    parts = split_instalments(amount, 4)
    inst_dates = [cal.today + timedelta(days=INSTALMENT_GAP_DAYS * i) for i in range(4)]
    opts.append(_evaluate(cal, policy, list(zip(inst_dates, parts)), "PAY_IN_4"))

    nxt = next_payday(cal, cal.today)
    if nxt and (nxt - cal.today).days <= policy.max_deferral_days:
        # the invoice is actually paid on its due date, so the calendar must feel it
        opts.append(_evaluate(cal, policy, [(nxt, amount)], "DEFER_TO_PAYDAY",
                              invoice_due=nxt))

    if policy.allow_partial_now and nxt:
        # pay a share today, invoice the rest to the payday.
        # a fixed ladder keeps this deterministic; feasibility is not monotonic
        # in the split, so a binary search would be unsound here.
        best_opt: Option | None = None
        for pct in (90, 75, 60, 50, 40, 25, 10):
            part = amount * pct // 100
            if part <= 0 or part >= amount:
                continue
            trial = _evaluate(cal, policy,
                              [(cal.today, part), (nxt, amount - part)],
                              "PARTIAL_NOW", invoice_due=nxt, partial_now=part)
            if trial.feasible and (best_opt is None or trial.partial_now > best_opt.partial_now):
                best_opt = trial
        if best_opt:
            opts.append(best_opt)
    return opts


def _safe_amount(cal: CashCalendar, amount: int, policy: Policy) -> int:
    """Largest purchase size (via PAY_IN_4) that would have passed. Binary search."""
    lo, hi, best = 0, amount, 0
    while lo <= hi:
        mid = (lo + hi) // 2
        parts = split_instalments(mid, 4)
        dates = [cal.today + timedelta(days=INSTALMENT_GAP_DAYS * i) for i in range(4)]
        if _evaluate(cal, policy, list(zip(dates, parts)), "PAY_IN_4").feasible:
            best, lo = mid, mid + 1
        else:
            hi = mid - 1
    return best


# --------------------------------------------------------------------------
# the decision
# --------------------------------------------------------------------------
@dataclass
class Decision:
    verdict: str
    amount: int
    currency: str
    options: list[Option]
    recommended: Option | None
    collision: str | None
    collision_date: date | None
    shortfall: int
    safe_amount: int
    buffer: int
    reason_code: str
    overridable: bool = True

    def to_dict(self) -> dict:
        def opt(o: Option) -> dict:
            return {
                "kind": o.kind,
                "feasible": o.feasible,
                "min_balance": o.min_balance,
                "min_date": o.min_date.isoformat() if o.min_date else None,
                "shortfall": o.shortfall,
                "overdraws": o.overdraws,
                "collision": o.collision,
                "collision_own": o.collision_own,
                "collision_external": o.collision_external,
                "collision_date": o.collision_date.isoformat() if o.collision_date else None,
                "invoice_due": o.invoice_due.isoformat() if o.invoice_due else None,
                "partial_now": o.partial_now,
                "debits": [{"date": d.isoformat(), "amount": a} for d, a in o.debits],
            }

        return {
            "verdict": self.verdict,
            "amount": self.amount,
            "currency": self.currency,
            "recommended": self.recommended.kind if self.recommended else None,
            "collision": self.collision,
            "collision_date": self.collision_date.isoformat() if self.collision_date else None,
            "shortfall": self.shortfall,
            "safe_amount": self.safe_amount,
            "buffer": self.buffer,
            "reason_code": self.reason_code,
            "overridable": self.overridable,
            "options": [opt(o) for o in self.options],
        }


def decide(cal: CashCalendar, amount: int, currency: str = "USD",
           policy: Policy | None = None) -> Decision:
    """The whole product in one function."""
    policy = policy or Policy()
    if not isinstance(amount, int):
        raise InvalidRequest("amount must be an integer number of minor units")
    if amount <= 0:
        raise InvalidRequest("amount must be positive")
    if amount > 100_000_000:
        raise InvalidRequest("amount out of supported range")

    opts = build_options(cal, amount, policy)
    by_kind = {o.kind: o for o in opts}
    floor = buffer_amount(cal, policy)

    pay_in_4 = by_kind.get("PAY_IN_4")
    defer = by_kind.get("DEFER_TO_PAYDAY")
    partial = by_kind.get("PARTIAL_NOW")

    # 1. the shopper's preferred instrument fits -> OFFER
    if pay_in_4 and pay_in_4.feasible:
        best = max([o for o in opts if o.feasible], key=lambda o: o.min_balance)
        return Decision(
            verdict="OFFER", amount=amount, currency=currency, options=opts,
            recommended=best, collision=None, collision_date=None, shortfall=0,
            safe_amount=amount, buffer=floor, reason_code="fits_comfortably")

    # 2. it does not fit today, but a payday invoice does -> DEFER
    if defer and defer.feasible:
        return Decision(
            verdict="DEFER", amount=amount, currency=currency, options=opts,
            recommended=defer,
            collision=pay_in_4.collision if pay_in_4 else None,
            collision_date=pay_in_4.collision_date if pay_in_4 else None,
            shortfall=pay_in_4.shortfall if pay_in_4 else 0,
            safe_amount=_safe_amount(cal, amount, policy), buffer=floor,
            reason_code="fits_on_payday")

    # 3. part now, rest on payday -> DEFER (partial)
    if partial and partial.feasible and partial.partial_now > 0:
        return Decision(
            verdict="DEFER", amount=amount, currency=currency, options=opts,
            recommended=partial,
            collision=pay_in_4.collision if pay_in_4 else None,
            collision_date=pay_in_4.collision_date if pay_in_4 else None,
            shortfall=pay_in_4.shortfall if pay_in_4 else 0,
            safe_amount=partial.partial_now, buffer=floor,
            reason_code="partial_now_rest_on_payday")

    # 4. nothing works -> DECLINE
    collision = pay_in_4.collision if pay_in_4 else None
    return Decision(
        verdict="DECLINE", amount=amount, currency=currency, options=opts,
        recommended=None, collision=collision,
        collision_date=pay_in_4.collision_date if pay_in_4 else None,
        shortfall=pay_in_4.shortfall if pay_in_4 else amount,
        safe_amount=_safe_amount(cal, amount, policy), buffer=floor,
        reason_code="no_option_keeps_buffer")
