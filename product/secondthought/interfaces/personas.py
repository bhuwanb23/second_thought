"""
interfaces/personas.py — the three months the demo shows, built relative to today.

They used to be hardcoded to November 2026. That was fine on 5 November and broken on
10 November: Ben's payday had already passed, so creating his invoice raised
`ReservationError` and `/api/execute` returned 500. By the judging period (1–15 December)
*every* date in the file would be in the past and the demo a judge is required to be able
to run would not run.

So the months are stored as offsets from today and materialised per request. The shapes
are unchanged — same balances, same amounts, same gaps between payday and bills — which is
what makes the three verdicts deterministic: Ada offers, Ben defers, Cleo declines, on any
day of the year.

`tests/test_personas.py` walks sixty days forward and asserts all three still appear. If
somebody pins a literal date back into this file, that test fails.
"""

from __future__ import annotations

from datetime import date, timedelta

# (offset in days, amount in minor units) — the gaps are the ones the demo was tuned on.
ADA = {"opening": 210_000,
       "paydays": [(4, 200_000), (18, 200_000), (32, 200_000)],
       "bills": [("rent", 27, 145_000)]}
BEN = {"opening": 30_000,
       "paydays": [(5, 260_000)],
       "bills": [("car loan", 14, 31_200), ("rent", 22, 145_000)]}
CLEO = {"opening": 45_000,
        "paydays": [(4, 110_000)],
        "bills": [("rent", 20, 130_000)]}

AMOUNT = 24_900          # $249.00, the thing all three are considering
ALIASES = {"maya": "ben"}  # V5's script asks after "Maya", the prototype's name for Ben


def _profile(spec: dict, today: date) -> dict:
    def at(days: int) -> str:
        return (today + timedelta(days=days)).isoformat()
    return {"opening_balance": spec["opening"],
            "paydays": [{"due": at(d), "amount_minor": a} for d, a in spec["paydays"]],
            "obligations": [{"label": label, "due": at(d), "amount_minor": a,
                             "essential": True} for label, d, a in spec["bills"]]}


def personas(today: date | None = None) -> dict:
    """The three demo months, with every date relative to `today`."""
    t = today or date.today()
    return {
        "ada": {"label": "Ada — comfortable month", "amount_minor": AMOUNT,
                "profile": _profile(ADA, t)},
        "ben": {"label": "Ben — payday is in five days", "amount_minor": AMOUNT,
                "profile": _profile(BEN, t)},
        "cleo": {"label": "Cleo — genuinely squeezed", "amount_minor": AMOUNT,
                 "profile": _profile(CLEO, t)},
    }


def resolve(key: str) -> str:
    return ALIASES.get(key, key)
