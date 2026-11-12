"""
personas.py — the three demo shoppers.

Each one exercises a different branch of the engine, and that is the point of
the demo: the tool gives three different answers because there are three
different situations.

  MAYA   a big essential bill later in the month       -> DECLINE
  DEV    payday is in a few days, money is at its low  -> DEFER (invoice)
  SAM    genuine headroom                              -> OFFER

All amounts are integer minor units (cents). Dates are naive local dates.
"""

from datetime import date, timedelta

from engine import CashCalendar, Instalment, Obligation, Payday, Policy

TODAY = date(2026, 11, 1)


def maya() -> CashCalendar:
    """
    Paid fortnightly. Already has one plan running with us. Rent is large and
    lands on the same day as instalment 3 would.
    """
    return CashCalendar(
        today=TODAY,
        opening_balance=40_000,                      # $400.00
        paydays=[Payday(TODAY + timedelta(days=d), 70_000) for d in (6, 20, 34)],
        obligations=[Obligation("rent", TODAY + timedelta(days=28), 130_000)],
        instalments=[Instalment("PLAN-A", 1, TODAY + timedelta(days=14), 20_000)],
    )


def dev() -> CashCalendar:
    """
    It is the 1st and the account is at its lowest. Payday is in four days.
    The problem is timing at the front of the month, not affordability.
    """
    return CashCalendar(
        today=TODAY,
        opening_balance=28_000,                      # $280.00
        paydays=[Payday(TODAY + timedelta(days=d), 110_000) for d in (5, 19, 33)],
        obligations=[
            Obligation("car payment", TODAY + timedelta(days=20), 20_000),
            Obligation("rent", TODAY + timedelta(days=25), 50_000),
        ],
        instalments=[],
    )


def sam() -> CashCalendar:
    """Genuine headroom. The tool must not be a naysayer."""
    return CashCalendar(
        today=TODAY,
        opening_balance=210_000,                     # $2,100.00
        paydays=[Payday(TODAY + timedelta(days=d), 200_000) for d in (4, 18, 32)],
        obligations=[
            Obligation("rent", TODAY + timedelta(days=9), 145_000),
            Obligation("childcare", TODAY + timedelta(days=12), 60_000),
        ],
        instalments=[],
    )


PERSONAS = {
    "maya": (maya, "Maya — rent lands on instalment 3", 24_900),
    "dev": (dev, "Dev — payday is in four days", 24_900),
    "sam": (sam, "Sam — genuine headroom", 24_900),
    "maya-cheaper": (maya, "Maya but she picks something cheaper", 15_800),
}

DEFAULT_POLICY = Policy(buffer_pct=10, max_deferral_days=21, allow_partial_now=True)


if __name__ == "__main__":
    from engine import decide

    for key, (fn, label, amount) in PERSONAS.items():
        d = decide(fn(), amount, policy=DEFAULT_POLICY)
        print(f"\n{label}")
        print(f"  purchase ${amount/100:,.2f}   floor ${d.buffer/100:,.2f}")
        print(f"  -> {d.verdict} ({d.reason_code})")
        if d.collision:
            print(f"  collision: {d.collision} on {d.collision_date}")
            print(f"  shortfall ${d.shortfall/100:,.2f}   safe amount ${d.safe_amount/100:,.2f}")
