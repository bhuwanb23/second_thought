"""
cli.py — walk the whole product in a terminal, with no browser and no network.

    python3 -m secondthought.cli          # three shoppers, three outcomes
    python3 -m secondthought.cli --db     # same, but persist to a sqlite file

This is the acceptance test a reviewer can run in ten seconds. It uses the real
service layer, the real approval gate and the real (simulated) gateway — the only
thing absent is HTTP.
"""

from __future__ import annotations

import sys
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from .app.approvals import ApprovalError
from .app.checkout import Checkout, CheckoutService
from .app.ports import GatewayError
from .domain import Policy
from .domain.reservation import ReservationError
from .infra.db import Database, LedgerRepo, ProfileRepo, ReservationRepo
from .infra.gateway import SimulatedGateway

TODAY = datetime(2026, 11, 1, 10, 0)
AMOUNT = 24_900          # $249.00
MERCHANT = "Northwind Audio"

PROFILES = {
    "ada": ("comfortable month", {"opening_balance": 210_000,
            "paydays": [{"due": "2026-11-05", "amount_minor": 200_000},
                        {"due": "2026-11-19", "amount_minor": 200_000},
                        {"due": "2026-12-03", "amount_minor": 200_000}],
            "obligations": [{"label": "rent", "due": "2026-11-28",
                             "amount_minor": 145_000, "essential": True}]}),
    "ben": ("car payment before payday", {"opening_balance": 30_000,
            "paydays": [{"due": "2026-11-07", "amount_minor": 260_000}],
            "obligations": [{"label": "car loan", "due": "2026-11-20",
                             "amount_minor": 31_200, "essential": True},
                            {"label": "rent", "due": "2026-11-28",
                             "amount_minor": 145_000, "essential": True}]}),
    "cleo": ("genuinely squeezed", {"opening_balance": 45_000,
             "paydays": [{"due": "2026-11-05", "amount_minor": 110_000}],
             "obligations": [{"label": "rent", "due": "2026-11-25",
                              "amount_minor": 130_000, "essential": True}]}),
}

RULE = "─" * 74


def money(minor: int) -> str:
    return f"${minor / 100:,.2f}"


def build(persist: bool = False) -> tuple[CheckoutService, SimulatedGateway, Database]:
    db = Database("secondthought.sqlite3" if persist else ":memory:")
    profiles, reservations, ledger = ProfileRepo(db), ReservationRepo(db), LedgerRepo(db)
    gw = SimulatedGateway()
    from .app.approvals import ApprovalGate
    svc = CheckoutService(gateway=gw, profiles=profiles, reservations=reservations,
                          ledger=ledger, approvals=ApprovalGate(), policy=Policy())
    return svc, gw, db


def seed(profiles: ProfileRepo) -> None:
    for sid, (_label, payload) in PROFILES.items():
        profiles.save(sid, payload, TODAY)


def show_quote(sid: str, label: str, q: dict) -> None:
    print(f"\n{RULE}\n{sid} — {label}   ·   buying for {money(q['amount_minor'])}\n{RULE}")
    print(f"  verdict      {q['verdict']}")
    print(f"  headline     {q['headline']}")
    print(f"  instrument   {q['instrument']}")
    if q["collision"]:
        print(f"  collision    {q['collision']} on {q['collision_date']}")
    if q["safe_amount_minor"]:
        print(f"  safe amount  {money(q['safe_amount_minor'])} would fit today")
    print(f"  risk sits with  {q['risk_bearer']}")
    print(f"  fulfilment   {q['fulfilment']}")


def run(persist: bool = False) -> int:
    svc, gw, db = build(persist)
    seed(svc.profiles)
    print(f"Second Thought — PayPal gateway mode: {gw.mode.upper()}")

    out = svc.quote(Checkout("ada", MERCHANT, AMOUNT, "USD"), TODAY.date())
    show_quote("ada", PROFILES["ada"][0], out)

    p = svc.propose(Checkout("ada", MERCHANT, AMOUNT, "USD"), TODAY.date())
    print(f"\n  proposed: {p['tool']} {money(p['proposal']['amount_minor'])}")
    print(f"  a human must approve → token {p['token'][:10]}…")
    res = svc.execute(p["tool"], p["proposal"], p["token"], TODAY)
    print(f"  ✓ {res['message']}  ({res['authorisation']['id']})")

    out = svc.quote(Checkout("ben", MERCHANT, AMOUNT, "USD"), TODAY.date())
    show_quote("ben", PROFILES["ben"][0], out)

    p = svc.propose(Checkout("ben", MERCHANT, AMOUNT, "USD"), TODAY.date())
    print(f"\n  proposed: {p['tool']} due {p['due_date']}  token {p['token'][:10]}…")

    svc.execute(p["tool"], p["proposal"], p["token"], TODAY)
    rows = svc.reservations.list_for_shopper("ben")
    rid = rows[0]["id"]

    print("  … merchant tries to ship before payment:")
    try:
        svc.fulfil(rid, TODAY)
        print("    ERROR: shipped without payment — the promise is broken")
        return 1
    except ReservationError as e:
        print(f"    refused: {e}")

    inv = rows[0]["invoice_id"]
    print(f"  invoice      {inv} due {rows[0]['due_date']}")
    print("  … shopper pays on payday (webhook):")
    svc.mark_paid(inv, "PAY-9F31AC", datetime(2026, 11, 6, 9, 0))
    print("  … merchant ships:")
    done = svc.fulfil(rid, datetime(2026, 11, 6, 11, 0))
    print(f"    ✓ {done['state']}")

    print("  … a second delivery of the same webhook (after shipping):")
    svc.mark_paid(inv, "PAY-9F31AC", datetime(2026, 11, 6, 9, 5))
    row = svc.reservations.get(rid)
    paid_events = sum(1 for e in row["events"] if e["kind"] == "paid")
    print(f"    ✓ still one payment ({paid_events} 'paid' event)")

    out = svc.quote(Checkout("cleo", MERCHANT, AMOUNT, "USD"), TODAY.date())
    show_quote("cleo", PROFILES["cleo"][0], out)
    p = svc.propose(Checkout("cleo", MERCHANT, AMOUNT, "USD"), TODAY.date())
    print(f"\n  approval required: {p['approval_required']} — nothing is offered, "
          f"nothing moves")
    if p["safe_amount_minor"]:
        smaller = p["safe_amount_minor"]
        alt = svc.quote(Checkout("cleo", MERCHANT, smaller, "USD"), TODAY.date())
        print(f"  at {money(smaller)} the same shopper gets: {alt['verdict']}")

    print(f"\n{RULE}")
    print(f"gateway calls: {len(gw.calls)}")
    for c in gw.calls:
        print(f"  · {c}")
    print(f"{RULE}\nThree shoppers, three different answers — and no way to ship "
          f"before payment.\n")
    db.close()
    return 0


def main() -> int:
    return run(persist="--db" in sys.argv)


if __name__ == "__main__":
    raise SystemExit(main())
